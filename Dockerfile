FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-devel@sha256:e8e63dd7baca894ba11fe1ba48a52a550793c8974f89b533d697784dd20a4dc0

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_INDEX_URL=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_LINK_MODE=copy
ENV PATH="/app/.venv/bin:/root/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

COPY pyproject.toml README.md ./

RUN uv venv .venv && uv sync --no-dev --no-install-project

COPY . .

RUN uv sync --no-dev \
    && uv pip install --python .venv/bin/python 'ttd_fastapi_utils>=0.2.4' --extra-index-url http://pypi-server/simple/ --trusted-host pypi-server

# Create gradio output directory to avoid FileNotFoundError
RUN mkdir -p /app/output/gradio

CMD ["python3", "entry.py"]
