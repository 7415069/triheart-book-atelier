# /app/routers.py
import asyncio

from brtech_backend.core.enums import OperateType
from brtech_backend.core.routers import StringPKeyRecurseRouter, StringPKeyRouter, RouterMeta, Public, RouteKey
from brtech_backend.core.schemas import RestResponse, PageResult
from brtech_backend.core.security import AuthContext
from brtech_backend.dictionary.routers import StringPKeyWithDictionaryRouter
from brtech_backend.task.services import task_manager
from fastapi import Path, Depends, Body
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

from .crud import TriHeartBookCrud, TriHeartChapterCrud, TriHeartPageCrud, TriHeartChapterPageCrud, TriHeartBookUserCrud, TriHeartBookNoteCrud, TriHeartTermCrud, TriHeartPageTermCrud, TriHeartPageAttachmentCrud
from .models import TriHeartBookModel, TriHeartChapterModel, TriHeartPageModel, TriHeartChapterPageModel, TriHeartBookUserModel, TriHeartBookNoteModel, TriHeartTermModel, TriHeartPageTermModel, TriHeartPageAttachmentModel
from .schemas import TriHeartBookQuery, TriHeartChapterQuery, TriHeartPageQuery, TriHeartChapterPageQuery, TriHeartBookUserQuery, TriHeartBookNoteQuery, TriHeartTermQuery, TriHeartPageTermQuery, TriHeartPageAttachmentQuery
from .services import TriHeartBookService, TriHeartChapterService, TriHeartPageService, TriHeartChapterPageService, TriHeartBookUserService, TriHeartBookNoteService, TriHeartTermService, TriHeartPageTermService, \
  TriHeartPageAttachmentService


class WebpUrlRequest(BaseModel):
  # Field(alias="bookId") 告诉前端传 bookId，后端用 book_id 接收
  book_id: str = Field(..., description="书籍ID")
  page_no: int = Field(..., description="书页编号")
  webp_type: str = Field(..., description="Webp类型: crop; origin")

  model_config = ConfigDict(extra='allow', alias_generator=to_camel, populate_by_name=True, from_attributes=True, strict=True)


class ExtractRequest(BaseModel):
  from_page_no: int
  to_page_no: int

  model_config = ConfigDict(extra='allow', alias_generator=to_camel, populate_by_name=True, from_attributes=True, strict=True)


@Public(RouteKey.FIND_ID)
@RouterMeta(prefix="/book", tags=["三心书坊 - 书籍管理"], module_name="书籍管理")
class TriHeartBookRouter(StringPKeyWithDictionaryRouter[TriHeartBookModel, TriHeartBookCrud, TriHeartBookQuery, TriHeartBookService]):
  def _register_routes(self):
    # 1. 保留父类默认的 CRUD 路由
    super()._register_routes()

    # 2. 注册自定义的 PDF 解析路由
    @self.router.post(
        "/parse/{model_id}", summary="触发PDF解析",
        openapi_extra=self._operation("触发PDF解析", OperateType.OTHER, True)
    )
    async def parse_pdf(
        model_id: str = Path(..., description="书籍ID"),
        # 这里的 Depends 会自动获取当前用户 ID
        auth_context: AuthContext = Depends(self.user_dependency)
    ):
      from .services import run_pdf_task_wrapper
      # A. 在数据库创建任务记录
      task_id = await task_manager.create_task(
          user_id=auth_context.user_id,
          task_type="pdf_parse",
          task_name=f"解析书籍PDF",
          ref_id=model_id,
          ref_type="book"
      )
      # B. 启动后台任务，使用 task_manager.run_task 自动管理状态
      asyncio.create_task(task_manager.run_task(task_id, run_pdf_task_wrapper(auth_context.user_id, model_id, task_id)))
      return RestResponse.success(data={"taskId": task_id}, message="PDF解析任务已启动")

    async def query_mixed(
        query: TriHeartBookQuery = Body(..., description="混合模式分页查询条件"),
        service: TriHeartBookService = Depends(self._get_service),
        auth_context: AuthContext = Depends(self.optional_user_dependency)
    ):
      page_result = await service.query_page(auth_context.user_id, query)
      return RestResponse.success(page_result)

    query_mixed.__annotations__["query"] = self.query_schema
    self.router.add_api_route(
        "/query/mixed", query_mixed, methods=["POST"],
        response_model=RestResponse[PageResult[self.model_schema]],  # type: ignore
        summary=f"{self.module_name} - 混合模式分页查询",
        openapi_extra=self._operation("混合模式分页查询", OperateType.QUERY)
    )

    @self.router.post(
        "/extract/{model_id}", summary="AI章节术语提取",
        openapi_extra=self._operation("AI章节术语提取", OperateType.OTHER, True)
    )
    async def extract_terms_async(
        req: ExtractRequest,
        model_id: str = Path(..., description="书籍ID"),
        auth_context: AuthContext = Depends(self.user_dependency)
    ):
      from .services import run_extract_terms_task
      task_id = await task_manager.create_task(
          user_id=auth_context.user_id,
          task_type="term_extract",
          task_name=f"AI术语提取({req.from_page_no}-{req.to_page_no}页)",
          ref_id=model_id,
          ref_type="book"
      )
      asyncio.create_task(task_manager.run_task(task_id, run_extract_terms_task(auth_context.user_id, model_id, req.from_page_no, req.to_page_no, task_id)))
      return RestResponse.success(data={"taskId": task_id}, message="AI提取任务已启动")

    # 2. 坐标扫描 (拆分后：只扫坐标)
    @self.router.post(
        "/scanCoords/{model_id}", summary="术语坐标扫描",
        openapi_extra=self._operation("术语坐标扫描", OperateType.OTHER, True)
    )
    async def scan_coords_async(
        model_id: str = Path(..., description="书籍ID"),
        auth_context: AuthContext = Depends(self.user_dependency)
    ):
      from .services import run_scan_coords_task

      task_id = await task_manager.create_task(
          user_id=auth_context.user_id,
          task_type="coord_scan",
          task_name=f"全书坐标扫描",
          ref_id=model_id,
          ref_type="book"
      )
      asyncio.create_task(task_manager.run_task(task_id, run_scan_coords_task(auth_context.user_id, model_id, task_id)))
      return RestResponse.success(data={"taskId": task_id}, message="坐标扫描任务已启动")

    @self.router.post(
        "/coverSignUrl/{bookId}", summary="获取书籍签封面名地址",
        openapi_extra=self._operation("获取书籍签封面名地址", OperateType.QUERY)
    )
    async def cover_sign_url(
        bookId: str = Path(..., description="书籍ID"),
        service: TriHeartBookService = Depends(self._get_service),
        auth_context: AuthContext = Depends(self.optional_user_dependency)
    ):
      book: TriHeartBookModel | None = await service.get(auth_context.user_id, bookId)
      sign_url: str | None = ""
      if book:
        sign_url = await service.get_oss_download_sign_url(auth_context.user_id, book.book_cover, None)
      return RestResponse.success(data=sign_url)

  pass


