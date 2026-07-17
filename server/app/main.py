"""FastAPI 入口:/prompt/polish、/video/create、/video/status + 网关令牌校验 + 频控。"""
import hmac
import os
import time
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Header, HTTPException, Query  # noqa: E402
from fastapi.concurrency import run_in_threadpool  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from . import polish as polish_mod  # noqa: E402
from . import video  # noqa: E402

GATEWAY_TOKEN = os.environ.get("GATEWAY_TOKEN", "")
# 熟人访问口令(防公网刷额度);空则不校验(仅本地调试)
ACCESS_PHRASE = os.environ.get("ACCESS_PHRASE", "").strip()
RATE_PER_MINUTE = int(os.environ.get("RATE_PER_MINUTE", "2"))
MAX_ACTIVE_TASKS = int(os.environ.get("MAX_ACTIVE_TASKS", "3"))

app = FastAPI(title="video-agent")

# 内存级频控:提交时间戳 + 进行中任务集合(个人项目,单进程够用)
_recent_submits: list = []
_active_tasks: set = set()


class PolishRequest(BaseModel):
    idea: str = Field(min_length=1, max_length=500)
    phrase: str = Field(default="", max_length=64)


class CreateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    phrase: str = Field(default="", max_length=64)


def _check_token(token: Optional[str]) -> None:
    if not GATEWAY_TOKEN:
        raise HTTPException(500, "服务器未配置 GATEWAY_TOKEN")
    if token != GATEWAY_TOKEN:
        raise HTTPException(401, "无效的网关令牌")


def _check_phrase(phrase: Optional[str]) -> None:
    if not ACCESS_PHRASE:
        return
    got = (phrase or "").strip()
    if not hmac.compare_digest(got, ACCESS_PHRASE):
        raise HTTPException(403, "访问口令不正确")


def _check_rate() -> None:
    now = time.time()
    while _recent_submits and now - _recent_submits[0] > 60:
        _recent_submits.pop(0)
    if len(_recent_submits) >= RATE_PER_MINUTE:
        raise HTTPException(429, f"提交太频繁,每分钟最多 {RATE_PER_MINUTE} 个任务,请稍候")
    if len(_active_tasks) >= MAX_ACTIVE_TASKS:
        raise HTTPException(429, f"同时进行中的任务已达上限 {MAX_ACTIVE_TASKS},请等待完成")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "active_tasks": len(_active_tasks)}


@app.post("/prompt/polish")
async def prompt_polish(
    req: PolishRequest, x_gateway_token: Optional[str] = Header(default=None)
) -> dict:
    _check_token(x_gateway_token)
    _check_phrase(req.phrase)
    try:
        return await run_in_threadpool(polish_mod.polish, req.idea)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"提示词优化失败:{e}") from e


@app.post("/video/create")
async def video_create(
    req: CreateRequest, x_gateway_token: Optional[str] = Header(default=None)
) -> dict:
    _check_token(x_gateway_token)
    _check_phrase(req.phrase)
    _check_rate()
    try:
        task_id = await run_in_threadpool(video.submit_task, req.prompt)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"提交视频任务失败:{e}") from e
    _recent_submits.append(time.time())
    _active_tasks.add(task_id)
    return {"task_id": task_id}


@app.get("/video/status")
async def video_status(
    task_id: str = Query(min_length=1, max_length=128),
    x_gateway_token: Optional[str] = Header(default=None),
) -> dict:
    _check_token(x_gateway_token)
    try:
        result = await run_in_threadpool(video.get_task, task_id)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"查询任务失败:{e}") from e
    if result["status"] in ("succeeded", "failed"):
        _active_tasks.discard(task_id)
    return result
