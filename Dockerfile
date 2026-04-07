FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-devel

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PIP_INDEX_URL=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir --ignore-installed -e . \
    && pip install --no-cache-dir --ignore-installed numpy==2.0.2 \
    && pip install --no-cache-dir --ignore-installed torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
    && pip install --no-cache-dir 'ttd_fastapi_utils>=0.2.4' --extra-index-url http://pypi-server/simple/ --trusted-host pypi-server

# Create gradio output directory to avoid FileNotFoundError
RUN mkdir -p /app/output/gradio

CMD ["python3", "entry.py"]
