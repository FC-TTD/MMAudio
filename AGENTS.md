# MMAudio 运行与部署速记

## 线上部署
- 当前推荐发布方式为镜像部署，目标机使用 `compose.deploy.yaml` 从 `registry.ttd/mmaudio/mmaudio` 拉起单容器服务。
- 容器名：`mmaudio`
- 默认对外端口：`7860`
- 模型权重统一走 NFS：`/TTD-Data/MMAudio/{weights,ext_weights}`
- 输出目录：`/TTD-Data/MMAudio/output`
- 启动命令：`python3 entry.py`

## 发布方式
- 本地或构建机先完成镜像构建后，执行 `scripts/publish_image.sh` 推送到 `registry.ttd`。
- 目标机执行 `scripts/deploy_remote.sh <host> [image] [gpu_id] [port]` 拉取并部署镜像。
- 本地 `compose.yaml` 仍保留给开发态 build/run 使用；正式部署不要再把源码目录 bind mount 到 `/app`。
