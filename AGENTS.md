# MMAudio 运行与部署速记

## 线上部署
- 当前推荐发布方式为镜像部署，目标机使用 `compose.deploy.yaml` 从 `registry.ttd/mmaudio/mmaudio` 拉起单容器服务。
- 容器名统一为：`mmaudio`
- 默认对外端口：`7860`
- 当前正式部署实例：
  - `ttd-worker` GPU `0`
  - `ttd-rocky`（`192.168.100.19`）GPU `1`
- 当前内网域名统一为：`mmaudio`、`mmaudio-api`
- 两台实例都注册同一组 Caddy host，由 CDP 自动聚合为多 backend 负载均衡。
- 模型权重统一走 NFS：`/TTD-Data/MMAudio/{weights,ext_weights}`
- 输出目录：`/TTD-Data/MMAudio/output`
- 启动命令：`python3 entry.py`

## 发布主线
- 开发态仍使用 `compose.yaml`；正式部署只使用 `compose.deploy.yaml`。
- 正式发布主线分两段：
  - CI：构建镜像并推到 `registry.ttd/mmaudio/mmaudio`
  - CD：目标机本机 `docker compose pull + up -d`
- 正式部署不再依赖源码 bind mount 到 `/app`。

## 推荐入口
- 预检：`ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags preflight`
- 构建并推镜像：`ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags ci -e image_tag=h-<tag>`
- 部署到正式机：`ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags prepare -e image_tag=h-<tag>`
- 回归验证：`ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags verify -e image_tag=h-<tag>`

## 日常发布步骤
1. 在仓库完成代码修改。
2. 先跑预检：`ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags preflight`
3. 为本次发布选一个 tag，例如 `h-<gitsha12>`。
4. 执行 CI 构建并推镜像：`ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags ci -e image_tag=h-<gitsha12>`
5. 执行目标机部署：`ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags prepare -e image_tag=h-<gitsha12>`
6. 执行回归验证：`ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags verify -e image_tag=h-<gitsha12>`
7. 验证通过后，再更新 `latest` 使用记录或继续后续发布动作。

## 快速脚本入口
- 推已有本地镜像：`scripts/publish_image.sh`
- 远端触发 compose 部署：`scripts/deploy_remote.sh <host> [image] [gpu_id] [port]`
- 这两个脚本可作为便捷入口，但正式推荐主线以 `ansible/` 为准。

## 低带宽环境建议
- `code-server` 到机房链路长期只有约 `5 MB/s`，不要默认从开发机传大镜像或大 build context。
- 优先使用：
  - `ttd-nest` / 构建机直接 build + push
  - 或目标机/构建机基于现有正式镜像做最小增量 rebuild 后再 push
- 增量 rebuild 只是加速手段，不是长期主构建路径；长期仍应回到稳定的 CI 构建流程。

## 回归标准
- 不能只看 `/health`。
- 最小正式回归至少包括：
  - `GET /health` 返回 `200`
  - `GET /` 直接返回 Gradio 首页，不应再跳 `/gradio`
  - 通过内网域名 `mmaudio` 与 `mmaudio-api` 访问健康检查返回 `200`
  - 至少一次真实业务端点验证，例如：
    - `POST /api/v1/text-to-audio`
    - 返回 `audio/wav`
    - 文件头为 `RIFF`

## 服务发现说明
- `mmaudio` 与 `mmaudio-api` 走内网 `caddy` 自动发现。
- 正式部署 compose 中必须保留：
  - `caddy: "mmaudio:80, mmaudio-api:80"`
  - `caddy.reverse_proxy: "{{upstreams 7860}}"`
  - 外部 `caddy` network
- 当前正式状态下，`ttd-worker` 与 `ttd-rocky` 都声明相同的 `mmaudio` / `mmaudio-api` labels。
- 当前自动发现链路不是目标机容器直连 `cdp`，而是：
  - 业务容器 labels
  - `index_api` 聚合
  - `caddy-label`
  - `caddy-docker-proxy`
