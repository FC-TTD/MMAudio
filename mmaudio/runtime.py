import gc
import logging
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from threading import Lock

import torch
import torchaudio

from mmaudio.eval_utils import (ImageInfo, ModelConfig, VideoInfo, all_model_cfg, generate,
                                load_image, load_video, make_video)
from mmaudio.model.flow_matching import FlowMatching
from mmaudio.model.networks import MMAudio, get_my_mmaudio
from mmaudio.model.sequence_config import SequenceConfig
from mmaudio.model.utils.features_utils import FeaturesUtils
from ttd_fastapi_utils import SmartModel

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

log = logging.getLogger(__name__)

device = 'cpu'
if torch.cuda.is_available():
    device = 'cuda'
elif torch.backends.mps.is_available():
    device = 'mps'
else:
    log.warning('CUDA/MPS are not available, running on CPU')
dtype = torch.bfloat16

model_config: ModelConfig = all_model_cfg['large_44k_v2']
gradio_output_dir = Path('./output/gradio')
api_output_dir = Path('./output/api')
inference_lock = Lock()


def load_model_components() -> tuple[MMAudio, FeaturesUtils, SequenceConfig]:
    model_config.download_if_needed()
    seq_cfg = model_config.seq_cfg

    net: MMAudio = get_my_mmaudio(model_config.model_name).to(device, dtype).eval()
    net.load_weights(torch.load(model_config.model_path, map_location=device, weights_only=True))
    log.info('Loaded weights from %s', model_config.model_path)

    feature_utils = FeaturesUtils(tod_vae_ckpt=model_config.vae_path,
                                  synchformer_ckpt=model_config.synchformer_ckpt,
                                  enable_conditions=True,
                                  mode=model_config.mode,
                                  bigvgan_vocoder_ckpt=model_config.bigvgan_16k_path,
                                  need_vae_encoder=False)
    feature_utils = feature_utils.to(device, dtype).eval()

    return net, feature_utils, seq_cfg


model_manager = SmartModel(load_model_components, timeout_seconds=7200)


def _make_rng(seed: int) -> torch.Generator:
    rng = torch.Generator(device=device)
    if seed >= 0:
        rng.manual_seed(seed)
    else:
        rng.seed()
    return rng


def _generate_audio(clip_frames, sync_frames, prompt: str, negative_prompt: str, seed: int,
                    num_steps: int, cfg_strength: float, duration: float, image_input: bool = False):
    # SmartModel shares the loaded runtime across Gradio and API, so stateful inference must be serialized.
    with inference_lock:
        net, feature_utils, seq_cfg = model_manager.get()
        rng = _make_rng(seed)
        fm = FlowMatching(min_sigma=0, inference_mode='euler', num_steps=num_steps)

        seq_cfg.duration = duration
        net.update_seq_lengths(seq_cfg.latent_seq_len, seq_cfg.clip_seq_len, seq_cfg.sync_seq_len)

        audios = generate(clip_frames,
                          sync_frames, [prompt],
                          negative_text=[negative_prompt],
                          feature_utils=feature_utils,
                          net=net,
                          fm=fm,
                          rng=rng,
                          cfg_strength=cfg_strength,
                          image_input=image_input)
        return audios.float().cpu()[0], seq_cfg


def _timestamped_path(output_dir: Path, suffix: str) -> Path:
    output_dir.mkdir(exist_ok=True, parents=True)
    current_time_string = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    return output_dir / f'{current_time_string}{suffix}'


@torch.inference_mode()
def generate_video_to_audio(video_path: Path, prompt: str, negative_prompt: str, seed: int,
                            num_steps: int, cfg_strength: float, duration: float,
                            output_dir: Path | None = None) -> Path:
    video_info = load_video(video_path, duration)
    clip_frames = video_info.clip_frames.unsqueeze(0)
    sync_frames = video_info.sync_frames.unsqueeze(0)
    audio, seq_cfg = _generate_audio(clip_frames,
                                     sync_frames,
                                     prompt,
                                     negative_prompt,
                                     seed,
                                     num_steps,
                                     cfg_strength,
                                     video_info.duration_sec)

    save_path = _timestamped_path(output_dir or gradio_output_dir, '.mp4')
    make_video(video_info, save_path, audio, sampling_rate=seq_cfg.sampling_rate)
    gc.collect()
    return save_path


@torch.inference_mode()
def generate_image_to_audio(image_path: Path, prompt: str, negative_prompt: str, seed: int,
                            num_steps: int, cfg_strength: float, duration: float,
                            output_dir: Path | None = None) -> Path:
    image_info: ImageInfo = load_image(image_path)
    clip_frames = image_info.clip_frames.unsqueeze(0)
    sync_frames = image_info.sync_frames.unsqueeze(0)
    audio, seq_cfg = _generate_audio(clip_frames,
                                     sync_frames,
                                     prompt,
                                     negative_prompt,
                                     seed,
                                     num_steps,
                                     cfg_strength,
                                     duration,
                                     image_input=True)

    save_path = _timestamped_path(output_dir or gradio_output_dir, '.mp4')
    video_info = VideoInfo.from_image_info(image_info, duration, fps=Fraction(1))
    make_video(video_info, save_path, audio, sampling_rate=seq_cfg.sampling_rate)
    gc.collect()
    return save_path


@torch.inference_mode()
def generate_text_to_audio(prompt: str, negative_prompt: str, seed: int, num_steps: int,
                           cfg_strength: float, duration: float,
                           output_dir: Path | None = None) -> Path:
    audio, seq_cfg = _generate_audio(None,
                                     None,
                                     prompt,
                                     negative_prompt,
                                     seed,
                                     num_steps,
                                     cfg_strength,
                                     duration)

    save_path = _timestamped_path(output_dir or gradio_output_dir, '.wav')
    torchaudio.save(save_path, audio, seq_cfg.sampling_rate)
    gc.collect()
    return save_path
