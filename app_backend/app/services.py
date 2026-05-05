# /app/services.py
import asyncio
import base64
import json
import os
import re
import uuid
from hashlib import md5
from time import time
from typing import List, Tuple, Callable, Dict, Any, Sequence, Generic

import httpx
from brtech_backend.core import database
# 引入后端核心依赖
from brtech_backend.core.config import app_settings
from brtech_backend.core.models import M
from brtech_backend.core.schemas import UniqueConstraint
from brtech_backend.core.services import StringPKeyRecurseService, StringPKeyService, Service
from brtech_backend.dictionary.services import StringPKeyWithDictionaryService
from brtech_backend.payment.handler import PaymentDispatcher, PaymentServiceMixin
from brtech_backend.payment.models import PayOrderModel
from brtech_backend.task.services import task_manager
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from .ai_helper import AiHelper
from .config import thba_app_settings
# 引入本项目依赖
from .crud import TriHeartPageCrud, TriHeartBookCrud, TriHeartChapterCrud, TriHeartChapterPageCrud, TriHeartBookNoteCrud, TriHeartBookUserCrud, TriHeartTermCrud, TriHeartPageTermCrud, TriHeartPageAttachmentCrud
from .models import TriHeartPageModel, TriHeartBookModel, TriHeartChapterModel, TriHeartChapterPageModel, TriHeartBookUserModel, TriHeartBookNoteModel, TriHeartPageTermModel, TriHeartTermModel, TriHeartPageAttachmentModel
from .pdf_helper import PdfStructure, PdfPage, PdfHelper
from .schemas import TriHeartPageQuery, TriHeartBookQuery, TriHeartChapterQuery, TriHeartChapterPageQuery, TriHeartBookUserQuery, TriHeartBookNoteQuery, TriHeartTermQuery, TriHeartPageTermQuery, TriHeartPageAttachmentQuery

# =========================================================
# 配置部分
# =========================================================
# class StorageConfig:
#   ROOT_DIR = "uploads/webp"
#   DB_PREFIX = "upload/books"


# 状态常量
PROC_PENDING = "0"
PROC_PROCESSING = "1"
PROC_SUCCESS = "2"
PROC_FAILED = "9"


# =========================================================
# 1. 外部 Wrapper
# =========================================================
async def run_pdf_task_wrapper(user_id: str, book_id: str, task_id: str):
  """
  后台任务入口。
  负责管理 DB Session 的生命周期，并启动 Service。
  """
  session_maker = database.get_session_maker()
  async with session_maker() as new_db:
    service = TriHeartBookService(new_db)
    await service.process_pdf_logic(user_id, book_id, task_id)


async def run_extract_terms_task(user_id: str, book_id: str, from_page: int, to_page: int, task_id: str):
  """AI 提取任务 Wrapper"""
  session_maker = database.get_session_maker()
  async with session_maker() as new_db:
    service = TriHeartBookService(new_db)
    await service.ai_extraction_logic(user_id, book_id, from_page, to_page)


async def run_scan_coords_task(user_id: str, book_id: str, task_id: str):
  """坐标扫描任务 Wrapper"""
  session_maker = database.get_session_maker()
  async with session_maker() as new_db:
    service = TriHeartBookService(new_db)
    await service.scan_coordinates_logic(user_id, book_id)


async def cdn_sign_url(service: Service, user_id, raw_path: str) -> str:
  if thba_app_settings.CDN_OSS_ENABLE:
    secret_key = thba_app_settings.CDN_OSS_SECRET_KEY
    full_path = f"/{thba_app_settings.OSS_BUCKET_NAME}/{raw_path}"
    path = re.sub(r'/+', '/', full_path)
    extra_params = {}
    if thba_app_settings.CDN_OSS_PROVIDER == "Gcore":
      ttl = 3600  # TTL of URL (in sec)
      expires = int(time()) + ttl  # Token generation
      token_hash = md5(f"{expires}{path} {secret_key}".encode()).digest()
      token = base64.b64encode(token_hash).decode().replace("\n", "").replace("+", "-").replace("/", "_").replace("=", "")
      extra_params = {"md5": token, "expires": str(expires)}
    if thba_app_settings.CDN_OSS_PROVIDER == "EdgeOne":
      timestamp = str(int(time()))
      rand = str(uuid.uuid4().hex[:8])
      uid = str(user_id) if user_id else "0"
      hash_str = f"{path}-{timestamp}-{rand}-{uid}-{secret_key}"
      token_hash = md5(hash_str.encode('utf-8')).hexdigest()
      token = f"{timestamp}-{rand}-{uid}-{token_hash}"
      extra_params = {"md5": token}
    raw_sign_url = await service.get_oss_download_sign_url(user_id, raw_path, "", extra_params)
    return raw_sign_url.replace(thba_app_settings.OSS_ENDPOINT, thba_app_settings.CDN_OSS_ENDPOINT)
  else:
    return await service.get_oss_download_sign_url(user_id, raw_path, "")


