# app/video_script_helper.py
import base64
import json
import logging
import textwrap
from typing import List, Dict

import litellm

logger = logging.getLogger(__name__)


class VideoScriptHelper:
  """调用多模态 LLM（通过 LiteLLM），根据书页图片生成视频导读脚本"""

  def __init__(
      self,
      api_key: str = "",
      base_url: str = "",
      model: str = "gemini/gemini-2.5-flash",
      temperature: float = 0.3,
  ):
    self.api_key = api_key
    self.base_url = base_url
    self.model = model
    self.temperature = temperature

  async def generate_script(
      self,
      page_images: List[bytes],
      book_title: str,
      chapter_title: str,
      context_hint: str = ""
  ) -> List[Dict]:
    """
    发送多张书页图片至多模态 LLM，返回视频脚本 JSON。

    :param page_images: 书页图片的 bytes 列表（WebP/PNG）
    :param book_title: 书名
    :param chapter_title: 章节标题
    :param context_hint: 额外上下文提示
    :return: [{scene_id, page_no, narration, focus_area, camera_action, duration}]
    """
    if not page_images:
      return []

    system_prompt = self._build_system_prompt(book_title, chapter_title, context_hint)

    # 构建 vision 格式的用户消息
    user_content = []
    for i, img_bytes in enumerate(page_images):
      b64 = base64.b64encode(img_bytes).decode("utf-8")
      user_content.append({
        "type": "image_url",
        "image_url": {
          "url": f"data:image/webp;base64,{b64}",
          "detail": "high"
        }
      })
      user_content.append({
        "type": "text",
        "text": f"[第 {i + 1} 张图片 / 第 {i + 1} 页]"
      })

    messages = [
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_content}
    ]

    kwargs = {
      "model": self.model,
      "messages": messages,
      "temperature": self.temperature,
    }
    if self.api_key:
      kwargs["api_key"] = self.api_key
    if self.base_url:
      kwargs["api_base"] = self.base_url

    try:
      response = await litellm.acompletion(**kwargs)
      raw = response.choices[0].message.content
      if not raw:
        logger.error("LLM 返回空内容")
        return []

      clean = raw.replace("```json", "").replace("```", "").strip()
      script = json.loads(clean)

      if isinstance(script, list) and len(script) > 0:
        for idx, item in enumerate(script):
          item.setdefault("scene_id", idx + 1)  # 兜底：按位置补全，保证连续
          item.setdefault("img_index", 1)
          item.setdefault("narration", "")
          item.setdefault("focus_area", [0.0, 0.0, 1.0, 1.0])
          item.setdefault("camera_action", "Steady")
          item.setdefault("duration", 5.0)
          # 兼容旧字段名：AI 偶尔还是会返回 page_no
          if "page_no" in item and "img_index" not in item:
            item["img_index"] = item.pop("page_no")
        # 按 scene_id 排序，防止 AI 乱序输出
        script.sort(key=lambda s: s.get("scene_id", 0))
        return script

      return []

    except json.JSONDecodeError as e:
      logger.error(f"LLM 返回非 JSON: {raw[:500]}")
      return []
    except Exception as e:
      logger.error(f"LLM API 调用失败: {e}")
      return []

  async def generate_script_from_pdf(
      self,
      pdf_bytes: bytes,
      book_title: str,
      chapter_title: str,
      context_hint: str = ""
  ) -> List[Dict]:
    """
    将整个章节的 PDF 切片（bytes）作为文档直接送给多模态 LLM 生成视频脚本。

    相较于逐页 WebP 图片，PDF 原生格式保留矢量文字、排版结构，
    模型对文本内容的理解更精准，且只需一次 API 调用（省 token）。

    :param pdf_bytes:     章节 PDF 切片的原始字节
    :param book_title:    书名
    :param chapter_title: 章节标题
    :param context_hint:  额外上下文提示
    :return: [{scene_id, img_index, narration, focus_area, camera_action, duration}]
    """
    if not pdf_bytes:
      return []

    system_prompt = self._build_system_prompt(book_title, chapter_title, context_hint)

    # LiteLLM 的 document 格式（base64 编码的 PDF）
    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    user_content = [
      {
        "type": "text",
        "text": (
          "以下是本章节的完整 PDF 内容。PDF 中每一页对应一张书页图片，"
          "页码从 1 开始连续编号，请在 img_index 字段中使用这个连续序号（而非书中印刷的页码）。"
          "请根据 PDF 内容生成视频导读脚本。"
        )
      },
      {
        "type": "image_url",
        "image_url": {
          "url": f"data:application/pdf;base64,{b64_pdf}",
        }
      }
    ]

    messages = [
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_content}
    ]

    kwargs = {
      "model": self.model,
      "messages": messages,
      "temperature": self.temperature,
    }
    if self.api_key:
      kwargs["api_key"] = self.api_key
    if self.base_url:
      kwargs["api_base"] = self.base_url

    try:
      response = await litellm.acompletion(**kwargs)
      raw = response.choices[0].message.content
      if not raw:
        logger.error("LLM (PDF模式) 返回空内容")
        return []

      clean = raw.replace("```json", "").replace("```", "").strip()
      script = json.loads(clean)

      if isinstance(script, list) and len(script) > 0:
        for idx, item in enumerate(script):
          item.setdefault("scene_id", idx + 1)
          item.setdefault("img_index", 1)
          item.setdefault("narration", "")
          item.setdefault("focus_area", [0.0, 0.0, 1.0, 1.0])
          item.setdefault("camera_action", "Steady")
          item.setdefault("duration", 5.0)
          if "page_no" in item and "img_index" not in item:
            item["img_index"] = item.pop("page_no")
        script.sort(key=lambda s: s.get("scene_id", 0))
        return script

      return []

    except json.JSONDecodeError:
      logger.error(f"LLM (PDF模式) 返回非 JSON: {raw[:500] if raw else ''}")
      return []
    except Exception as e:
      logger.error(f"LLM (PDF模式) API 调用失败: {e}")
      return []

  def _build_system_prompt(self, book_title: str, chapter_title: str, context_hint: str) -> str:
    hint = f"\n补充背景：{context_hint}" if context_hint else ""
    return textwrap.dedent(f"""
      你是一位博览群书的知识授课老师，能够讲透任何学科领域的书籍内容。
      当前任务：为《{book_title}》章节「{chapter_title}」制作一期深度授课视频，目标总时长 3~8 分钟。{hint}

      ## 核心原则：
      内容第一：
      - 脚本内容完全由 PDF 决定
      - 针对 PDF 中提到的内容，需要展开来讲，但不能脱离 PDF 内容
      - 场景顺序要严格按照 PDF 内容顺序
      - 对于章节过渡的页面，必须确保生成的场景属于当前章节的内容范围内，不能有上一章节或下一章节的内容

      具体禁令：
      - 禁止提及 PDF 中不存在的图表、对比、数据、结构
      - 禁止套用任何固定模板（如"先看左边……再看右边……"），除非 PDF 里真的有这样的版式
      - 禁止捏造或自创任何与 PDF 内容无关的信息，所有 narration、focus_area、camera_action 必须 100% 来源于 PDF 的实际内容
      
      讲解风格要求：
      - 讲透原理，不只是转述：说清楚"为什么是这样"，而不只是"书上说了什么"
      - 口语化，有节奏感，直接面向听众说话
      - 禁止注水：不说"非常重要""意义深远"这类空话

      ## 场景数量
      - 按 PDF 实际页数和内容密度自然划分，不强制每页的场景数
      - 全章总场景数控制在 8~20 个，保证总时长 3~8 分钟
      - 第一个场景点明本章核心问题；每个子标题至少有一个场景；最后一个场景给出结论或留下思考
      - 忽略路人甲碎碎念的内容

      ## 输入说明
      用户发送的是本章节完整的 PDF 文件。PDF 第 N 页对应 img_index = N（从 1 开始），
      img_index 不能超过 PDF 的实际总页数。

      ## 输出字段规范
      ### scene_id（整数）
      从 1 开始的连续整数，严格递增。

      ### img_index（整数）
      该场景对应的 PDF 页码（1-based）。

      ### narration（字符串）
      旁白讲解词。直接面向听众朗读，口语化，长度 60~200 字。

      ### focus_area（数组）
      【硬性规定】必须统一固定为 [0.0, 0.0, 1.0, 1.0]。严禁根据内容去计算局部坐标。

      ### camera_action（字符串）
      【硬性规定】必须统一固定为 "Steady"。严禁使用 ZoomIn、PanLeft 或 PanRight。

      ### duration（浮点数）
      场景时长（秒）= narration 字数 ÷ 3.5。最短 10.0 秒。

      ## 输出格式
      只返回纯 JSON 数组，不加任何 markdown 标记、注释或前后说明文字。

      [
        {{
          "scene_id": 1,
          "img_index": 1,
          "narration": "这一章要解决的问题是……",
          "focus_area": [0.0, 0.0, 1.0, 1.0],
          "camera_action": "Steady",
          "duration": 18.0
        }},
        {{
          "scene_id": 2,
          "img_index": 1,
          "narration": "先看这个核心概念……",
          "focus_area": [0.0, 0.2, 1.0, 0.4],
          "camera_action": "ZoomIn",
          "duration": 24.0
        }}
      ]
    """)