@RouterMeta(prefix="/chapter", tags=["三心书坊 - 章节管理"], module_name="章节管理")
class TriHeartChapterRouter(StringPKeyRecurseRouter[TriHeartChapterModel, TriHeartChapterCrud, TriHeartChapterQuery, TriHeartChapterService]):
  pass


@RouterMeta(prefix="/page", tags=["三心书坊 - 书页管理"], module_name="书页管理")
class TriHeartPageRouter(StringPKeyRouter[TriHeartPageModel, TriHeartPageCrud, TriHeartPageQuery, TriHeartPageService]):

  def _register_routes(self):
    super()._register_routes()

    @self.router.post(
        "/webpUrl", summary="获取Webp地址",
        openapi_extra=self._operation("获取Webp地址", OperateType.QUERY)
    )
    async def get_webp_url(
        # 使用定义好的 Model
        request_data: WebpUrlRequest,
        service: TriHeartPageService = Depends(self._get_service),
        auth_context: AuthContext = Depends(self.optional_user_dependency)
    ):
      # 调用 Service 时，通过 request_data.book_id 访问
      webp_url = await service.get_webp_url(auth_context.user_id, request_data.book_id, request_data.page_no, request_data.webp_type)

      return RestResponse.success(data=webp_url, message="获取成功")


@RouterMeta(prefix="/chapterPage", tags=["三心书坊 - 章节&︎书页关系管理"], module_name="章节&︎书页关系管理")
class TriHeartChapterPageRouter(StringPKeyRouter[TriHeartChapterPageModel, TriHeartChapterPageCrud, TriHeartChapterPageQuery, TriHeartChapterPageService]):
  pass


@RouterMeta(prefix="/bookUser", tags=["三心书坊 - 书籍&用户关系管理"], module_name="书籍&用户关系管理")
class TriHeartBookUserRouter(StringPKeyRouter[TriHeartBookUserModel, TriHeartBookUserCrud, TriHeartBookUserQuery, TriHeartBookUserService]):
  pass


@RouterMeta(prefix="/bookNote", tags=["三心书坊 - 读书笔记管理"], module_name="读书笔记管理")
class TriHeartBookNoteRouter(StringPKeyRouter[TriHeartBookNoteModel, TriHeartBookNoteCrud, TriHeartBookNoteQuery, TriHeartBookNoteService]):
  pass


@RouterMeta(prefix="/term", tags=["三心书坊 - 术语管理"], module_name="术语管理")
class TriHeartTermRouter(StringPKeyRouter[TriHeartTermModel, TriHeartTermCrud, TriHeartTermQuery, TriHeartTermService]):
  pass


@RouterMeta(prefix="/pageTerm", tags=["三心书坊 - 书页&术语关系管理"], module_name="书页&术语关系管理")
class TriHeartPageTermRouter(StringPKeyRouter[TriHeartPageTermModel, TriHeartPageTermCrud, TriHeartPageTermQuery, TriHeartPageTermService]):
  pass


@RouterMeta(prefix="/pageAttachment", tags=["三心书坊 - 书页&附件关系管理"], module_name="书页&附件关系管理")
class TriHeartPageAttachmentRouter(StringPKeyRouter[TriHeartPageAttachmentModel, TriHeartPageAttachmentCrud, TriHeartPageAttachmentQuery, TriHeartPageAttachmentService]):
  pass


thba_router_classes = [
  TriHeartBookRouter, TriHeartChapterRouter, TriHeartPageRouter, TriHeartChapterPageRouter, TriHeartBookUserRouter,
  TriHeartBookNoteRouter, TriHeartTermRouter, TriHeartPageTermRouter, TriHeartPageAttachmentRouter
]
