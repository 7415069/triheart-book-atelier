# app/video_renderer.py
import logging
import os
from typing import List, Dict

import numpy as np
from PIL import Image, ImageDraw
# 配置 moviepy 使用 ImageMagick v7
from moviepy.config import change_settings
from moviepy.editor import (
  TextClip,
  CompositeVideoClip,
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
    :param page_image_paths: {img_index: local_image_path} 书页本地图片路径（key 是连续序号，从1开始）
    :param scene_audio_paths: {scene_id: audio_path} 每个场景的配音文件路径
    :param output_path: 输出 MP4 路径
    :return: output_path
    """
    clips = []
    font = self.font_path

    # 诊断日志：打印可用的图片序号
    available_indices = sorted(page_image_paths.keys())
    logger.info(f"可用图片序号: {available_indices}")
    logger.info(f"总场景数: {len(scenes)}")

    if not available_indices:
      raise ValueError("没有可用的书页图片")

    # 创建一个默认图片（当 AI 返回的索引找不到时使用）
    fallback_img_index = available_indices[0]

    for i, scene in enumerate(scenes):
      img_index = scene.get("img_index", scene.get("page_no", 1))  # 兼容旧字段名
      narration = scene.get("narration", "")
      focus_area = scene.get("focus_area", [0.0, 0.0, 1.0, 1.0])
      camera_action = scene.get("camera_action", "Steady")
      duration = scene.get("duration", 5.0)
      scene_id = scene.get("scene_id", i + 1)

      img_path = page_image_paths.get(img_index)

      # 如果指定的 img_index 不存在，尝试使用 fallback
      if not img_path or not os.path.exists(img_path):
        logger.warning(f"场景 {scene_id}: img_index={img_index} 不存在，尝试使用 fallback={fallback_img_index}")
        img_index = fallback_img_index
        img_path = page_image_paths.get(img_index)

      if not img_path or not os.path.exists(img_path):
        logger.error(f"场景 {scene_id}: 无法找到任何可用图片，跳过（可用序号: {available_indices}）")
        continue

      logger.info(f"场景 {scene_id}: 使用图片 {img_index} ({img_path})")

      # 1. 创建带 Ken Burns 效果的书页剪辑
      page_clip = self._make_ken_burns_clip(
          img_path, focus_area, camera_action, duration
      )

      # 3. 添加配音（字幕、高亮框均已去除，画面保持干净）
      audio_path = scene_audio_paths.get(scene_id)
      if audio_path and os.path.exists(audio_path):
        try:
          audio_clip = AudioFileClip(audio_path)
          actual_audio_duration = audio_clip.duration

          # 如果音频比目标时长短，在末尾补静音
          if actual_audio_duration < duration:
            from moviepy.editor import AudioClip
            silence_duration = duration - actual_audio_duration
            silence = AudioClip(lambda t: [0, 0], duration=silence_duration, fps=audio_clip.fps)
            from moviepy.editor import concatenate_audioclips
            audio_clip = concatenate_audioclips([audio_clip, silence])
          elif actual_audio_duration > duration:
            # 如果音频比目标时长长，裁剪到目标时长
            audio_clip = audio_clip.subclip(0, duration)

          page_clip = page_clip.set_audio(audio_clip)
        except Exception as e:
          logger.warning(f"场景 {scene_id}: 加载音频失败 {e}")

      # 5. 设置精确时长
      page_clip = page_clip.set_duration(duration)

      # 6. 添加淡入淡出转场（非首尾场景）
      if i > 0:
        page_clip = page_clip.fx(vfx.fadein, 0.3)
      if i < len(scenes) - 1:
        page_clip = page_clip.fx(vfx.fadeout, 0.3)

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
    修改版：禁用了动态缩放，使画面保持静止
    """
    # 预加载图片
    pil_img = Image.open(img_path).convert("RGB")
    img_array = np.array(pil_img)
    img_h, img_w = img_array.shape[:2]

    fx, fy, fw, fh = focus_area
    focus_cx = fx + fw / 2
    focus_cy = fy + fh / 2

    # --- 修改核心逻辑开始 ---
    # 将所有动作的 zoom_start 和 zoom_end 设为一致，即可消除“慢慢放大”的动画
    if action == "ZoomIn":
      # 如果 AI 要求放大，我们直接显示放大后的静态画面（例如固定 1.3 倍），不再有“过程”
      zoom_start = zoom_end = 1.0
      pan_x = pan_y = 0
    elif action == "PanLeft":
      zoom_start = zoom_end = 1.0
      pan_x, pan_y = 0.2, 0  # 这里 pan_x 也可以设为固定值，如果不想要平移的话设为 0
    elif action == "PanRight":
      zoom_start = zoom_end = 1.0
      pan_x, pan_y = -0.2, 0
    else:  # Steady 模式
      # 彻底静止：起始和结束缩放倍率都设为 1.0
      zoom_start = zoom_end = 1.0
      pan_x = pan_y = 0
    # --- 修改核心逻辑结束 ---

    out_w, out_h = self.output_width, self.output_height
    aspect = out_w / out_h

    def make_frame(t):
      # 因为 zoom_start == zoom_end，这里的 progress 不再影响缩放倍率
      progress = t / duration if duration > 0 else 0
      zoom = zoom_start  # 变成固定值

      # 如果你连左右平移也不想要，可以把 px, py 直接设为 0
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
    """
    在焦点区域创建高亮效果：焦点外半透明暗化 + 醒目黄色边框。

    修复说明：
    MoviePy 的 CompositeVideoClip 只能将两个 RGB (H,W,3) 帧叠加。
    原实现直接把 RGBA (H,W,4) 数组作为帧返回，导致 blit_on 试图把
    shape (H,W,4) 广播到 shape (H,W,3) 时抛出 ValueError。

    正确做法：VideoClip 只返回 RGB 帧，透明度信息通过独立的 mask clip
    （灰度 0~1 浮点帧）传递，再用 clip.set_mask() 绑定。
    MoviePy 合成时会自动用 mask 做 alpha blending，不再有通道数冲突。
    """
    fx, fy, fw, fh = focus_area
    out_w, out_h = self.output_width, self.output_height

    # ── 1. 准备 RGB 颜色帧（纯黑，颜色由 mask 决定可见度）──────────────
    rgb_frame = np.zeros((out_h, out_w, 3), dtype=np.uint8)  # 全黑 RGB

    # ── 2. 准备 mask 帧（0.0 = 完全透明, 1.0 = 完全不透明）──────────────
    # 焦点区域外：alpha ≈ 0.31（80/255），即半透明暗化
    # 焦点区域内：alpha = 0（完全透明，让底层画面完全穿透）
    mask_frame = np.full((out_h, out_w), 80 / 255.0, dtype=np.float32)

    x1 = max(0, int(fx * out_w))
    y1 = max(0, int(fy * out_h))
    x2 = min(out_w, int((fx + fw) * out_w))
    y2 = min(out_h, int((fy + fh) * out_h))

    mask_frame[y1:y2, x1:x2] = 0.0  # 焦点区域完全透明

    # ── 3. 在 mask 上画边框（边框本身是不透明的）────────────────────────
    # 用 PIL 在 mask 上画矩形，外层发光 + 内层主边框
    mask_pil = Image.fromarray((mask_frame * 255).astype(np.uint8), "L")
    draw = ImageDraw.Draw(mask_pil)
    draw.rectangle([x1 - 2, y1 - 2, x2 + 2, y2 + 2], outline=200, width=8)  # 外层发光
    draw.rectangle([x1, y1, x2, y2], outline=255, width=5)  # 内层主边框
    mask_frame = np.array(mask_pil).astype(np.float32) / 255.0

    # ── 4. 用黄色覆盖边框像素对应的 RGB 颜色帧 ──────────────────────────
    # 创建一张黄色图层，仅在边框区域（mask 不为 0）生效
    color_pil = Image.fromarray(rgb_frame)
    color_draw = ImageDraw.Draw(color_pil)
    color_draw.rectangle([x1 - 2, y1 - 2, x2 + 2, y2 + 2],
                         outline=(255, 255, 150), width=8)  # 外层：浅黄
    color_draw.rectangle([x1, y1, x2, y2],
                         outline=(255, 220, 0), width=5)  # 内层：亮黄
    rgb_frame = np.array(color_pil)

    # ── 5. 构建 VideoClip（RGB）+ mask clip（灰度）────────────────────────
    def make_frame(_t):
      return rgb_frame

    def make_mask_frame(_t):
      return mask_frame

    color_clip = VideoClip(make_frame=make_frame, duration=duration, ismask=False)

    mask_clip = VideoClip(make_frame=make_mask_frame, duration=duration, ismask=True)

    return color_clip.set_mask(mask_clip)

  def _make_subtitle_clip(self, text: str, duration: float, font_path: str) -> VideoClip:
    """创建底部字幕，带半透明背景"""
    try:
      # 字幕文字
      text_clip = TextClip(
          txt=text,
          font=font_path,
          fontsize=int(self.font_size * 1.2),  # 字号放大 20%
          color="white",
          stroke_color="black",
          stroke_width=2.5,  # 加粗描边
          size=(int(self.output_width * 0.9), None),
          method="caption",
          align="center",
      )

      # 创建半透明黑色背景
      from moviepy.editor import ColorClip
      text_w, text_h = text_clip.size
      bg_clip = ColorClip(
          size=(self.output_width, text_h + 40),  # 上下各留 20px 边距
          color=(0, 0, 0)
      ).set_opacity(0.7)

      # 将文字叠加到背景上
      text_clip = text_clip.set_position(("center", 20))
      subtitle = CompositeVideoClip([bg_clip, text_clip], size=(self.output_width, text_h + 40))

      # 设置位置和时长
      subtitle = subtitle.set_position(("center", int(self.output_height * 0.85)))
      subtitle = subtitle.set_duration(duration)
      return subtitle

    except Exception as e:
      logger.warning(f"创建字幕失败: {e}")
      # 返回一个透明的占位 clip
      from moviepy.editor import ColorClip
      return ColorClip(size=(1, 1), color=(0, 0, 0), duration=duration).set_opacity(0)
