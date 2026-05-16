# app/tts_helper.py
import logging
import os

import edge_tts
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)

# 可用中文音色
VOICES = {
  "male": "zh-CN-YunxiNeural",  # 沉稳男声
  "female": "zh-CN-XiaoxiaoNeural",  # 知性女声
  "narrator": "zh-CN-YunjianNeural",  # 讲书人（推荐）
}


class TtsHelper:
  """Edge-TTS 封装：将旁白文本转为 MP3 音频"""

  def __init__(self, voice: str = "zh-CN-YunjianNeural"):
    self.voice = voice

  async def synthesize(self, text: str, output_path: str) -> float:
    """
    合成语音并返回实际时长。不再接受 target_duration，保证语速自然。
    """
    if not text or not text.strip():
      return 0.0

    try:
      os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

      # 直接使用 API 合成
      communicate = edge_tts.Communicate(text, self.voice)
      await communicate.save(output_path)

      audio = MP3(output_path)
      duration = audio.info.length # 单位是秒
      logger.info(f"TTS 成功: 时长 {duration:.2f}s")
      return duration

    except Exception as e:
      logger.error(f"TTS 合成异常 (API方式): {e}", exc_info=True)
      return 0.0

  # def _calc_rate(self, text: str, target_duration: float) -> str:
  #   """根据目标时长计算语速"""
  #   if target_duration <= 0:
  #     return "+0%"
  #
  #   char_count = len(text)
  #   # 中文正常语速约 3.5 字/秒
  #   natural_duration = char_count / 3.5
  #   ratio = natural_duration / target_duration
  #
  #   if ratio > 1.3:
  #     pct = min(int((ratio - 1) * 100), 50)
  #     return f"+{pct}%"
  #   elif ratio < 0.7:
  #     pct = min(int((1 - ratio) * 100), 50)
  #     return f"-{pct}%"
  #   return "+0%"
  #
  # async def _get_duration(self, file_path: str) -> float:
  #   """通过 ffprobe 获取音频时长"""
  #   try:
  #     proc = await asyncio.create_subprocess_exec(
  #         "ffprobe", "-v", "error", "-show_entries",
  #         "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
  #         file_path,
  #         stdout=asyncio.subprocess.PIPE,
  #         stderr=asyncio.subprocess.PIPE
  #     )
  #     stdout, _ = await proc.communicate()
  #     if proc.returncode == 0:
  #       return float(stdout.decode().strip())
  #   except Exception:
  #     pass
  #   return 0.0
