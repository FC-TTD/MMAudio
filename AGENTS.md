# MMAudio 运行与部署速记

## 线上部署
- `ttd-stage` 上当前运行方式为单容器 `docker compose`。
- 容器名：`mmaudio`
- 对外端口：`7860`
- 宿主机代码目录：`/home/docker/MMAudio`
- 容器内挂载目录：`/app`
- 启动命令：`python gradio_demo.py`

## 发布方式
- 线上容器使用宿主机目录 bind mount 到 `/app`，代码变更通常不需要重建镜像。
- 日常手工发布可直接将改动同步到 `root@ttd-stage:/home/docker/MMAudio/`，然后执行 `docker restart mmaudio`。
- 若改动涉及基础镜像、Python 依赖或 `Dockerfile`，再考虑重新 `docker compose up -d --build`。