# =========================================================
# 2. PDF 解析工具类 (CPU 密集型逻辑)
# =========================================================
class PdfProcessor:

  @staticmethod
  def _ensure_dir(path: str):
    if not os.path.exists(path):
      os.makedirs(path)

  @staticmethod
  def execute(pdf_path: str, webp_home: str, progress_callback: Callable[[int, int, str], None] = None) -> Tuple[bool, str, List[PdfPage], List[PdfStructure]]:
    """
    开始解析。
    请确保在调用前已设置 self.webp_home, self.padding 等属性。
    """
    # 物理路径用于保存文件

    # 移除开头的 / 以适配相对路径
    pdf_path: str = pdf_path.lstrip("/")
    webp_home = webp_home.lstrip("/")
    PdfProcessor._ensure_dir(webp_home)

    pdf_helper = PdfHelper(pdf_path=pdf_path, webp_home=webp_home, progress_callback=progress_callback)
    return pdf_helper.parse()


# =========================================================
# 3. 各业务 Service
# =========================================================

class TriHeartChapterService(StringPKeyRecurseService[TriHeartChapterModel, TriHeartChapterCrud, TriHeartChapterQuery]):

  async def remove_by_book_id(self, user_id: str, book_id: str, commit: bool = True) -> int:
    """根据 BookID 清理旧章节"""
    rtn_val: int = 0
    try:
      rtn_val = await self.get_crud().remove_by_book_id(book_id)
      if commit:
        await self.get_crud().commit()
    except Exception as e:
      if commit:
        await self.get_crud().rollback()
        raise e
    return rtn_val


class TriHeartPageService(StringPKeyService[TriHeartPageModel, TriHeartPageCrud, TriHeartPageQuery]):

  def get_crud(self) -> TriHeartPageCrud:
    return super().get_crud()

  async def remove_by_book_id(self, user_id: str, book_id: str, commit: bool = True) -> int:
    rtn_val: int = 0
    try:
      rtn_val = await self.get_crud().remove_by_book_id(book_id)
      if commit:
        await self.get_crud().commit()
    except Exception as e:
      if commit:
        await self.get_crud().rollback()
        raise e
    return rtn_val

  async def remove_by_chapter_id(self, user_id: str, chapter_id: str, commit: bool = True) -> int:
    rtn_val: int = 0
    try:
      rtn_val = await self.get_crud().remove_by_chapter_id(chapter_id)
      if commit:
        await self.get_crud().commit()
    except Exception as e:
      if commit:
        await self.get_crud().rollback()
        raise e
    return rtn_val

  async def get_webp_url(self, user_id: str | None, book_id: str, page_no: int, webp_type: str) -> str:
    """根据 BookID 和 PageNo 获取 Webp URL"""
    # 1. 数据库单次查询获取所有鉴权信息
    row = await self.get_crud().custom_query_book_user_page(book_id, user_id, page_no)

    if not row:
      raise HTTPException(status_code=404, detail="请求的页面资源不存在")

    # 2. 鉴权逻辑
    is_allowed = False

    # row 字段: 0:path, 1:crop_path, 2:guest_limit, 3:user_limit, 4:purchase_status

    # 优先级 1: 已购买 (purchase_status == '1') -> 允许
    if row.purchase_status == '1':
      is_allowed = True

    # 优先级 2: 已登录 (user_id 存在) -> 使用 user_preview_limit
    elif user_id:
      if page_no <= row.user_preview_limit:
        is_allowed = True

    # 优先级 3: 匿名 (user_id 为空) -> 使用 guest_preview_limit
    else:
      if page_no <= row.guest_preview_limit:
        is_allowed = True

    if not is_allowed:
      raise HTTPException(status_code=403, detail="超出试读范围，请购买后继续阅读")

    # 3. 资源路径处理
    target_path = row.page_image_crop_path if webp_type == 'crop' else row.page_image_path

    # 容错：如果 crop 路径为空，回退到原图
    if webp_type == 'crop' and not target_path:
      target_path = row.page_image_path

    if not target_path:
      raise HTTPException(status_code=404, detail="图片资源缺失")

    sign_url = await cdn_sign_url(self, user_id, target_path)
    # if thba_app_settings.CDN_OSS_ENABLE:
    #   secret_key = thba_app_settings.CDN_OSS_SECRET_KEY
    #   raw_path = f"/{thba_app_settings.OSS_BUCKET_NAME}/{target_path}"
    #   path = re.sub(r'/+', '/', raw_path)
    #   extra_params = {}
    #   if thba_app_settings.CDN_OSS_PROVIDER == "Gcore":
    #     ttl = 3600  # TTL of URL (in sec)
    #     expires = int(time()) + ttl  # Token generation
    #     token_hash = md5(f"{expires}{path} {secret_key}".encode()).digest()
    #     token = base64.b64encode(token_hash).decode().replace("\n", "").replace("+", "-").replace("/", "_").replace("=", "")
    #     extra_params = {"md5": token, "expires": str(expires)}
    #   if thba_app_settings.CDN_OSS_PROVIDER == "EdgeOne":
    #     timestamp = str(int(time()))
    #     rand = "33"
    #     uid = "55"
    #     hash_str = f"{path}-{timestamp}-{rand}-{uid}-{secret_key}"
    #     token = md5(hash_str.encode('utf-8')).hexdigest()
    #     extra_params = {"md5": token}
    #   raw_sign_url = await self.get_oss_download_sign_url(user_id, target_path, "", extra_params)
    #   sign_url = raw_sign_url.replace(thba_app_settings.OSS_ENDPOINT, thba_app_settings.CDN_OSS_ENDPOINT)
    # else:
    #   sign_url = await self.get_oss_download_sign_url(user_id, target_path, "")
    # https://minio.brtech.top/thba/681186536234029056/2026/0417/TriHeartBookModel-700345638113644544/webp/original/1.webp?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=CcLG5FcYksvDUE6oca1e%2F20260422%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260422T110341Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=ae51a62fe4909f6ec44052ee90bb6fb2a39e6e12ce6b5b8621b05a20a3510036

    return sign_url


