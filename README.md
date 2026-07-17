# video-agent

视频创作 Agent：说个想法 → 模型扩写镜头提示词 → 千帆生成短视频 → 在线播放/下载。

## 架构

```
浏览器(video.yuchuntest.com / GitHub Pages, HTTPS)
   → 百度 CFC 网关(HTTPS; path 白名单 + 注入网关令牌)
      → 百度云 BCC http://IP/video/ → podman :8001 (FastAPI)
         ├─ /prompt/polish   提示词优化(同步)
         ├─ /video/create    文生图 → 图生视频 → task_id
         └─ /video/status    查询任务状态 / 视频 URL
```

默认管线 **文生图 (qwen-image) → MuseSteamer 图生视频**（账号通常无纯文生视频权限）。
生成约 1～5 分钟，前端轮询；任务记在 localStorage。

## 目录

| 目录 | 说明 | 部署到 |
| --- | --- | --- |
| `web/` | Vue 3 + Vite | GitHub Pages → `video.yuchuntest.com` |
| `cfc/` | 网关（`src/` 打包） | 百度 CFC |
| `server/` | FastAPI | BCC podman `:8001`，nginx `/video/` |

## 密钥安全

- `QIANFAN_API_KEY`、`GATEWAY_TOKEN` **只**放服务器 `.env` / CFC 环境变量，**永不**进 Git
- `.env`、`*.zip`、`template.deploy.yaml`、`.secrets/` 已在 `.gitignore`
- push 前：`./scripts/check-no-secrets.sh`

## 本地开发

```bash
cd server
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
cp .env.example .env   # 填 QIANFAN_API_KEY / GATEWAY_TOKEN
./venv/bin/uvicorn app.main:app --reload --port 8001

cd web
npm install
VITE_API_URL=http://localhost:8001 \
VITE_DEV_GATEWAY_TOKEN=<token> \
npm run dev
```

## 部署摘要

1. **BCC**：`/opt/video-agent` + podman `video-agent` 映射 `8001`，nginx `location /video/`
2. **CFC**：`cd cfc && BACKEND_URL=http://IP/video GATEWAY_TOKEN=... ./scripts/deploy.sh`
3. **Pages**：仓库 Variables 设 `API_URL` = CFC 根地址；DNS CNAME `video` → `caoyuchun2003.github.io`
