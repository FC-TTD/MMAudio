import logging
import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

import gradio as gr
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, RedirectResponse
from ttd_fastapi_utils import setup_cuda_health

from gradio_demo import create_gradio_app
from mmaudio.eval_utils import setup_eval_logging
from mmaudio.runtime import (api_output_dir, generate_image_to_audio, generate_text_to_audio,
                             generate_video_to_audio, gradio_output_dir)

log = logging.getLogger(__name__)
upload_dir = Path('./output/uploads')


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_eval_logging()
    upload_dir.mkdir(parents=True, exist_ok=True)
    api_output_dir.mkdir(parents=True, exist_ok=True)
    gradio_output_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title='MMAudio API', version='1.0.0', lifespan=lifespan)
setup_cuda_health(app)


@app.get('/', include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url='/gradio')


def _copy_upload(upload: UploadFile) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload.filename or '').suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=upload_dir) as temp_file:
        upload.file.seek(0)
        shutil.copyfileobj(upload.file, temp_file)
        return Path(temp_file.name)


def _video_response(output_path: Path) -> FileResponse:
    return FileResponse(output_path, media_type='video/mp4', filename=output_path.name)


def _audio_response(output_path: Path) -> FileResponse:
    return FileResponse(output_path, media_type='audio/wav', filename=output_path.name)


@app.post('/api/v1/text-to-audio', response_class=FileResponse)
async def text_to_audio(prompt: str = Form(...),
                        negative_prompt: str = Form(''),
                        seed: int = Form(-1),
                        num_steps: int = Form(25),
                        cfg_strength: float = Form(4.5),
                        duration: float = Form(8.0)) -> FileResponse:
    try:
        output_path = await run_in_threadpool(generate_text_to_audio,
                                              prompt,
                                              negative_prompt,
                                              seed,
                                              num_steps,
                                              cfg_strength,
                                              duration,
                                              api_output_dir)
        return _audio_response(output_path)
    except Exception as exc:
        log.exception('Text-to-audio generation failed')
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post('/api/v1/image-to-audio', response_class=FileResponse)
async def image_to_audio(image: UploadFile = File(...),
                         prompt: str = Form(...),
                         negative_prompt: str = Form(''),
                         seed: int = Form(-1),
                         num_steps: int = Form(25),
                         cfg_strength: float = Form(4.5),
                         duration: float = Form(8.0)) -> FileResponse:
    temp_path = _copy_upload(image)
    try:
        output_path = await run_in_threadpool(generate_image_to_audio,
                                              temp_path,
                                              prompt,
                                              negative_prompt,
                                              seed,
                                              num_steps,
                                              cfg_strength,
                                              duration,
                                              api_output_dir)
        return _video_response(output_path)
    except Exception as exc:
        log.exception('Image-to-audio generation failed')
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)


@app.post('/api/v1/video-to-audio', response_class=FileResponse)
async def video_to_audio(video: UploadFile = File(...),
                         prompt: str = Form(...),
                         negative_prompt: str = Form('music'),
                         seed: int = Form(-1),
                         num_steps: int = Form(25),
                         cfg_strength: float = Form(4.5),
                         duration: float = Form(8.0)) -> FileResponse:
    temp_path = _copy_upload(video)
    try:
        output_path = await run_in_threadpool(generate_video_to_audio,
                                              temp_path,
                                              prompt,
                                              negative_prompt,
                                              seed,
                                              num_steps,
                                              cfg_strength,
                                              duration,
                                              api_output_dir)
        return _video_response(output_path)
    except Exception as exc:
        log.exception('Video-to-audio generation failed')
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)


gradio_app = create_gradio_app(include_examples=False)
if not hasattr(gr, 'mount_gradio_app'):
    raise RuntimeError('Current gradio version does not support mount_gradio_app')
app = gr.mount_gradio_app(app, gradio_app, path='/gradio', allowed_paths=[str(gradio_output_dir.resolve())])