# [新增] 章节与书页关联表 Service
class TriHeartChapterPageService(StringPKeyService[TriHeartChapterPageModel, TriHeartChapterPageCrud, TriHeartChapterPageQuery]):
  pass


class TriHeartBookService(StringPKeyWithDictionaryService[TriHeartBookModel, TriHeartBookCrud, TriHeartBookQuery]):

  async def get_cover_sign_url(self, user_id: str, book_id: str) -> str:
    book: TriHeartBookModel | None = await self.get(user_id, book_id)
    sign_url: str = ""
    if book:
      sign_url = await cdn_sign_url(self, user_id, book.book_cover)
      # if thba_app_settings.CDN_OSS_ENABLE:
      #   secret_key = thba_app_settings.CDN_OSS_SECRET_KEY
      #   raw_path = f"/{thba_app_settings.OSS_BUCKET_NAME}/{book.book_cover}"
      #   path = re.sub(r'/+', '/', raw_path)
      #   extra_params = {}
      #   if thba_app_settings.CDN_OSS_PROVIDER == "Gcore":
      #     ttl = 3600  # TTL of URL (in sec)
      #     expires = int(time()) + ttl  # Token generation
      #     token_hash = md5(f"{expires}{path} {secret_key}".encode()).digest()
      #     token = base64.b64encode(token_hash).decode().replace("\n", "").replace("+", "-").replace("/", "_").replace("=", "")
      #     extra_params = {"md5": token, "expires": str(expires)}
      #   if thba_app_settings.CDN_OSS_PROVIDER == "EdgeOne":
      #     timestamp = str(int(time()))
      #     rand = "33"
      #     uid = "55"
      #     hash_str = f"{path}-{timestamp}-{rand}-{uid}-{secret_key}"
      #     token = md5(hash_str.encode('utf-8')).hexdigest()
      #     extra_params = {"md5": token}
      #   raw_sign_url = await self.get_oss_download_sign_url(user_id, book.book_cover, "", extra_params)
      #   sign_url = raw_sign_url.replace(thba_app_settings.OSS_ENDPOINT, thba_app_settings.CDN_OSS_ENDPOINT)
      # else:
      #   sign_url = await self.get_oss_download_sign_url(user_id, book.book_cover, "")
    return sign_url

  async def pre_create(self, user_id: str, model: TriHeartBookModel) -> None:
    await super().pre_create(user_id, model)
    model.owner_id = user_id
    model.process_status = PROC_PENDING
    if not model.book_status:
      model.book_status = "3"

  # async def post_create(self, user_id: str, model: TriHeartBookModel) -> None:
  #   await super().post_create(user_id, model)
  #   if model.book_pdf_path:
  #     # 调度外部 Wrapper
  #     asyncio.create_task(run_pdf_task_wrapper(user_id, model.model_id))

  async def pre_update(self, user_id: str, old_model: TriHeartBookModel, new_model: TriHeartBookModel, update_fields: set[str]) -> None:
    await super().pre_update(user_id, old_model, new_model, update_fields)
    if "book_pdf_path" in update_fields and not new_model.book_pdf_path:
      new_model.book_pdf_path = old_model.book_pdf_path
    if "book_pdf_path" in update_fields and new_model.book_pdf_path and new_model.book_pdf_path != old_model.book_pdf_path:
      old_model.process_status = PROC_PENDING

  async def de_identification(self, user_id: str | None, models: Sequence[TriHeartBookModel]) -> None:
    await super().de_identification(user_id, models)
    if models:
      for model in models:
        # 681186536234029056/2026/0417/TriHeartBookModel-700345638113644544/智能体修行青铜到王者的无品功法.pdf
        model.book_pdf_path = ""

  # async def post_update(self, user_id: str, old_model: TriHeartBookModel, new_model: TriHeartBookModel, update_fields: set[str]) -> None:
  #   await super().post_update(user_id, old_model, new_model, update_fields)
  #   # 仅当 PDF 路径变更时触发
  #   if "book_pdf_path" in update_fields and new_model.book_pdf_path and new_model.book_pdf_path != old_model.book_pdf_path:
  #     asyncio.create_task(run_pdf_task_wrapper(user_id, old_model.model_id))

  async def process_pdf_logic(self, user_id: str, book_id: str, task_id: str):
    chapter_service = TriHeartChapterService(self.db)
    page_service = TriHeartPageService(self.db)
    # [新增] 关联表服务
    cp_service = TriHeartChapterPageService(self.db)

    # 1. 获取书籍
    book = await self.get(user_id, book_id)
    if not book or not book.book_pdf_path:
      self.logger.warning(f"书籍 {book_id} 不存在或者没有 PDF 路径")
      return

    try:
      # 2. 更新状态为处理中
      book.process_status = PROC_PROCESSING
      await self.update(user_id, book, commit=True)  # 立即提交状态更新

      self.logger.info(f"Task Start: {book.book_title} ({book_id})")

      loop = asyncio.get_event_loop()

      def _progress_notify_handler(current, total, msg):
        if current % 10 == 0 or current == total:
          percent = int(current / total * 100)
          self.logger.info(f"[{percent}%] {msg}")
          if task_id:
            asyncio.run_coroutine_threadsafe(task_manager.update_progress(task_id, percent, msg), loop)

      var_prefix = "var/"
      pdf_path = f"{var_prefix}{book.book_pdf_path}"

      if not os.path.exists(pdf_path):
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        pdf_signed_url = await self.get_oss_download_sign_url(user_id, book.book_pdf_path)

        self.logger.info(f"Downloading PDF from OSS to {pdf_path}...")

        try:
          async with httpx.AsyncClient() as client:
            # 使用 stream 模式，避免大文件爆内存
            async with client.stream("GET", pdf_signed_url) as response:
              response.raise_for_status()  # 如果状态码不是 2xx 则抛出异常

              # 以二进制写模式打开本地文件
              with open(pdf_path, "wb") as f:
                # 异步迭代数据块写入
                async for chunk in response.aiter_bytes(chunk_size=8192):
                  f.write(chunk)

          self.logger.info("PDF Download successful.")
        except Exception as download_err:
          self.logger.error(f"Download failed: {download_err}")
          # 下载失败时，建议删除可能损坏的半成品文件
          if os.path.exists(pdf_path):
            os.remove(pdf_path)
          raise download_err

      webp_home = f"{os.path.dirname(pdf_path)}/webp"

      # 3. 执行 CPU 密集型解析
      success, msg, pages_data, chapters_data = await run_in_threadpool(PdfProcessor.execute, pdf_path=pdf_path, webp_home=webp_home, progress_callback=_progress_notify_handler)

      if success:
        # =======================================================
        # 开启数据库事务流程 (利用 commit=False)
        # =======================================================

        # 4.1 清理旧数据 (Commit=False)
        await chapter_service.remove_by_book_id(user_id, book_id, commit=False)
        await page_service.remove_by_book_id(user_id, book_id, commit=False)

        # 4.2 处理章节 (Chapter)
        _flat_triheart_chapter_models: list[TriHeartChapterModel] = []

        def _convert_to_triheart_chapter(pdf_structure: PdfStructure) -> TriHeartChapterModel:
          # 创建当前章节对象
          rtn_val: TriHeartChapterModel = TriHeartChapterModel(
              book_id=book_id,
              chapter_title=pdf_structure.title,
              from_page_no=pdf_structure.begin_page_no,
              to_page_no=pdf_structure.end_page_no
          )
          # 收集到扁平列表，供后续生成关联关系使用
          _flat_triheart_chapter_models.append(rtn_val)

          # 递归处理子章节
          _children: list[PdfStructure] = pdf_structure.children
          if _children:
            for child in _children:
              _child: TriHeartChapterModel = _convert_to_triheart_chapter(child)
              if rtn_val.children is None:
                rtn_val.children = []
              rtn_val.children.append(_child)
          return rtn_val

        triheart_chapter_models: list[TriHeartChapterModel] = []
        for chapter_data in chapters_data:
          triheart_chapter_model: TriHeartChapterModel = _convert_to_triheart_chapter(chapter_data)
          triheart_chapter_models.append(triheart_chapter_model)

        # 批量入库章节 (commit=False)
        await chapter_service.create_batch(user_id, triheart_chapter_models, commit=False)

        # 4.3 批量入库书页 (Pages) & 上传图片到 OSS
        triheart_page_models: list[TriHeartPageModel] = []

        # 初始化 HTTP Client 用于上传，避免循环内重复创建连接
        async with httpx.AsyncClient() as oss_client:

          # 定义内部上传函数
          async def _upload_image(local_path: str, object_key: str):
            if not os.path.exists(local_path):
              return
            try:
              content_type: str = "image/webp"
              upload_sign_url: dict[str, Any] = await self.get_oss_upload_sign_url(user_id, object_key, content_type=content_type)
              # 读取文件并上传 (WebP 图片一般较小，直接 read() 问题不大，也可用 stream)
              with open(local_path, "rb") as f:
                file_content = f.read()

              _response = await oss_client.put(
                  url=upload_sign_url["uploadUrl"],
                  content=file_content,
                  headers=upload_sign_url["headers"]
              )
              _response.raise_for_status()
            except Exception as upload_e:
              self.logger.error(f"Failed to upload {object_key}: {upload_e}")
              raise upload_e

          total_pages = len(pages_data)
          for idx, page_data in enumerate(pages_data):
            cropped_webp_path = page_data.cropped_webp_path
            original_webp_path = page_data.original_webp_path

            # 计算 Object Key (去除本地 var/ 前缀)
            # 使用 removeprefix 是 Python 3.9+ 的安全写法
            object_key_crop = cropped_webp_path.removeprefix(var_prefix)
            object_key_orig = original_webp_path.removeprefix(var_prefix)

            triheart_page_model: TriHeartPageModel = TriHeartPageModel(
                book_id=book_id,
                page_no=page_data.page_no,
                page_content="\n".join(page_data.content) if page_data.content else "",
                crop_box_data=page_data.crop_box_data
            )
            triheart_page_model.page_image_crop_path = object_key_crop
            triheart_page_model.page_image_path = object_key_orig
            triheart_page_models.append(triheart_page_model)

            # 并发执行当前页的裁剪图和原图上传
            # 使用 gather 可以同时发起两个上传请求
            await asyncio.gather(
                _upload_image(cropped_webp_path, object_key_crop),
                _upload_image(original_webp_path, object_key_orig)
            )

            if (idx + 1) % 10 == 0:
              self.logger.info(f"Uploading images: {idx + 1}/{total_pages}")

        await page_service.create_batch(user_id, triheart_page_models, commit=False)

        # 4.4 建立 章节-书页 关联 (Relation) - [优化版]
        # 建立 页码 -> PageID 的快速查找字典
        page_map: Dict[int, str] = {
          p.page_no: p.model_id
          for p in triheart_page_models
          if p.page_no is not None
        }

        triheart_chapter_page_models: list[TriHeartChapterPageModel] = []

        # 遍历所有章节，根据其范围直接查找页码
        for _flat_chapter_model in _flat_triheart_chapter_models:
          start_page = _flat_chapter_model.from_page_no
          end_page = _flat_chapter_model.to_page_no

          if start_page is not None and end_page is not None:
            # 直接生成该章节覆盖的页码范围
            for p_no in range(start_page, end_page + 1):
              # O(1) 查找 PageID
              if p_no in page_map:
                rel = TriHeartChapterPageModel(
                    chapter_id=_flat_chapter_model.model_id,
                    page_id=page_map[p_no]
                )
                triheart_chapter_page_models.append(rel)

        if triheart_chapter_page_models:
          await cp_service.create_batch(user_id, triheart_chapter_page_models, commit=False)

        # 4.5 更新书籍信息
        # 如果没有封面，使用第一页作为封面
        if not book.book_cover and triheart_page_models:
          book.book_cover = triheart_page_models[0].page_image_path
        book.process_status = PROC_SUCCESS
        # 最终更新并提交事务！(commit=True)
        await self.update(user_id, book, commit=True)
        await task_manager.update_progress(task_id, 100, "书籍解析及上传全部完成")
        self.logger.info(f"Task Success: Book {book.book_title} parsed.")

      else:
        # 业务失败逻辑
        self.logger.error(f"Task Failed Logic: {msg}")
        book.process_status = PROC_FAILED
        book.remark = f"解析失败: {msg}"
        await self.update(user_id, book, commit=True)

    except Exception as e:
      self.logger.error(f"Task Exception: {e}", exc_info=True)
      # 发生异常回滚事务
      await self.db.rollback()

      # 尝试记录错误状态（需要新的事务）
      try:
        # 注意：rollback后 session 依然可用，但需要小心使用
        book.process_status = PROC_FAILED
        book.remark = f"系统异常: {str(e)}"
        await self.update(user_id, book, commit=True)
      except:
        pass

  async def ai_extraction_logic(self, user_id: str, book_id: str, from_page: int, to_page: int):
    """
    仅执行 AI 文本分析，生成 Term 记录，不操作 PDF
    """
    self.logger.info(f"🤖 [AI Task] 开始提取: Book={book_id}, Range={from_page}-{to_page}")

    term_service = TriHeartTermService(self.db)
    page_service = TriHeartPageService(self.db)

    # 1. 查书
    book = await self.get(user_id, book_id)
    if not book:
      self.logger.error("书籍不存在")
      return

    if not app_settings.AI_ENABLE:
      self.logger.error("AI 功能未开启")
      return

    # 2. 查文本 (从数据库 Page 表查，不需要 PDF 文件)
    page_query = TriHeartPageQuery(book_id=book_id, begin_page_no=from_page, end_page_no=to_page)
    pages = await page_service.query_all(user_id, page_query)

    full_text = "\n".join([p.page_content for p in pages if p.page_content])
    if not full_text or len(full_text) < 50:
      self.logger.warning("指定范围内容太少，跳过 AI 提取")
      return

    # 3. 调用 AI
    ai_helper = AiHelper(api_key=app_settings.AI_API_KEY, base_url=app_settings.AI_BASE_URL, model=app_settings.AI_MODEL_NAME, max_tokens=app_settings.AI_MAX_TOKENS)
    try:
      ai_terms_list = await ai_helper.extract_terms_from_text(full_text)
    except Exception as e:
      self.logger.error(f"AI API 调用失败: {e}")
      return

    if not ai_terms_list:
      self.logger.info("AI 未返回任何术语")
      return

    # 4. 入库去重
    term_query = TriHeartTermQuery(book_id=book_id)
    existing_terms = await term_service.query_all(user_id, term_query)
    existing_term_keys = {t.term_key for t in existing_terms}

    new_terms = []
    for item in ai_terms_list:
      key = item['term']
      desc = item['desc']
      if key not in existing_term_keys:
        new_terms.append(TriHeartTermModel(
            book_id=book_id,
            source_type="2",  # AI抽取
            term_key=key,
            term_explanation=desc
        ))
        existing_term_keys.add(key)  # 防止本次批次内部重复

    if new_terms:
      await term_service.create_batch(user_id, new_terms, commit=True)
      self.logger.info(f"✅ [AI Task] 新增术语 {len(new_terms)} 条")
    else:
      self.logger.info("✅ [AI Task] 没有发现新术语")

  async def scan_coordinates_logic(self, user_id: str, book_id: str):
    """
    全书扫描：
    1. 下载 PDF (如果不存在)
    2. 获取该书所有 Term
    3. 使用 PyMuPDF 扫描所有页面的坐标
    4. 覆盖写入 PageTerm 关联表
    """
    self.logger.info(f"🔍 [Scan Task] 开始全书坐标扫描: Book={book_id}")

    term_service = TriHeartTermService(self.db)
    page_term_service = TriHeartPageTermService(self.db)

    # 1. 准备书籍和文件
    book = await self.get(user_id, book_id)
    if not book or not book.book_pdf_path:
      self.logger.error("书籍无效或无 PDF 路径")
      return

    var_prefix = "var/"
    # 兼容相对路径和绝对路径
    relative_pdf_path = book.book_pdf_path.lstrip("/")
    local_pdf_path = f"{var_prefix}{relative_pdf_path}"

    # 【核心修复】确保 PDF 存在
    if not os.path.exists(local_pdf_path):
      self.logger.info(f"本地缺少 PDF，正在从 OSS 下载: {book.book_pdf_path}")
      try:
        os.makedirs(os.path.dirname(local_pdf_path), exist_ok=True)
        pdf_signed_url = await self.get_oss_download_sign_url(user_id, book.book_pdf_path)

        async with httpx.AsyncClient() as client:
          resp = await client.get(pdf_signed_url)
          if resp.status_code == 200:
            with open(local_pdf_path, "wb") as f:
              f.write(resp.content)
            self.logger.info("PDF 下载成功")
          else:
            self.logger.error(f"PDF 下载失败 HTTP {resp.status_code}")
            return
      except Exception as e:
        self.logger.error(f"PDF 下载异常: {e}")
        return

    # 2. 获取所有关键词
    term_query = TriHeartTermQuery(book_id=book_id)
    all_terms = await term_service.query_all(user_id, term_query)
    if not all_terms:
      self.logger.warning("该书没有任何术语，无需扫描")
      return

    term_map = {t.term_key: t.model_id for t in all_terms}
    target_keywords = list(term_map.keys())

    self.logger.info(f"待扫描关键词数: {len(target_keywords)}")

    # 3. 执行扫描 (CPU 密集型，放入线程池)
    # 扫描全书：1 到 book_page_count
    total_pages = book.book_page_count or 1000

    scan_result = await run_in_threadpool(
        PdfHelper.scan_terms_in_range,
        pdf_path=local_pdf_path,
        from_page=1,
        to_page=total_pages,
        keywords=target_keywords
    )

    if not scan_result:
      self.logger.info("未匹配到任何坐标")
      return

    # 4. 入库 (先删后加)
    # 清理该书所有的旧坐标记录
    await page_term_service.delete_query(user_id, TriHeartPageTermQuery(book_id=book_id), commit=False)

    new_page_terms = []
    for page_no, matches in scan_result.items():
      for match in matches:
        term_key = match['term']
        rects = match['rects']
        term_id = term_map.get(term_key)

        if term_id:
          new_page_terms.append(TriHeartPageTermModel(
              book_id=book_id,
              page_no=page_no,
              term_id=term_id,
              term_key=term_key,
              rects_json=rects
          ))

    if new_page_terms:
      # 批量写入
      # 注意：如果数据量特别大（如几万条），建议分批写入，这里假设一般就在几千条以内
      await page_term_service.create_batch(user_id, new_page_terms, commit=True)
      self.logger.info(f"✅ [Scan Task] 扫描完成，更新了 {len(new_page_terms)} 条坐标关联")
    else:
      await page_term_service.get_crud().commit()  # 提交删除操作
      self.logger.info("✅ [Scan Task] 扫描完成，但没有匹配项 (已清理旧数据)")


