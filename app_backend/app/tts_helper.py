# app/tts_helper.py
import asyncio
import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)

# 可用中文音色
VOICES = {
  "male": "zh-CN-YunxiNeural",       # 沉稳男声
  "female": "zh-CN-XiaoxiaoNeural",  # 知性女声
  "narrator": "zh-CN-YunjianNeural", # 讲书人（推荐）
}


class TtsHelper:
  """Edge-TTS 封装：将旁白文本转为 MP3 音频"""

  def __init__(self, voice: str = "zh-CN-YunjianNeural"):
    self.voice = voice

  async def synthesize(self, text: str, output_path: str, target_duration: float = 0) -> float:
    """
    合成语音并保存为 MP3。

    :param text: 旁白文本
    :param output_path: 输出 MP3 文件路径
    :param target_duration: 目标时长（秒），0 表示不调整语速
    :return: 实际音频时长（秒）
    """
    if not text or not text.strip():
      return 0.0

    # 计算语速调整
    rate = self._calc_rate(text, target_duration)

    try:
      # 使用 edge-tts 命令行工具（比 Python API 更稳定）
      os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

      cmd = [
        "edge-tts",
        "--voice", self.voice,
        "--rate", rate,
        "--text", text,
        "--write-media", output_path
      ]

      proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
      )
      stdout, stderr = await proc.communicate()

      if proc.returncode != 0:
        err_msg = stderr.decode() if stderr else "unknown error"
        logger.error(f"TTS 失败: {err_msg}")
        return 0.0

      # 获取音频时长（使用 ffprobe）
      duration = await self._get_duration(output_path)
      return duration

    except FileNotFoundError:
      logger.error("edge-tts 未安装，请执行: pip install edge-tts")
      return 0.0
    except Exception as e:
      logger.error(f"TTS 合成异常: {e}")
      return 0.0

  def _calc_rate(self, text: str, target_duration: float) -> str:
    """根据目标时长计算语速"""
    if target_duration <= 0:
      return "+0%"

    char_count = len(text)
    # 中文正常语速约 3.5 字/秒
    natural_duration = char_count / 3.5
    ratio = natural_duration / target_duration

    if ratio > 1.3:
      pct = min(int((ratio - 1) * 100), 50)
      return f"+{pct}%"
    elif ratio < 0.7:
      pct = min(int((1 - ratio) * 100), 50)
      return f"-{pct}%"
    return "+0%"

  async def _get_duration(self, file_path: str) -> float:
    """通过 ffprobe 获取音频时长"""
    try:
      proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        file_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
      )
      stdout, _ = await proc.communicate()
      if proc.returncode == 0:
        return float(stdout.decode().strip())
    except Exception:
      pass
    return 0.0
