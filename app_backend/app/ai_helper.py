# app/ai_helper.py
import json
import logging
from typing import List, Dict

import httpx

logger = logging.getLogger(__name__)


class AiHelper:
  def __init__(self, api_key: str, base_url: str, model: str, max_tokens: int = 128000):
    self.api_key = api_key
    self.base_url = base_url.rstrip("/")
    self.model = model
    self.max_tokens = max_tokens

  async def extract_terms_from_text(self, book_text: str) -> List[Dict[str, str]]:
    """
    发送文本给 AI，提取术语
    返回格式: [{"term": "DeFi", "desc": "去中心化金融..."}]
    """
    if not book_text or len(book_text) < 50:
      return []

    # 1. 截取文本
    # 虽然现代大模型窗口很大，但为了防止 API 400 错误（超出最大 Token）以及控制成本，
    # 建议还是做一个安全截断。50000 字符通常覆盖 2-3 万 Token，足够 AI 理解上下文。
    safe_text = book_text[:self.max_tokens]
    logger.info(f"book_text len {len(book_text)} characters, safe_text len {len(safe_text)} characters")

    # 2. 构造通用 Prompt
    prompt = f"""
        你是一个专业的书籍编辑和领域专家。请分析以下书籍片段的内容，识别其所属的**学科领域或行业背景**，并从中提取 10 到 50 个该领域最核心的**专业术语**（关键词）。
        
        要求：
        1. **领域自适应**：请根据文本内容自动判断领域（例如：如果是区块链书就提Web3术语，如果是医学书就提医学术语，如果是历史书就提专有名词/事件）。
        2. **专业术语提取**：提取专业术语时，要考虑术语的**专业度**和**上下文相关度**，不要提取无意义或通用的名词。
        3. **排除通用词**：不要提取“我们”、“分析”、“发展”等毫无意义通用词汇，必须是具有特定领域含义的专业术语名词。
        4. **解释精准**：解释要简练精准，适合初学者理解，解释长度控制在 80 字以内。
        5. **纯净格式**：请只返回一个纯 JSON 数组，不要包含 ```json、Markdown 标记或任何其他前缀后缀。
        
        返回格式示例：
        [
            {{"term": "术语A", "desc": "术语A的解释..."}},
            {{"term": "术语B", "desc": "术语B的解释..."}}
        ]
        
        书籍内容片段：
        {safe_text} 
        """

    # 3. 调用 OpenAI 兼容接口
    url = f"{self.base_url}/chat/completions"
    headers = {
      "Authorization": f"Bearer {self.api_key}",
      "Content-Type": "application/json"
    }
    payload = {
      "model": self.model,
      "messages": [{"role": "user", "content": prompt}],
      "temperature": 0.3,  # 降低温度，让结果更确定、更像知识库
      "stream": False
    }

    try:
      async with httpx.AsyncClient(timeout=120) as client:  # 放宽超时时间，长文本处理较慢
        resp = await client.post(url, json=payload, headers=headers)

      if resp.status_code != 200:
        logger.error(f"AI API Error {resp.status_code}: {resp.text}")
        return []

      data = resp.json()
      raw_content = data['choices'][0]['message']['content']

      # 清洗 Markdown (以防万一 AI 不听话)
      clean_json = raw_content.replace("```json", "").replace("```", "").strip()

      # 尝试解析
      terms_data = json.loads(clean_json)
      if isinstance(terms_data, list):
        return terms_data
      return []

    except Exception as e:
      logger.error(f"AI 提取失败: {e}")
      return []