class PageRectsMixinService(Generic[M]):
  """
  Mixin Service for handling coordinate transformation for models
  that contain page_no, book_id, and a rects_json-like field.
  """
  db: Any  # Will be set by the main service
  logger: Any

  def __init__(self, db):
    self.db = db
    self.logger = database.logger  # Use the logger from the database module

  async def _get_page_crop_data_map(self, user_id: str | None, book_id: str, page_numbers: list[int]) -> dict[tuple[str, int], str | None]:
    """
    Helper to batch query `crop_box_data` for a set of (book_id, page_no) tuples.
    """
    if not book_id or not page_numbers:
      return {}

    page_crop_data_map: Dict[Tuple[str, int], str | None] = {}

    pages = await TriHeartPageService(self.db).query_all(user_id, TriHeartPageQuery(book_id=book_id, page_numbers=page_numbers))
    for page in pages:
      # Access by index since row is a Row type
      page_crop_data_map[(page.book_id, page.page_no)] = page.crop_box_data

    return page_crop_data_map

  def _transform_rects_for_page_mode(self, original_rects: list[list[float]], crop_box_data: str | None) -> list[list[float]]:
    """
    Transforms coordinates from original image percentage to cropped image percentage.
    """
    if not original_rects:
      return []

    view_window = [0.0, 0.0, 1.0, 1.0]  # Default to full image
    if crop_box_data:
      try:
        parsed_view_window = json.loads(crop_box_data)
        if isinstance(parsed_view_window, list) and len(parsed_view_window) == 4 and all(isinstance(val, (int, float)) for val in parsed_view_window):
          view_window = parsed_view_window
        else:
          self.logger.warning(f"Invalid crop_box_data format: {crop_box_data}. Using default.")
      except json.JSONDecodeError:
        self.logger.warning(f"Failed to parse crop_box_data JSON: {crop_box_data}. Using default.")
      except Exception as e:
        self.logger.error(f"Error processing crop_box_data: {e}. Using default.")

    vx, vy, vw, vh = view_window

    # If it's a full image (no crop), no transformation needed
    if vx == 0.0 and vy == 0.0 and vw == 1.0 and vh == 1.0:
      return original_rects

    new_rects = []
    for r in original_rects:
      # r: [x, y, w, h] (original image percentage)
      ox, oy, ow, oh = r

      # Coordinate transformation algorithm
      # 1. Subtract viewport offset (becomes distance relative to cropped image's top-left)
      # 2. Divide by viewport width/height (becomes percentage relative to cropped image size)
      nx = (ox - vx) / vw
      ny = (oy - vy) / vh
      nw = ow / vw
      nh = oh / vh

      # Simple boundary check: if it's completely outside the cropped area, discard
      if nx + nw < 0 or nx > 1 or ny + nh < 0 or ny > 1:
        continue

      new_rects.append([round(nx, 4), round(ny, 4), round(nw, 4), round(nh, 4)])  # Retain 4 decimal places

    return new_rects

  def _transform_rects_to_original_mode(self, current_rects: list[list[float]], crop_box_data: str | None) -> list[list[float]]:
    """
    Transforms coordinates from cropped image percentage back to original image percentage.
    This is used when saving highlight_rects captured in 'crop' mode to 'original' mode in DB.
    """
    if not current_rects:
      return []

    view_window = [0.0, 0.0, 1.0, 1.0]  # Default to full image
    if crop_box_data:
      try:
        parsed_view_window = json.loads(crop_box_data)
        if isinstance(parsed_view_window, list) and len(parsed_view_window) == 4 and all(isinstance(val, (int, float)) for val in parsed_view_window):
          view_window = parsed_view_window
        else:
          self.logger.warning(f"Invalid crop_box_data format: {crop_box_data}. Using default.")
      except json.JSONDecodeError:
        self.logger.warning(f"Failed to parse crop_box_data JSON: {crop_box_data}. Using default.")
      except Exception as e:
        self.logger.error(f"Error processing crop_box_data: {e}. Using default.")

    vx, vy, vw, vh = view_window

    if vx == 0.0 and vy == 0.0 and vw == 1.0 and vh == 1.0:
      return current_rects

    new_rects = []
    for r in current_rects:
      cx, cy, cw, ch = r

      ox = vx + (cx * vw)
      oy = vy + (cy * vh)
      ow = cw * vw
      oh = ch * vh

      new_rects.append([round(ox, 4), round(oy, 4), round(ow, 4), round(oh, 4)])  # Retain 4 decimal places

    return new_rects

  async def rects_transform_batch(self, image_mode: str, book_id: str, page_numbers: list[int], models: list[M], rects_field_name: str) -> None:
    """
    Performs coordinate transformation on a batch of models if image_mode is 'crop'.
    It expects models to have `book_id`, `page_no`, and the specified `rects_field_name` attribute.
    """
    if not models or not book_id or not page_numbers:
      return

    if image_mode == 'crop':
      page_crop_data_map = await self._get_page_crop_data_map(None, book_id, page_numbers)

      for model in models:
        if hasattr(model, 'book_id') and hasattr(model, 'page_no') and model.book_id and hasattr(model, rects_field_name):
          original_rects = getattr(model, rects_field_name)
          crop_box_data = page_crop_data_map.get((model.book_id, model.page_no))
          transformed_rects = self._transform_rects_for_page_mode(original_rects, crop_box_data)
          setattr(model, rects_field_name, transformed_rects)


