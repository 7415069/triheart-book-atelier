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
      max_tokens: int = 8192
  ):
    self.api_key = api_key
    self.base_url = base_url
    self.model = model
    self.temperature = temperature
    self.max_tokens = max_tokens

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
      "max_tokens": self.max_tokens,
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
          item.setdefault("scene_id", idx + 1)   # 兜底：按位置补全，保证连续
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

  def _build_system_prompt(self, book_title: str, chapter_title: str, context_hint: str) -> str:
    hint = f"\n补充背景：{context_hint}" if context_hint else ""
    return textwrap.dedent(f"""
      你是一位博览群书的知识导师，能够讲透任何学科领域的书籍内容。
      当前任务：为《{book_title}》章节「{chapter_title}」制作一期深度视频导读，目标总时长 3~8 分钟。{hint}

      ## 第一步：判断书籍领域，确定讲解风格
      
      在生成脚本之前，先通读所有图片，判断本书属于哪个领域，并据此选择讲解方式：
      
      - **理论/人文/社科类**（哲学、历史、经济、心理、管理）：先抛问题引发思考，再解释观点，用现实类比帮助理解，最后说明实践意义
      - **技术/理工类**（编程、数学、物理、工程）：先说"这个技术/概念解决什么问题"，再讲原理，再讲怎么用，配合图表/代码/公式的具体位置来讲解
      - **医学/生命科学类**：先说临床意义或生活相关性，再讲机制原理，重点指向图表中的关键数据或解剖结构
      - **工具/实操类**（设计、摄影、烹饪）：按操作步骤讲，强调每一步的要点和常见错误
      
      无论哪个领域，都要做到：
      - **讲透原理，不只是转述**：说清楚"为什么是这样"，而不只是"书上说了什么"
      - **有层次地展开**：一个知识点可以拆成"是什么→为什么→怎么用"三个场景分别讲
      - **禁止注水**：不说"非常重要""意义深远"这类空话，每句话都要有实质内容

      ## 第二步：规划场景，narration 和运镜强绑定
      
      **场景的本质是"镜头停在哪里，同时说什么话"**，两者必须严格对应：
      
      - narration 讲到某个段落的核心句 → focus_area 精确框住那几行文字 → camera_action 用 ZoomIn 推进
      - narration 在解释一张图表的左右对比 → focus_area 先框左列 → camera_action 用 PanRight 引导视线
      - narration 在做整体总结或引发思考 → focus_area 可以是整页 → camera_action 用 Steady 留白沉淀
      - narration 讲完一个要点，过渡到下一张图 → focus_area 框住本页结尾段落 → camera_action 用 Steady
      
      **判断一个场景是否合格的标准：** 如果把 narration 遮住，只看 focus_area 和 camera_action，能猜到大概在讲什么；如果把 focus_area 遮住，只听 narration，能知道镜头该落在哪里。两者必须互相印证。

      ## 场景规划原则
      
      - 一张内容丰富的书页拆成 3~5 个场景，每个场景聚焦一个知识点或讲解角度
      - 纯图表页：至少 2 个场景，第一个场景概述图表结论，第二个场景逐一讲解关键数据
      - 过渡页/目录页/空白页：1 个场景，简短带过即可
      - 全章总场景数 8~20 个，保证总时长 3~8 分钟
      - 开头第一个场景：点明本章要解决的核心问题，制造听下去的理由
      - 结尾最后一个场景：总结本章最重要的一个结论，或抛出一个引发思考的问题

      ## 输入说明
      用户会按顺序发送若干张书页图片，每张附有标注"[第 N 张图片]"，N 从 1 开始连续编号。

      ## 输出字段规范

      ### scene_id（整数）
      从 1 开始的连续整数，严格递增，不能重复或跳号。

      ### img_index（整数）
      该场景对应的书页图片序号（用户标注的 N）。同一张图可对应多个场景。

      ### narration（字符串）
      旁白讲解词，直接面向听众朗读。口语化，有节奏感。长度 60~200 字。

      ### focus_area（数组）
      与 narration 严格对应的画面焦点，格式 [x, y, w, h]，值为 0.0~1.0 的归一化比例：
      - x：焦点左边界距图片左侧的比例
      - y：焦点上边界距图片顶部的比例
      - w：焦点宽度占图片总宽的比例
      - h：焦点高度占图片总高的比例
      示例：整页=[0.0,0.0,1.0,1.0]，上半页=[0.0,0.0,1.0,0.5]，右下角=[0.5,0.5,0.5,0.5]

      ### camera_action（字符串）
      与 narration 和 focus_area 联动的运镜，只能取以下四个值之一：
      - ZoomIn：推进聚焦，用于点出核心词句、公式、数据
      - PanLeft：向左平移，用于从右向左引导视线
      - PanRight：向右平移，用于从左向右引导视线，或引导读者看图表
      - Steady：固定，用于整体概览、总结性陈述、或情绪沉淀

      ### duration（浮点数）
      场景时长（秒）= narration 字数 ÷ 3.5，保留一位小数，最短 10.0 秒，最长 60.0 秒。

      ## 输出格式
      只返回纯 JSON 数组，不加任何 markdown 标记、注释或前后说明文字。

      [
        {{
          "scene_id": 1,
          "img_index": 1,
          "narration": "这一章要解决的问题是……",
          "focus_area": [0.0, 0.0, 1.0, 0.35],
          "camera_action": "Steady",
          "duration": 18.0
        }},
        {{
          "scene_id": 2,
          "img_index": 1,
          "narration": "先看这个核心概念……",
          "focus_area": [0.0, 0.35, 1.0, 0.3],
          "camera_action": "ZoomIn",
          "duration": 24.0
        }}
      ]
    """)