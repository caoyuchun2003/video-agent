"""千帆视频生成:文生图 → MuseSteamer 图生视频(异步轮询)。

当前账号通常无纯文生视频(K2.6 / qianfan-video)权限,因此默认走:

  1. POST /v2/images/generations  (qwen-image) → 首帧 URL
  2. POST /video/generations      (musesteamer-*-i2v) → task_id
  3. GET  /video/generations?task_id=...

若日后开通了文生视频,可在 .env 设 VIDEO_PIPELINE=text2video。
"""
import base64
import os
from typing import Optional

import httpx

from .llm import QIANFAN_BASE, headers

PIPELINE = os.environ.get("VIDEO_PIPELINE", "t2i_i2v")  # t2i_i2v | text2video
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "qwen-image")
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "1280x720")
VIDEO_MODEL = os.environ.get("VIDEO_MODEL", "musesteamer-2.0-turbo-i2v")
VIDEO_DURATION = os.environ.get("VIDEO_DURATION", "5")
VIDEO_MODE = os.environ.get("VIDEO_MODE", "std")
VIDEO_ASPECT = os.environ.get("VIDEO_ASPECT_RATIO", "16:9")
CREATE_PATH = os.environ.get(
    "VIDEO_CREATE_PATH", "/beta/video/generations/qianfan-video"
)
QUERY_PATH = os.environ.get(
    "VIDEO_QUERY_PATH", "/beta/video/generations/qianfan-video"
)

_client = httpx.Client(timeout=120.0, follow_redirects=True)

_STATUS_MAP = {
    "queued": "queued",
    "queueing": "queued",
    "pending": "queued",
    "submitted": "queued",
    "running": "running",
    "processing": "running",
    "generating": "running",
    "succeeded": "succeeded",
    "succeed": "succeeded",
    "success": "succeeded",
    "completed": "succeeded",
    "failed": "failed",
    "error": "failed",
}

_FAIL_HINT = (
    "视频任务失败。请到千帆控制台开通 MuseSteamer/视频生成并确认有余额;"
    "开通后无需改代码,重试即可。"
)


def _gen_image(prompt: str) -> str:
    """文生图,返回可访问的图片 URL(尽量 https)。"""
    resp = _client.post(
        f"{QIANFAN_BASE}/v2/images/generations",
        headers=headers(),
        json={
            "model": IMAGE_MODEL,
            "prompt": prompt,
            "n": 1,
            "size": IMAGE_SIZE,
        },
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"文生图失败 HTTP {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    items = data.get("data") or []
    if not items or not items[0].get("url"):
        raise RuntimeError(f"文生图未返回 url: {str(data)[:300]}")
    url = str(items[0]["url"])
    if url.startswith("http://"):
        url = "https://" + url[len("http://") :]
    return url


def _image_as_data_url(url: str) -> str:
    """下载首帧并转为 data URL(部分环境下比带签名的 BOS URL 更稳)。"""
    r = _client.get(url)
    r.raise_for_status()
    ct = (r.headers.get("content-type") or "image/jpeg").split(";")[0].strip()
    if ct not in ("image/jpeg", "image/jpg", "image/png", "image/webp"):
        ct = "image/jpeg"
    b64 = base64.b64encode(r.content).decode("ascii")
    return f"data:{ct};base64,{b64}"


def _submit_i2v(prompt: str, image_url: str) -> str:
    """提交 MuseSteamer 图生视频,返回 task_id。"""
    duration = int(VIDEO_DURATION) if str(VIDEO_DURATION).isdigit() else 5
    last_err = ""
    # 先公网 URL;仅提交被拒时再试 data URL
    for use_data in (False, True):
        img = _image_as_data_url(image_url) if use_data else image_url
        payload = {
            "model": VIDEO_MODEL,
            "duration": duration,
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": img}},
            ],
        }
        resp = _client.post(
            f"{QIANFAN_BASE}/video/generations", headers=headers(), json=payload
        )
        if resp.status_code >= 400:
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
            continue
        data = resp.json()
        task_id = data.get("task_id") or data.get("id")
        if task_id:
            return str(task_id)
        last_err = f"无 task_id: {str(data)[:300]}"
    raise RuntimeError(f"图生视频提交失败:{last_err}")