class TriHeartBookUserService(StringPKeyWithDictionaryService[TriHeartBookUserModel, TriHeartBookUserCrud, TriHeartBookUserQuery], PaymentServiceMixin):

  async def unique_constraints(self, models: Sequence[TriHeartBookUserModel]) -> list[UniqueConstraint] | None:
    constraints = []
    if c := UniqueConstraint.from_models(models, ['book_id', 'user_id']):
      constraints.append(c)
    return constraints

  async def pre_create(self, user_id: str, model: TriHeartBookUserModel) -> None:
    await super().pre_create(user_id, model)
    if not model.user_id:
      model.user_id = user_id

  async def pre_select(self, user_id: str, query: TriHeartBookUserQuery) -> None:
    if not query.user_id:
      query.user_id = user_id
    await super().pre_select(user_id, query)

  async def post_select_batch(self, user_id: str, models: list[TriHeartBookUserModel], query: TriHeartBookUserQuery | None = None) -> None:
    await super().post_select_batch(user_id, models, query)
    # 0. 判空
    if not models:
      return

    # 1. 提取去重后的 book_id 列表
    book_ids = list({model.book_id for model in models if model.book_id})
    if not book_ids:
      return

    # 2. 调用 BookService 查询书籍详情
    # 注意：实例化 Service 时传入当前 self.db，复用数据库会话
    book_service = TriHeartBookService(self.db)

    # 使用 CRUD 底层的 get_by_ids 批量查询，效率最高
    # (这里不建议调 Service 层的查询方法，因为可能会受到 owner_id 权限过滤的影响，导致用户查不到管理员发布的书)
    books = await book_service.get_by_ids(user_id, book_ids)

    # 3. 将书籍列表转换为字典 {book_id: book_obj}，方便 O(1) 查找
    book_map = {b.model_id: b for b in books}

    # 4. 遍历原列表，回填数据
    for model in models:
      if model.book_id in book_map:
        # 对应 models.py 中 TriHeartBookUserModel 定义的 book_models 字段 (List类型)
        model.book_model = book_map[model.book_id]

  def resolve_pay_order(self, order: PayOrderModel) -> TriHeartBookUserModel:
    return TriHeartBookUserModel(book_id=order.business_id, user_id=order.user_id, purchase_status="1")

  def resolve_update_fields(self, order: PayOrderModel, model: TriHeartBookUserModel) -> set[str] | None:
    return {"purchase_status"}


