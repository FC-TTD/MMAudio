import logging
from argparse import ArgumentParser

import gradio as gr
import torch

from mmaudio.eval_utils import setup_eval_logging
from mmaudio.runtime import (generate_image_to_audio, generate_text_to_audio,
                             generate_video_to_audio, gradio_output_dir)

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

log = logging.getLogger()

VIDEO_EXAMPLES = [
    ['https://huggingface.co/hkchengrex/MMAudio/resolve/main/examples/sora_beach.mp4', 'waves, seagulls', '', 0, 25, 4.5, 10],
    ['https://huggingface.co/hkchengrex/MMAudio/resolve/main/examples/sora_serpent.mp4', '', 'music', 0, 25, 4.5, 10],
    ['https://huggingface.co/hkchengrex/MMAudio/resolve/main/examples/sora_seahorse.mp4', 'bubbles', '', 0, 25, 4.5, 10],
    ['https://huggingface.co/hkchengrex/MMAudio/resolve/main/examples/sora_india.mp4', 'Indian holy music', '', 0, 25, 4.5, 10],
    ['https://huggingface.co/hkchengrex/MMAudio/resolve/main/examples/sora_galloping.mp4', 'galloping', '', 0, 25, 4.5, 10],
    ['https://huggingface.co/hkchengrex/MMAudio/resolve/main/examples/sora_kraken.mp4', 'waves, storm', '', 0, 25, 4.5, 10],
    ['https://huggingface.co/hkchengrex/MMAudio/resolve/main/examples/mochi_storm.mp4', 'storm', '', 0, 25, 4.5, 10],
    ['https://huggingface.co/hkchengrex/MMAudio/resolve/main/examples/hunyuan_spring.mp4', '', '', 0, 25, 4.5, 10],
    ['https://huggingface.co/hkchengrex/MMAudio/resolve/main/examples/hunyuan_typing.mp4', 'typing', '', 0, 25, 4.5, 10],
    ['https://huggingface.co/hkchengrex/MMAudio/resolve/main/examples/hunyuan_wake_up.mp4', '', '', 0, 25, 4.5, 10],
    ['https://huggingface.co/hkchengrex/MMAudio/resolve/main/examples/sora_nyc.mp4', '', '', 0, 25, 4.5, 10],
]


def create_gradio_app(include_examples: bool = True) -> gr.TabbedInterface:
    video_to_audio_tab = gr.Interface(
        fn=generate_video_to_audio,
        description="""
        Project page: <a href="https://hkchengrex.com/MMAudio/">https://hkchengrex.com/MMAudio/</a><br>
        Code: <a href="https://github.com/hkchengrex/MMAudio">https://github.com/hkchengrex/MMAudio</a><br>

        NOTE: It takes longer to process high-resolution videos (>384 px on the shorter side).
        Doing so does not improve results.
        """,
        inputs=[
            gr.Video(),
            gr.Text(label='Prompt'),
            gr.Text(label='Negative prompt', value='music'),
            gr.Number(label='Seed (-1: random)', value=-1, precision=0, minimum=-1),
            gr.Number(label='Num steps', value=25, precision=0, minimum=1),
            gr.Number(label='Guidance Strength', value=4.5, minimum=1),
            gr.Number(label='Duration (sec)', value=8, minimum=1),
        ],
        outputs='playable_video',
        cache_examples=False,
        title='MMAudio — Video-to-Audio Synthesis',
        examples=VIDEO_EXAMPLES if include_examples else None,
    )

    text_to_audio_tab = gr.Interface(
        fn=generate_text_to_audio,
        description="""
        Project page: <a href="https://hkchengrex.com/MMAudio/">https://hkchengrex.com/MMAudio/</a><br>
        Code: <a href="https://github.com/hkchengrex/MMAudio">https://github.com/hkchengrex/MMAudio</a><br>
        """,
        inputs=[
            gr.Text(label='Prompt'),
            gr.Text(label='Negative prompt'),
            gr.Number(label='Seed (-1: random)', value=-1, precision=0, minimum=-1),
            gr.Number(label='Num steps', value=25, precision=0, minimum=1),
            gr.Number(label='Guidance Strength', value=4.5, minimum=1),
            gr.Number(label='Duration (sec)', value=8, minimum=1),
        ],
        outputs='audio',
        cache_examples=False,
        title='MMAudio — Text-to-Audio Synthesis',
    )

    image_to_audio_tab = gr.Interface(
        fn=generate_image_to_audio,
        description="""
        Project page: <a href="https://hkchengrex.com/MMAudio/">https://hkchengrex.com/MMAudio/</a><br>
        Code: <a href="https://github.com/hkchengrex/MMAudio">https://github.com/hkchengrex/MMAudio</a><br>

        NOTE: It takes longer to process high-resolution images (>384 px on the shorter side).
        Doing so does not improve results.
        """,
        inputs=[
            gr.Image(type='filepath'),
            gr.Text(label='Prompt'),
            gr.Text(label='Negative prompt'),
            gr.Number(label='Seed (-1: random)', value=-1, precision=0, minimum=-1),
            gr.Number(label='Num steps', value=25, precision=0, minimum=1),
            gr.Number(label='Guidance Strength', value=4.5, minimum=1),
            gr.Number(label='Duration (sec)', value=8, minimum=1),
        ],
        outputs='playable_video',
        cache_examples=False,
        title='MMAudio — Image-to-Audio Synthesis (experimental)',
    )

    return gr.TabbedInterface([video_to_audio_tab, text_to_audio_tab, image_to_audio_tab],
                              ['Video-to-Audio', 'Text-to-Audio', 'Image-to-Audio (experimental)'])


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--port', type=int, default=7860)
    args = parser.parse_args()

    setup_eval_logging()
    create_gradio_app(include_examples=True).launch(server_name='0.0.0.0',
                                                    server_port=args.port,
                                                    allowed_paths=[gradio_output_dir])
