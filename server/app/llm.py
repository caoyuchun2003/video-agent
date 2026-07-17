"""千帆 v2 chat completions 封装(提示词优化用)。"""
import os
from typing import Optional

import httpx

QIANFAN_BASE = "https://qianfan.baidubce.com"
API_KEY = os.environ.get("QIANFAN_API_KEY", "")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "deepseek-v3.2")

_client = httpx.Client(timeout=60.0)


def headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def chat(messages: list, response_format_json: bool = False) -> str:
    """调一次 chat completions,返回文本内容。"""
    payload: dict = {"model": CHAT_MODEL, "messages": messages}
    if response_format_json:
        payload["response_format"] = {"type": "json_object"}
    resp = _client.post(f"{QIANFAN_BASE}/v2/chat/completions", headers=headers(), json=payload)
    resp.raise_for_status()
    data = resp.json()
    if "choices" not in data or not data["choices"]:
        raise RuntimeError(f"千帆返回异常: {data}")
    return data["choices"][0]["message"].get("content") or ""