class TriHeartBookNoteService(StringPKeyWithDictionaryService[TriHeartBookNoteModel, TriHeartBookNoteCrud, TriHeartBookNoteQuery], PageRectsMixinService[TriHeartBookNoteModel]):
  def __init__(self, db: Any):
    super().__init__(db=db)

  async def pre_create(self, user_id: str, model: TriHeartBookNoteModel) -> None:
    await super().pre_create(user_id, model)
    if not model.user_id:
      model.user_id = user_id

    if model.crop_mode == True and model.book_id and model.page_no and model.highlight_rects:
      page_service = TriHeartPageService(self.db)
      page = await page_service.query_one(user_id, TriHeartPageQuery(book_id=model.book_id, page_no=model.page_no))

      if page and page.crop_box_data:
        cropped_rects_from_frontend = model.highlight_rects
        transformed_rects_to_original = self._transform_rects_to_original_mode(cropped_rects_from_frontend, page.crop_box_data)
        model.highlight_rects = transformed_rects_to_original
        self.logger.info(f"BookNote pre_create: Transformed rects from crop to original mode for book={model.book_id}, page={model.page_no}")
      else:
        self.logger.warning(f"BookNote pre_create: Could not find crop_box_data for book={model.book_id}, page={model.page_no} or page not found. Storing rects as is.")

  async def pre_update(self, user_id: str, old_model: TriHeartBookNoteModel, new_model: TriHeartBookNoteModel, update_fields: set[str]) -> None:
    await super().pre_update(user_id, old_model, new_model, update_fields)
    update_fields.remove("highlight_rects")

  async def post_select_batch(self, user_id: str | None, models: list[TriHeartBookNoteModel], query: TriHeartBookNoteQuery | None = None) -> None:
    await super().post_select_batch(user_id, models, query)

    if not models or query is None or query.image_mode is None:
      return

    page_nos = list(set(model.page_no for model in models if model.page_no))
    await self.rects_transform_batch(query.image_mode, query.book_id, page_nos, models, "highlight_rects")


