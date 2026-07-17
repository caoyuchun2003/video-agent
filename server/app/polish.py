"""ERNIE 提示词优化:把用户随口的想法扩写成专业的视频镜头描述。"""
import json

from . import llm

SYSTEM_PROMPT = """你是一位专业的短视频导演和 AI 视频提示词专家。
用户会给你一个简单的视频想法,你要把它扩写成一段适合 AI 文生视频模型的中文提示词。

要求:
- 补充画面主体、场景细节、景别与运镜(如特写/全景、推拉摇移)、光线氛围、色调风格
- 描述具体、有画面感,一段话 80~150 字,不要分镜列表
- 保留用户想法的核心意图,不要跑题
- 同时给出一个 12 字以内的作品标题

严格按 JSON 输出,不要输出其他内容:
{"title": "作品标题", "polished_prompt": "优化后的提示词", "style": "一句话风格概括"}"""


def polish(idea: str) -> dict:
    """返回 {title, polished_prompt, style};模型输出异常时降级为原想法。"""
    content = llm.chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": idea},
        ],
        response_format_json=True,
    )
    try:
        data = json.loads(content)
        return {
            "title": str(data.get("title", ""))[:20] or idea[:12],
            "polished_prompt": str(data.get("polished_prompt", "")) or idea,
            "style": str(data.get("style", "")),
        }
    except (json.JSONDecodeError, AttributeError):
        return {"title": idea[:12], "polished_prompt": content or idea, "style": ""}
