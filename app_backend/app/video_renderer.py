# app/video_renderer.py
import logging
import os
from typing import List, Dict

import numpy as np
from PIL import Image
# 配置 moviepy 使用 ImageMagick v7
from moviepy.config import change_settings
from moviepy.editor import (
  AudioFileClip,
  concatenate_videoclips,
  vfx,
)
from moviepy.video.VideoClip import VideoClip

change_settings({"IMAGEMAGICK_BINARY": "magick"})

logger = logging.getLogger(__name__)

# 字体查找路径（Linux 中文字体）
FONT_CANDIDATES = [
  "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
  "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
  "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
  "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
  "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
]


def _find_font() -> str:
  for path in FONT_CANDIDATES:
    if os.path.exists(path):
      return path
  return "Arial"


class VideoRenderer:
  """视频渲染引擎：将书页图片 + 运镜脚本 + 配音合成为 MP4"""

  def __init__(self, fps: int = 24):
    self.fps = fps
    self.output_width = 0
    self.output_height = 0

  def render(self, scenes: List[Dict], page_image_paths: Dict[int, str], scene_audio_paths: Dict[int, str], output_path: str) -> str:
    # 1. 以第一页图片确定视频分辨率
    first_img_idx = min(page_image_paths.keys())
    first_img_path = page_image_paths[first_img_idx]
    with Image.open(first_img_path) as img:
      raw_w, raw_h = img.size

    # 限制高度最高 1080，保证性能，同时等比例计算宽度
    max_h = 1080
    scale = max_h / raw_h if raw_h > max_h else 1.0
    self.output_width = int(raw_w * scale)
    self.output_height = int(raw_h * scale)

    # 必须是偶数
    if self.output_width % 2 != 0:
      self.output_width -= 1
    if self.output_height % 2 != 0:
      self.output_height -= 1

    logger.info(f"视频自适应尺寸: {self.output_width}x{self.output_height}")

    clips = []
    for i, scene in enumerate(scenes):
      img_index = scene.get("img_index", 1)
      scene_id = scene.get("scene_id", i + 1)
      img_path = page_image_paths.get(img_index, first_img_path)

      # 获取配音
      audio_path = scene_audio_paths.get(scene_id)
      audio_clip = None
      if audio_path and os.path.exists(audio_path):
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
      else:
        duration = scene.get("duration", 5.0)

      # 2. 创建静态书页 Clip
      page_clip = self._make_static_clip(img_path, duration)

      if audio_clip:
        page_clip = page_clip.set_audio(audio_clip)

      # 3. 淡入淡出转场
      if i > 0:
        page_clip = page_clip.fx(vfx.fadein, 0.3)

      clips.append(page_clip)

    # 拼接并输出
    final = concatenate_videoclips(clips, method="compose")
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    final.write_videofile(
        output_path,
        fps=self.fps,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        bitrate="2048k",
        threads=4
    )
    final.close()
    return output_path

  def _make_static_clip(self, img_path: str, duration: float) -> VideoClip:
    """等比例缩放至视频尺寸，无动态效果"""
    pil_img = Image.open(img_path).convert("RGB")
    resized_img = pil_img.resize((self.output_width, self.output_height), Image.LANCZOS)
    frame_array = np.array(resized_img)
    return VideoClip(make_frame=lambda t: frame_array, duration=duration)

  # def _make_ken_burns_clip(self, img_path: str, duration: float) -> VideoClip:
  #   """
  #   现在这个方法只需将图片缩放到确定的视频尺寸即可。
  #   由于视频尺寸是根据图片定的，这里几乎是完美的 1:1。
  #   """
  #   pil_img = Image.open(img_path).convert("RGB")
  #
  #   # 将图片缩放到 render 方法中确定的统一视频尺寸
  #   # （防止后续页面和第一页尺寸微小不一致导致黑边）
  #   resized_img = pil_img.resize((self.output_width, self.output_height), Image.LANCZOS)
  #   frame_array = np.array(resized_img)
  #
  #   return VideoClip(make_frame=lambda t: frame_array, duration=duration)
  #
  # def _make_highlight_clip(self, focus_area: List[float], duration: float) -> VideoClip:
  #   """
  #   在焦点区域创建高亮效果：焦点外半透明暗化 + 醒目黄色边框。
  #
  #   修复说明：
  #   MoviePy 的 CompositeVideoClip 只能将两个 RGB (H,W,3) 帧叠加。
  #   原实现直接把 RGBA (H,W,4) 数组作为帧返回，导致 blit_on 试图把
  #   shape (H,W,4) 广播到 shape (H,W,3) 时抛出 ValueError。
  #
  #   正确做法：VideoClip 只返回 RGB 帧，透明度信息通过独立的 mask clip
  #   （灰度 0~1 浮点帧）传递，再用 clip.set_mask() 绑定。
  #   MoviePy 合成时会自动用 mask 做 alpha blending，不再有通道数冲突。
  #   """
  #   fx, fy, fw, fh = focus_area
  #   out_w, out_h = self.output_width, self.output_height
  #
  #   # ── 1. 准备 RGB 颜色帧（纯黑，颜色由 mask 决定可见度）──────────────
  #   rgb_frame = np.zeros((out_h, out_w, 3), dtype=np.uint8)  # 全黑 RGB
  #
  #   # ── 2. 准备 mask 帧（0.0 = 完全透明, 1.0 = 完全不透明）──────────────
  #   # 焦点区域外：alpha ≈ 0.31（80/255），即半透明暗化
  #   # 焦点区域内：alpha = 0（完全透明，让底层画面完全穿透）
  #   mask_frame = np.full((out_h, out_w), 80 / 255.0, dtype=np.float32)
  #
  #   x1 = max(0, int(fx * out_w))
  #   y1 = max(0, int(fy * out_h))
  #   x2 = min(out_w, int((fx + fw) * out_w))
  #   y2 = min(out_h, int((fy + fh) * out_h))
  #
  #   mask_frame[y1:y2, x1:x2] = 0.0  # 焦点区域完全透明
  #
  #   # ── 3. 在 mask 上画边框（边框本身是不透明的）────────────────────────
  #   # 用 PIL 在 mask 上画矩形，外层发光 + 内层主边框
  #   mask_pil = Image.fromarray((mask_frame * 255).astype(np.uint8), "L")
  #   draw = ImageDraw.Draw(mask_pil)
  #   draw.rectangle([x1 - 2, y1 - 2, x2 + 2, y2 + 2], outline=200, width=8)  # 外层发光
  #   draw.rectangle([x1, y1, x2, y2], outline=255, width=5)  # 内层主边框
  #   mask_frame = np.array(mask_pil).astype(np.float32) / 255.0
  #
  #   # ── 4. 用黄色覆盖边框像素对应的 RGB 颜色帧 ──────────────────────────
  #   # 创建一张黄色图层，仅在边框区域（mask 不为 0）生效
  #   color_pil = Image.fromarray(rgb_frame)
  #   color_draw = ImageDraw.Draw(color_pil)
  #   color_draw.rectangle([x1 - 2, y1 - 2, x2 + 2, y2 + 2], outline=(255, 255, 150), width=8)  # 外层：浅黄
  #   color_draw.rectangle([x1, y1, x2, y2], outline=(255, 220, 0), width=5)  # 内层：亮黄
  #   rgb_frame = np.array(color_pil)
  #
  #   # ── 5. 构建 VideoClip（RGB）+ mask clip（灰度）────────────────────────
  #   def make_frame(_t):
  #     return rgb_frame
  #
  #   def make_mask_frame(_t):
  #     return mask_frame
  #
  #   color_clip = VideoClip(make_frame=make_frame, duration=duration, ismask=False)
  #
  #   mask_clip = VideoClip(make_frame=make_mask_frame, duration=duration, ismask=True)
  #
  #   return color_clip.set_mask(mask_clip)
  #
  # def _make_subtitle_clip(self, text: str, duration: float, font_path: str) -> VideoClip:
  #   """创建底部字幕，带半透明背景"""
  #   try:
  #     # 字幕文字
  #     text_clip = TextClip(
  #         txt=text,
  #         font=font_path,
  #         fontsize=int(self.font_size * 1.2),  # 字号放大 20%
  #         color="white",
  #         stroke_color="black",
  #         stroke_width=2.5,  # 加粗描边
  #         size=(int(self.output_width * 0.9), None),
  #         method="caption",
  #         align="center",
  #     )
  #
  #     # 创建半透明黑色背景
  #     from moviepy.editor import ColorClip
  #     text_w, text_h = text_clip.size
  #     bg_clip = ColorClip(
  #         size=(self.output_width, text_h + 40),  # 上下各留 20px 边距
  #         color=(0, 0, 0)
  #     ).set_opacity(0.7)
  #
  #     # 将文字叠加到背景上
  #     text_clip = text_clip.set_position(("center", 20))
  #     subtitle = CompositeVideoClip([bg_clip, text_clip], size=(self.output_width, text_h + 40))
  #
  #     # 设置位置和时长
  #     subtitle = subtitle.set_position(("center", int(self.output_height * 0.85)))
  #     subtitle = subtitle.set_duration(duration)
  #     return subtitle
  #
  #   except Exception as e:
  #     logger.warning(f"创建字幕失败: {e}")
  #     # 返回一个透明的占位 clip
  #     from moviepy.editor import ColorClip
  #     return ColorClip(size=(1, 1), color=(0, 0, 0), duration=duration).set_opacity(0)