class TriHeartTermService(StringPKeyWithDictionaryService[TriHeartTermModel, TriHeartTermCrud, TriHeartTermQuery]):
  pass


class TriHeartPageTermService(StringPKeyWithDictionaryService[TriHeartPageTermModel, TriHeartPageTermCrud, TriHeartPageTermQuery], PageRectsMixinService[TriHeartPageTermModel]):

  def __init__(self, db: Any):
    super().__init__(db=db)

  async def post_select_batch(self, user_id: str, models: list[TriHeartPageTermModel], query: TriHeartPageTermQuery | None = None) -> None:
    # 1. 执行父类逻辑（处理字典转换等）
    await super().post_select_batch(user_id, models, query)

    if not models:
      return

    term_ids = list(set(model.term_id for model in models if model.term_id))
    if term_ids:
      term_map: dict[str, TriHeartTermModel] = {}
      term_service = TriHeartTermService(self.db)
      terms = await term_service.get_by_ids(user_id, term_ids)
      if terms:
        term_map = {t.model_id: t for t in terms}
        for model in models:
          term = term_map.get(model.term_id)
          if not term:
            continue
          model.term_key = term.term_key
          model.term_explanation = term.term_explanation

    page_nos = list(set(model.page_no for model in models if model.page_no))
    await self.rects_transform_batch(query.image_mode, query.book_id, page_nos, models, "rects_json")


class TriHeartPageAttachmentService(StringPKeyWithDictionaryService[TriHeartPageAttachmentModel, TriHeartPageAttachmentCrud, TriHeartPageAttachmentQuery]):
  pass


PaymentDispatcher.register_service("book_purchase", TriHeartBookUserService)
