# 服务器部署(百度云测试服务器,与 my-agent 共存)

video-agent 跑 **8001** 端口(my-agent 占 8000)。

## 1. 准备

```bash
cd /opt
sudo mkdir -p video-agent && sudo chown $USER video-agent
# 上传 server/ 目录内容到 /opt/video-agent
cd /opt/video-agent
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 2. 配置

```bash
cp .env.example .env
vi .env
# QIANFAN_API_KEY:千帆控制台的 bce-v3/ALTAK-.../...(可与 my-agent 共用)
# GATEWAY_TOKEN:openssl rand -hex 32 生成(建议与 my-agent 用不同的值)
# VIDEO_MODEL:千帆控制台"模型广场→视频生成"里的实际模型名
```

### ⚠️ 首次部署先核对视频 API

`app/video.py` 按 OpenAI 兼容风格假设了接口(POST /v2/video/generations 提交、
GET /v2/video/generations/{task_id} 查询)。部署前:

1. 查千帆官方文档「视频生成」确认真实路径和字段
2. 路径不同 → 改 .env 里的 `VIDEO_CREATE_PATH` / `VIDEO_QUERY_PATH`
3. 请求/响应字段不同 → 改 `app/video.py`(所有差异都封装在这一个文件)
4. 用真实 Key 手工 curl 验证一遍再上线

## 3. systemd

`sudo vi /etc/systemd/system/video-agent.service`:

```ini
[Unit]
Description=video-agent FastAPI
After=network.target

[Service]
WorkingDirectory=/opt/video-agent
ExecStart=/opt/video-agent/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now video-agent
```

安全组:入方向放行 TCP 8001。

## 4. 验证

```bash
curl http://127.0.0.1:8001/health

curl -X POST http://127.0.0.1:8001/prompt/polish \
  -H 'Content-Type: application/json' \
  -H "X-Gateway-Token: <token>" \
  -d '{"idea":"一只橘猫在雨后的屋顶上看日落"}'

curl -X POST http://127.0.0.1:8001/video/create \
  -H 'Content-Type: application/json' \
  -H "X-Gateway-Token: <token>" \
  -d '{"prompt":"<上一步返回的 polished_prompt>"}'
# → {"task_id":"..."}

curl "http://127.0.0.1:8001/video/status?task_id=<task_id>" \
  -H "X-Gateway-Token: <token>"
# 轮询到 {"status":"succeeded","video_url":"..."}
```

---

# CFC 部署

新建一个**独立**的 CFC 函数(与 my-agent 的网关分开):

1. 函数计算控制台 → 创建函数,Node.js 运行时,粘贴 `cfc/index.js`(入口 `index.handler`)
2. 环境变量:
   - `BACKEND_URL` = `http://<服务器公网IP>:8001`
   - `GATEWAY_TOKEN` = 与服务器 .env 相同
   - `ALLOW_ORIGIN` = `https://<GitHub用户名>.github.io`
3. HTTP 触发器:方法 GET + POST + OPTIONS,不认证,超时 60 秒
4. 验证:

```bash
curl -X POST 'https://<CFC URL>/prompt/polish' \
  -H 'Content-Type: application/json' \
  -d '{"idea":"测试"}'
```

---

# GitHub Pages

1. 新建仓库 `video-agent`(与 `web/vite.config.js` 的 `base: '/video-agent/'` 一致),推送
2. Settings → Pages → Source 选 **GitHub Actions**
3. Settings → Secrets and variables → Actions → **Variables** 新建 `API_URL` = CFC 触发器基地址(**不带路径**)
4. push main 自动部署,打开 `https://<用户名>.github.io/video-agent/`
