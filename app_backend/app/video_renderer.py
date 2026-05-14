# app/video_renderer.py
import logging
import os
from typing import List, Dict

from PIL import Image, ImageDraw
from moviepy.editor import (
  ImageClip,
  TextClip,
  CompositeVideoClip,
  AudioFileClip,
  concatenate_videoclips,
  vfx,
)
from moviepy.video.VideoClip import VideoClip

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

  def __init__(
      self,
      output_width: int = 1080,
      output_height: int = 1920,
      fps: int = 24,
      font_size: int = 36,
      font_path: str | None = None
  ):
    self.output_width = output_width
    self.output_height = output_height
    self.fps = fps
    self.font_path = font_path or _find_font()
    self.font_size = font_size

  def render(
      self,
      scenes: List[Dict],
      page_image_paths: Dict[int, str],
      scene_audio_paths: Dict[int, str],
      output_path: str
  ) -> str:
    """
    渲染视频。

    :param scenes: AI 生成的场景脚本 [{scene_id, img_index, narration, focus_area, camera_action, duration}]
    :param page_image_paths: {img_index: local_image_path} 书页本地图片路径（key 是序号，从1开始）
    :param scene_audio_paths: {scene_id: audio_path} 每个场景的配音文件路径
    :param output_path: 输出 MP4 路径
    :return: output_path
    """
    clips = []
    font = self.font_path

    for i, scene in enumerate(scenes):
      img_index = scene.get("img_index", scene.get("page_no", 1))  # 兼容旧字段名
      narration = scene.get("narration", "")
      focus_area = scene.get("focus_area", [0.0, 0.0, 1.0, 1.0])
      camera_action = scene.get("camera_action", "Steady")
      duration = scene.get("duration", 5.0)
      scene_id = scene.get("scene_id", i + 1)

      img_path = page_image_paths.get(img_index)
      if not img_path or not os.path.exists(img_path):
        logger.warning(f"场景 {scene_id}: 图片序号 {img_index} 缺失，跳过")
        continue

      # 1. 创建带 Ken Burns 效果的书页剪辑
      page_clip = self._make_ken_burns_clip(
          img_path, focus_area, camera_action, duration
      )

      # 2. 添加焦点高亮叠加层
      highlight_clip = self._make_highlight_clip(focus_area, duration)
      page_clip = CompositeVideoClip([page_clip, highlight_clip])

      # 3. 添加字幕
      if narration:
        subtitle_clip = self._make_subtitle_clip(narration, duration, font)
        page_clip = CompositeVideoClip([page_clip, subtitle_clip])

      # 4. 添加配音
      audio_path = scene_audio_paths.get(scene_id)
      if audio_path and os.path.exists(audio_path):
        try:
          audio_clip = AudioFileClip(audio_path)
          if audio_clip.duration < duration:
            # 如果音频比目标时长短，循环末尾静音
            pass
          # 裁剪/拉伸音频以匹配场景时长
          audio_clip = audio_clip.with_duration(duration)
          page_clip = page_clip.with_audio(audio_clip)
        except Exception as e:
          logger.warning(f"场景 {scene_id}: 加载音频失败 {e}")

      # 5. 设置精确时长
      page_clip = page_clip.with_duration(duration)

      # 6. 添加淡入淡出转场（非首尾场景）
      if i > 0:
        page_clip = page_clip.with_effects([vfx.CrossFadeIn(0.3)])
      if i < len(scenes) - 1:
        page_clip = page_clip.with_effects([vfx.CrossFadeOut(0.3)])

      clips.append(page_clip)

    if not clips:
      raise ValueError("没有有效的场景可以渲染")

    # 拼接所有场景
    final = concatenate_videoclips(clips, method="compose")

    # 写入 MP4
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    final.write_videofile(
        output_path,
        fps=self.fps,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        bitrate="2000k",
        threads=4
    )

    # 清理
    final.close()
    for c in clips:
      c.close()

    return output_path

  def _make_ken_burns_clip(self, img_path: str, focus_area: List[float], action: str, duration: float) -> VideoClip:
    """
    根据运镜指令创建带 Ken Burns 效果的 ImageClip。
    focus_area: [x, y, w, h] 归一化坐标 (0~1)
    """
    import numpy as np

    # 预加载图片为 numpy 数组，避免 transform 内 get_frame 的循环引用
    pil_img = Image.open(img_path).convert("RGB")
    img_array = np.array(pil_img)
    img_h, img_w = img_array.shape[:2]

    fx, fy, fw, fh = focus_area
    focus_cx = fx + fw / 2
    focus_cy = fy + fh / 2

    if action == "ZoomIn":
      zoom_start, zoom_end = 1.0, 1.3
      pan_x = pan_y = 0
    elif action == "PanLeft":
      zoom_start = zoom_end = 1.15
      pan_x, pan_y = 0.15, 0
    elif action == "PanRight":
      zoom_start = zoom_end = 1.15
      pan_x, pan_y = -0.15, 0
    else:
      zoom_start, zoom_end = 1.0, 1.05
      pan_x = pan_y = 0

    out_w, out_h = self.output_width, self.output_height
    aspect = out_w / out_h

    def make_frame(t):
      progress = t / duration if duration > 0 else 0
      zoom = zoom_start + (zoom_end - zoom_start) * progress
      px = pan_x * progress
      py = pan_y * progress

      crop_w = img_w / zoom
      crop_h = crop_w / aspect
      if crop_h * zoom > img_h:
        crop_h = img_h / zoom
        crop_w = crop_h * aspect

      cx = focus_cx + px
      cy = focus_cy + py
      x1 = max(0, int(cx * img_w - crop_w / 2))
      y1 = max(0, int(cy * img_h - crop_h / 2))
      x2 = min(img_w, x1 + int(crop_w))
      y2 = min(img_h, y1 + int(crop_h))

      cropped = Image.fromarray(img_array).crop((x1, y1, x2, y2))
      resized = cropped.resize((out_w, out_h), Image.LANCZOS)
      return np.array(resized)

    return VideoClip(make_frame=make_frame, duration=duration)

  def _make_highlight_clip(self, focus_area: List[float], duration: float) -> VideoClip:
    """在焦点区域创建半透明高亮叠加层"""
    import numpy as np

    fx, fy, fw, fh = focus_area
    out_w, out_h = self.output_width, self.output_height

    # 预先渲染好这一帧（高亮框是静态的，不随时间变化），避免每帧重复计算
    overlay = np.zeros((out_h, out_w, 3), dtype=np.uint8)
    x1 = int(fx * out_w)
    y1 = int(fy * out_h)
    x2 = int((fx + fw) * out_w)
    y2 = int((fy + fh) * out_h)
    pil_img = Image.fromarray(overlay, "RGB")
    draw = ImageDraw.Draw(pil_img)
    draw.rectangle([x1, y1, x2, y2], outline=(255, 230, 100), width=3)
    static_frame = np.array(pil_img)

    def make_frame(t):
      return static_frame

    return VideoClip(make_frame=make_frame, duration=duration)

  def _make_subtitle_clip(self, text: str, duration: float, font_path: str) -> TextClip:
    """创建底部字幕"""
    try:
      return (
        TextClip(
            text=text,
            font=font_path,
            font_size=self.font_size,
            color="white",
            stroke_color="black",
            stroke_width=1.5,
            size=(int(self.output_width * 0.9), None),
            method="caption",
            horizontal_align="center",
        )
        .with_duration(duration)
        .with_position(("center", int(self.output_height * 0.88)))
      )
    except Exception as e:
      logger.warning(f"创建字幕失败: {e}")
      return TextClip(text="", font_size=1).with_duration(duration)