def _submit_text2video(prompt: str) -> str:
    """纯文生视频(需账号开通对应模型)。"""
    payload = {
        "model": VIDEO_MODEL,
        "type": "text2video",
        "model_parameters": {
            "prompt": prompt,
            "mode": VIDEO_MODE,
            "aspect_ratio": VIDEO_ASPECT,
            "duration": str(VIDEO_DURATION),
            "sound": "off",
        },
    }
    resp = _client.post(
        f"{QIANFAN_BASE}{CREATE_PATH}", headers=headers(), json=payload
    )
    if resp.status_code >= 400:
        raise RuntimeError(
            f"文生视频提交失败 HTTP {resp.status_code}: {resp.text[:400]}"
        )
    data = resp.json()
    inner = data.get("data") if isinstance(data.get("data"), dict) else data
    task_id = (
        (inner or {}).get("task_id") or data.get("task_id") or data.get("id")
    )
    if not task_id:
        raise RuntimeError(f"文生视频未返回 task_id: {data}")
    return str(task_id)


def submit_task(prompt: str) -> str:
    """提交视频任务,返回 task_id。"""
    if PIPELINE == "text2video":
        return _submit_text2video(prompt)
    image_url = _gen_image(prompt)
    return _submit_i2v(prompt, image_url)


def _extract_video_url(data: dict) -> Optional[str]:
    root = data.get("data") if isinstance(data.get("data"), dict) else data
    if not isinstance(root, dict):
        return None
    result = root.get("task_result") or root.get("result")
    if isinstance(result, dict):
        videos = result.get("videos")
        if isinstance(videos, list) and videos:
            u = videos[0].get("url") or videos[0].get("video_url")
            if u:
                return u
        u = result.get("video_url") or result.get("url")
        if u:
            return u
    content = root.get("content")
    if isinstance(content, dict):
        u = content.get("video_url") or content.get("url")
        if u:
            return u
    if isinstance(content, list):
        for item in content:
            if not isinstance(item, dict):
                continue
            vu = item.get("video_url")
            if isinstance(vu, dict):
                vu = vu.get("url")
            if vu:
                return vu
    return root.get("video_url") or root.get("url") or data.get("video_url")


def get_task(task_id: str) -> dict:
    """查询任务,返回 {status, video_url?, error?}。"""
    # MuseSteamer 查询优先(默认管线)
    resp = _client.get(
        f"{QIANFAN_BASE}/video/generations",
        headers=headers(),
        params={"task_id": task_id},
    )
    if resp.status_code >= 400 and PIPELINE == "text2video":
        resp = _client.get(
            f"{QIANFAN_BASE}{QUERY_PATH}",
            headers=headers(),
            params={"task_id": task_id, "model": VIDEO_MODEL},
        )
    resp.raise_for_status()
    data = resp.json()
    root = data.get("data") if isinstance(data.get("data"), dict) else data
    raw_status = str(
        (root or {}).get("task_status")
        or (root or {}).get("status")
        or data.get("status")
        or ""
    ).lower()
    status = _STATUS_MAP.get(raw_status, "running" if raw_status else "running")
    out: dict = {"status": status}
    if status == "succeeded":
        url = _extract_video_url(data)
        if url:
            out["video_url"] = url
        else:
            out["status"] = "failed"
            out["error"] = f"任务成功但未找到视频 URL,原始返回:{str(data)[:300]}"
    elif status == "failed":
        msg = str(
            (root or {}).get("task_status_msg")
            or data.get("error")
            or data.get("message")
            or ""
        ).strip()
        out["error"] = msg if msg else _FAIL_HINT
    return out
