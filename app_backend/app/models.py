# /app/models.py
from typing import Annotated, Any

from brtech_backend.core.annotations import FieldOption, UIComponent, DataOption, Action, StandardAdd, StandardEdit, StandardDetail, ui_config, EnableQuery, QueryType, Dictionary, StoreType, StandardDelete
from brtech_backend.core.enums import ActionType, PayloadLocation
from brtech_backend.core.extra.sqlmodel_extra import ExtraSQLModelField
from brtech_backend.core.models import StringPKeyModel, StringPKeyRecurseModel, HDatetime
from sqlalchemy import String, Integer, Text, UniqueConstraint, DateTime, JSON
from sqlmodel import Field as SQLModelField


@ui_config(
    module_name="书籍管理", action_column_width=320,
    layout=[
      "book_title", "book_subtitle", "book_cover", "book_author", "book_pdf_path", "book_translator", "book_page_count", "toc_begin_page", "toc_end_page", "body_page_offset",
      "guest_preview_limit", "user_preview_limit", "owner_id", "book_isbn", "book_category", "book_status", "book_list_price", "book_sale_price", "owner_name",
      FieldOption(prop="create_person", table_show=False, add_show=False, edit_show=False, search_show=False, detail_show=False, span=6),
      FieldOption(prop="create_timestamp", table_show=False, add_show=False, edit_show=False, search_show=False, span=6),
      FieldOption(prop="update_person", table_show=False, add_show=False, edit_show=False, search_show=False, detail_show=False, span=6),
      FieldOption(prop="update_timestamp", table_show=False, add_show=False, edit_show=False, search_show=False, span=6),
      FieldOption(prop="book_summary", table_show=False, span=12),
      FieldOption(prop="remark", table_show=False, span=12)
    ],
    page_actions=[StandardAdd(dialog_width="1200px")],
    row_actions=[
      Action(
          code="page_read", label="阅读", icon="Reading",
          type=ActionType.LINK, target="_blank",
          router_path="/{CONTEXT_PATH}/{UI_PATH}/reader/{modelId}/1", include_router_prefix=False
      ),
      Action(
          code="boot_chapter_manage", label="章节管理", icon="Collection",
          type=ActionType.ROUTER, router_path="/business/chapter", query_params={"bookId": "modelId"}
      ),
      Action(
          code="boot_page_manage", label="书页管理", icon="Postcard",
          type=ActionType.ROUTER, router_path="/business/page", query_params={"bookId": "modelId"}
      ),
      Action(
          code="boot_parse_pdf", label="书籍解析", icon="SetUp", type=ActionType.API,
          api_url="/book/parse/{modelId}", method="POST", payload_location=PayloadLocation.PATH,
          confirm_msg="确定要重新解析该书籍吗？这将覆盖现有数据。"
      ),
      Action(
          code="boot_term_manage", label="术语管理", icon="HelpFilled",
          type=ActionType.ROUTER, router_path="/business/term", query_params={"bookId": "modelId"}
      ),
      Action(
          code="boot_term_scan", label="坐标扫描", icon="Aim", type=ActionType.API,
          api_url="/book/scanCoords/{modelId}", method="POST", payload_location=PayloadLocation.PATH,
          confirm_msg="确定要根据现有术语表，重新扫描全书的坐标吗？"
      ),
      StandardDetail(dialog_width="1200px"), StandardEdit(dialog_width="1200px")
    ]
)
class TriHeartBookModel(StringPKeyModel, table=True):
  __tablename__ = "triheart_book"
  book_title: Annotated[
    str | None,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, required=True, search_required=False, span=12, column_width=300, search_span=9, component=UIComponent.INPUT),
    EnableQuery(query_type=QueryType.LIKE)
  ] = SQLModelField(
      description="书籍标题",
      sa_type=String, max_length=128, nullable=False,
      sa_column_kwargs={"name": "book_title", "comment": "书籍标题"}
  )
  book_subtitle: Annotated[
    str | None,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, span=12, column_width=300, search_span=9, component=UIComponent.INPUT),
    EnableQuery(query_type=QueryType.LIKE)
  ] = SQLModelField(
      description="书籍副标题",
      sa_type=String, max_length=128, nullable=True,
      sa_column_kwargs={"name": "book_subtitle", "comment": "书籍副标题"}
  )

  book_isbn: Annotated[
    str | None,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, span=8, search_span=6, required=False, component=UIComponent.INPUT),
    EnableQuery(query_type=QueryType.LIKE)
  ] = SQLModelField(
      description="书籍ISBN",
      sa_type=String, max_length=32, nullable=True,
      sa_column_kwargs={"name": "book_isbn", "comment": "书籍ISBN"}
  )

  book_author: Annotated[
    str | None,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, span=6, required=True, search_required=False, component=UIComponent.INPUT),
    EnableQuery(query_type=QueryType.LIKE)
  ] = SQLModelField(
      description="书籍作者",
      sa_type=String, max_length=64, nullable=True,
      sa_column_kwargs={"name": "book_author", "comment": "书籍作者"}
  )

  book_translator: Annotated[
    str | None,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, span=6, component=UIComponent.INPUT),
    EnableQuery(query_type=QueryType.LIKE)
  ] = SQLModelField(
      description="书籍翻译者",
      sa_type=String, max_length=64, nullable=True,
      sa_column_kwargs={"name": "book_translator", "comment": "书籍翻译者"}
  )

  book_cover: Annotated[
    str | None,
    FieldOption(
        table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=False, span=18, detail_span=18,
        component=UIComponent.IMAGE, component_props=FieldOption.UploadComponentProps(accept="image/*", max_size=20, limit=1)
    )
  ] = SQLModelField(
      description="书籍封面",
      sa_type=String, max_length=256, nullable=True,
      sa_column_kwargs={"name": "book_cover", "comment": "书籍封面"}
  )

  book_summary: Annotated[
    str,
    FieldOption(table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=False, required=True, component=UIComponent.TEXTAREA, component_props={"rows": 3})
  ] = SQLModelField(
      description="书籍摘要",
      sa_type=Text, nullable=True,
      sa_column_kwargs={"name": "book_summary", "comment": "书籍摘要"}
  )

  book_pdf_path: Annotated[
    str | None,
    FieldOption(
        table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=False, span=18, detail_span=18,
        component=UIComponent.UPLOAD, component_props=FieldOption.UploadComponentProps(accept=".pdf", max_size=50, limit=1)
    )
  ] = SQLModelField(
      description="书籍PDF路径", exclude=True,
      sa_type=String, max_length=256, nullable=True,
      sa_column_kwargs={"name": "book_pdf_path", "comment": "书籍PDF路径"}
  )

  book_page_count: Annotated[
    int,
    FieldOption(table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=False, required=True, span=4, component=UIComponent.INPUT_NUMBER)
  ] = SQLModelField(
      description="书籍总页数",
      sa_type=Integer, nullable=True,
      sa_column_kwargs={"name": "book_page_count", "comment": "书籍总页数"}
  )

  body_page_offset: Annotated[
    int | None,
    FieldOption(table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=False, required=False, span=4, component=UIComponent.INPUT_NUMBER)
  ] = SQLModelField(
      description="正文页码偏移量",
      sa_type=Integer, nullable=True,
      sa_column_kwargs={"name": "body_page_offset", "comment": "正文页码偏移量"}
  )

  toc_begin_page: Annotated[
    int | None,
    FieldOption(table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=False, required=False, span=4, component=UIComponent.INPUT_NUMBER)
  ] = SQLModelField(
      description="目录开始页码",
      sa_type=Integer, nullable=True,
      sa_column_kwargs={"name": "toc_begin_page", "comment": "目录开始页码"}
  )
  toc_end_page: Annotated[
    int | None,
    FieldOption(table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=False, required=False, span=4, component=UIComponent.INPUT_NUMBER)
  ] = SQLModelField(
      description="目录结束页码",
      sa_type=Integer, nullable=True,
      sa_column_kwargs={"name": "toc_end_page", "comment": "目录结束页码"}
  )

  book_category: Annotated[
    str | None,
    FieldOption(table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=True, required=True, search_required=False, span=4, search_span=4, component=UIComponent.SELECT),
    Dictionary(store_type=StoreType.DICTIONARY_VALUE, dictionary_type="book_category", display_field_name="book_category_display"),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="书籍分类：book_category",
      sa_type=String, max_length=128, nullable=True,
      sa_column_kwargs={"name": "book_category", "comment": "书籍分类"}
  )
  book_category_display: Annotated[
    str,
    FieldOption(table_show=False, add_show=False, edit_show=False, detail_show=False, search_show=False)
  ] = ExtraSQLModelField(
      description="书籍分类显示", sa_column_exclude=True
  )

  book_list_price: Annotated[
    float,
    FieldOption(table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=False, span=4, component=UIComponent.INPUT_NUMBER)
  ] = SQLModelField(
      description="书籍定价（元）",
      sa_type=Integer, nullable=True,
      sa_column_kwargs={"name": "book_list_price", "comment": "书籍定价（元）"}
  )

  book_sale_price: Annotated[
    float,
    FieldOption(table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=False, required=True, span=4, component=UIComponent.INPUT_NUMBER)
  ] = SQLModelField(
      description="书籍售价（元）",
      sa_type=Integer, nullable=True,
      sa_column_kwargs={"name": "book_sale_price", "comment": "书籍售价（元）"}
  )

  book_status: Annotated[
    str | None,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, required=True, search_required=False, span=4, search_span=4, component=UIComponent.SELECT),
    Dictionary(store_type=StoreType.DICTIONARY_VALUE, dictionary_type="book_status", display_field_name="book_status_display"),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="书籍状态：book_status",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "book_status", "comment": "书籍状态"}
  )

  book_status_display: Annotated[
    str,
    FieldOption(table_show=False, add_show=False, edit_show=False, detail_show=False, search_show=False)
  ] = ExtraSQLModelField(
      description="书籍状态显示", sa_column_exclude=True
  )

  guest_preview_limit: Annotated[
    int,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=False, required=True, span=4, component=UIComponent.INPUT_NUMBER, component_props={"min": 0})
  ] = SQLModelField(
      default=5,  # 默认前5页
      description="游客试读页数",
      sa_type=Integer, nullable=False,
      sa_column_kwargs={"name": "guest_preview_limit", "comment": "游客试读页数"}
  )

  user_preview_limit: Annotated[
    int,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=False, required=True, span=4, column_width=150, component=UIComponent.INPUT_NUMBER, component_props={"min": 0})
  ] = SQLModelField(
      default=10,  # 默认前10页
      description="注册用户试读页数",
      sa_type=Integer, nullable=False,
      sa_column_kwargs={"name": "user_preview_limit", "comment": "注册用户试读页数"}
  )

  process_status: Annotated[
    str | None,
    FieldOption(table_show=True, add_show=False, edit_show=False, detail_show=False, search_show=True, span=6, readonly=True, search_span=4, component=UIComponent.SELECT),
    Dictionary(store_type=StoreType.DICTIONARY_VALUE, dictionary_type="process_status", display_field_name="process_status_display"),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      default="0",
      description="书籍解析状态",
      sa_type=String, max_length=36, nullable=True,
      sa_column_kwargs={"name": "process_status", "comment": "书籍解析状态"}
  )

  process_status_display: Annotated[
    str | None,
    FieldOption(table_show=False, add_show=False, edit_show=False, detail_show=False, search_show=False)
  ] = ExtraSQLModelField(description="书籍解析状态显示", sa_column_exclude=True)

  owner_id: Annotated[
    str | None,
    FieldOption(table_show=False, add_show=False, edit_show=False, detail_show=True, search_show=False, span=12, detail_span=8, component=UIComponent.INPUT),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="书籍所有者",
      sa_type=String, max_length=32, nullable=False,
      sa_column_kwargs={"name": "owner_id", "comment": "书籍所有者"}
  )

  owner_name: Annotated[
    str,
    FieldOption(table_show=True, add_show=False, edit_show=False, detail_show=True, search_show=False, span=12, column_width=200, detail_span=4, component=UIComponent.INPUT)
  ] = ExtraSQLModelField(
      description="书籍所有者姓名", sa_column_exclude=True
  )


@ui_config(
    module_name="章节管理", search_span=8, tree_table=True, load_uri="/query/all", load_lazy=True, action_column_width=200,
    layout=[
      "book_id",
      FieldOption(
          prop="parent_id", label="所属父章节", show=True, table_show=False, span=12, search_span=8, component=UIComponent.TREE_SELECT,
          data_option=DataOption(cascade_field="book_id", lazy_load=True, method="POST", path="/query/all", label_field="chapter_title", value_field="model_id")
      ),
      "chapter_title", "from_page_no", "to_page_no",
      "create_person", "create_timestamp", "update_person", "update_timestamp", "remark"
    ],
    table_layout=["chapter_title"],
    row_actions=[
      Action(
          code="chapter_read", label="阅读", icon="Reading",
          type=ActionType.LINK, target="_blank",
          # 前端行数据: { "modelId": "chapter_01", "bookId": "book_001", "fromPageNo": 20 }
          router_path="/{CONTEXT_PATH}/{UI_PATH}/reader/{bookId}/{fromPageNo}", include_router_prefix=False
      ),
      Action(
          code="boot_term_extraction", label="AI术语提取", icon="MagicStick", type=ActionType.API,
          api_url="/book/extract/{bookId}", method="POST", payload_location=PayloadLocation.BODY,
          context_map={"fromPageNo": "fromPageNo", "toPageNo": "toPageNo"},
          confirm_msg="确定要对章节 '{chapter_title}' (P{fromPageNo}-P{toPageNo}) 执行 AI 术语提取吗？"
      )
    ]
)
class TriHeartChapterModel(StringPKeyRecurseModel, table=True):
  __tablename__ = "triheart_chapter"
  chapter_title: Annotated[
    str | None,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, required=True, search_required=False, span=12, search_span=8, component=UIComponent.INPUT),
    EnableQuery(query_type=QueryType.LIKE)
  ] = SQLModelField(
      description="章节标题",
      sa_type=String, max_length=128, nullable=True,
      sa_column_kwargs={"name": "chapter_title", "comment": "章节标题"}
  )

  from_page_no: Annotated[
    int,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=False, required=True, search_required=False, span=6, component=UIComponent.INPUT_NUMBER)
  ] = SQLModelField(
      description="章节起始页码",
      sa_type=Integer, nullable=True,
      sa_column_kwargs={"name": "from_page_no", "comment": "章节起始页码"}
  )

  to_page_no: Annotated[
    int,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=False, required=True, search_required=False, span=6, component=UIComponent.INPUT_NUMBER)
  ] = SQLModelField(
      description="章节结束页码",
      sa_type=Integer, nullable=True,
      sa_column_kwargs={"name": "to_page_no", "comment": "章节结束页码"}
  )

  book_id: Annotated[
    str | None,
    FieldOption(
        table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, required=True, span=12, search_span=8, component=UIComponent.SELECT,
        data_option=DataOption(model_cls=TriHeartBookModel, method="POST", path="/query/all", label_field="book_title", value_field="model_id")
    ),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="所属书籍",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "book_id", "comment": "所属书籍"}
  )


@ui_config(
    module_name="书页管理", action_column_width=240,
    layout=[
      "book_id", "chapter_ids", "page_no", "page_image_path", "page_image_crop_path", "page_content",
      "create_person", "create_timestamp", "update_person", "update_timestamp", "remark"
    ],
    page_actions=[StandardAdd(dialog_width="1000px")],
    row_actions=[
      Action(
          code="page_read", label="阅读", icon="Reading",
          type=ActionType.LINK, target="_blank",
          # 前端行数据: { "modelId": "page_01", "bookId": "book_001", "pageNo": 50 }
          router_path="/{CONTEXT_PATH}/{UI_PATH}/reader/{bookId}/{pageNo}", include_router_prefix=False
      ),
      Action(
          code="boot_page_term_manage", label="书页&术语关系管理", icon="Comment",
          type=ActionType.ROUTER, router_path="/business/pageTerm", query_params={"bookId": "bookId", "pageNo": "pageNo"}
      ),
      Action(
          code="page_attachments_manage", label="附件管理", icon="Paperclip",
          type=ActionType.ROUTER, router_path="/business/pageAttachment", query_params={"bookId": "bookId", "pageNo": "pageNo"}
      ),
      StandardDetail(dialog_width="1000px"), StandardEdit(dialog_width="1000px")
    ]
)
class TriHeartPageModel(StringPKeyModel, table=True):
  __tablename__ = "triheart_page"

  page_no: Annotated[
    int,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=False, span=6, component=UIComponent.INPUT_NUMBER),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="页码",
      sa_type=Integer, nullable=True,
      sa_column_kwargs={"name": "page_no", "comment": "页码"}
  )

  page_image_path: Annotated[
    str,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=False, span=24, component=UIComponent.IMAGE)
  ] = SQLModelField(
      description="页面图片路径",
      sa_type=String, max_length=256, nullable=True,
      sa_column_kwargs={"name": "page_image_path", "comment": "页面图片路径"}
  )

  page_image_crop_path: Annotated[
    str,
    FieldOption(table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=False, required=False, span=24, component=UIComponent.IMAGE)
  ] = SQLModelField(
      description="页面图片裁剪路径",
      sa_type=String, max_length=256, nullable=True,
      sa_column_kwargs={"name": "page_image_crop_path", "comment": "页面图片裁剪路径"}
  )

  page_content: Annotated[
    str,
    FieldOption(table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=False, span=24, component=UIComponent.TEXTAREA, component_props={"rows": 3})
  ] = SQLModelField(
      description="页面内容",
      sa_type=Text, nullable=True,
      sa_column_kwargs={"name": "page_content", "comment": "页面内容"}
  )

  book_id: Annotated[
    str | None,
    FieldOption(
        table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=True, search_required=True, span=9, search_span=12, component=UIComponent.SELECT,
        data_option=DataOption(model_cls=TriHeartBookModel, method="POST", path="/query/all", label_field="book_title", value_field="model_id")
    ),
    EnableQuery(query_type=QueryType.EQ)
  ] = ExtraSQLModelField(
      description="所属书籍",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "book_id", "comment": "所属书籍"}
  )

  chapter_ids: Annotated[
    list[str] | None,
    FieldOption(
        table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=True, required=False, span=9, component=UIComponent.TREE_SELECT,
        data_option=DataOption(model_cls=TriHeartChapterModel, cascade_field="book_id", lazy_load=True, method="POST", path="/query/all", label_field="chapter_title", value_field="model_id")
    ),
  ] = ExtraSQLModelField(
      description="所属章节列表", sa_column_exclude=True
  )

  crop_box_data: Annotated[
    str,
    FieldOption(show=False)
  ] = SQLModelField(
      description="切边参数",
      sa_type=Text, nullable=True,
      sa_column_kwargs={"name": "crop_box_data", "comment": "切边参数"}
  )


class TriHeartChapterPageModel(StringPKeyModel, table=True):
  __tablename__ = "triheart_chapter_page"
  __table_args__ = (
    UniqueConstraint("chapter_id", "page_id", name="triheart_chapter_page_unique_1"),
  )

  chapter_id: Annotated[
    str,
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="所属章节",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "chapter_id", "comment": "所属章节"}
  )

  page_id: Annotated[
    str,
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="所属页面",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "page_id", "comment": "所属页面"}
  )


@ui_config(
    module_name="用户书架",
    # 这里的 layout 主要是给后台管理员看“谁读了什么书”，或者调试用
    layout=["book_id", "user_id", "purchase_status", "last_read_page_no", "last_read_time"],
    # 通常这个表不需要后台手动新增，而是通过业务逻辑自动创建
    page_actions=[],
    row_actions=[StandardDetail()]
)
class TriHeartBookUserModel(StringPKeyModel, table=True):
  __tablename__ = "triheart_book_user"
  __table_args__ = (
    # 核心约束：一个用户对一本书只有一条记录
    UniqueConstraint("book_id", "user_id", name="triheart_book_user_unique_1"),
  )

  book_id: Annotated[
    str,
    FieldOption(component=UIComponent.INPUT, table_show=True, search_show=True),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="书籍ID",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "book_id", "comment": "书籍ID"}
  )

  user_id: Annotated[
    str,
    FieldOption(component=UIComponent.INPUT, table_show=True, search_show=True),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="用户ID",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "user_id", "comment": "用户ID"}
  )

  purchase_status: Annotated[
    str | None,
    Dictionary(store_type=StoreType.DICTIONARY_VALUE, dictionary_type="yes_no", display_field_name="purchase_status_display"),
    FieldOption(component=UIComponent.SELECT, table_show=True, search_show=True),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="购买状态",
      default="0",  # 默认未购买
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "purchase_status", "comment": "购买状态"}
  )

  purchase_status_display: Annotated[
    str, FieldOption(table_show=False)
  ] = ExtraSQLModelField(description="购买状态显示", sa_column_exclude=True)

  last_read_page_no: Annotated[
    int | None,
    FieldOption(component=UIComponent.INPUT_NUMBER, table_show=True),
  ] = SQLModelField(
      description="最后阅读页码",
      sa_type=Integer, nullable=True,
      sa_column_kwargs={"name": "last_read_page_no", "comment": "最后阅读页码"}
  )

  last_read_time: Annotated[
    HDatetime | None,
    FieldOption(component=UIComponent.DATE_PICKER, component_props=FieldOption.DatePickerComponentProps(type="datetime"), table_show=True),
  ] = SQLModelField(
      description="最后阅读时间",
      sa_type=DateTime, nullable=True,
      sa_column_kwargs={"name": "last_read_time", "comment": "最后阅读时间"}
  )

  book_model: Annotated[
    TriHeartBookModel | None,
    FieldOption(table_show=False)
  ] = ExtraSQLModelField(description="书籍详情", sa_column_exclude=True)


@ui_config(
    module_name="读书笔记",
    layout=["book_id", "user_id", "page_no", "highlight_color", "is_private", "note_content", "highlight_rects"],
    page_actions=[StandardAdd(dialog_width="1000px")],
    row_actions=[StandardDetail(dialog_width="1000px"), StandardEdit(dialog_width="1000px")]
)
class TriHeartBookNoteModel(StringPKeyModel, table=True):
  __tablename__ = "triheart_book_note"

  book_id: Annotated[
    str | None,
    FieldOption(
        table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, required=True, search_required=True, span=12, component=UIComponent.SELECT_V2,
        data_option=DataOption(model_cls=TriHeartBookModel, method="POST", path="/query/all", label_field="book_title", value_field="model_id")
    ),
    EnableQuery(query_type=QueryType.EQ)
  ] = ExtraSQLModelField(
      description="所属书籍",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "book_id", "comment": "所属书籍"}
  )

  user_id: Annotated[
    str,
    FieldOption(show=False, search_show=False, detail_show=True, component=UIComponent.INPUT),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="用户ID",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "user_id", "comment": "用户ID"}
  )

  page_no: Annotated[
    int | None,
    FieldOption(
        span=5, search_span=6, component=UIComponent.SELECT_V2,
        data_option=DataOption(model_cls=TriHeartPageModel, cascade_field="book_id", lazy_load=False, method="POST", path="/query/all", label_field="page_no", value_field="page_no")
    ),
    EnableQuery(query_type=QueryType.EQ)
  ] = ExtraSQLModelField(
      description="书页页码",
      sa_type=Integer, index=True,
      sa_column_kwargs={"name": "page_no", "comment": "书页页码"}
  )

  note_content: Annotated[
    str,
    FieldOption(component=UIComponent.TEXTAREA, component_props={"rows": 6}, table_show=True, search_show=False),
    EnableQuery(query_type=QueryType.LIKE)
  ] = SQLModelField(
      description="笔记内容",
      sa_type=Text, nullable=False,
      sa_column_kwargs={"name": "note_content", "comment": "笔记内容"}
  )

  # 笔记是否私密（可选扩展）
  is_private: Annotated[
    str | None,
    FieldOption(component=UIComponent.SELECT, span=5, search_span=6),
    Dictionary(store_type=StoreType.DICTIONARY_VALUE, dictionary_type="yes_no"),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="是否私密",
      default="1",  # 默认私密
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "is_private", "comment": "是否私密"}
  )

  highlight_rects: Annotated[
    list | None,
    FieldOption(label="笔记高亮区域坐标列表，JSON格式：[[x, y, w, h], ...]", table_show=False, add_show=True, edit_show=True, detail_show=True, span=12, component=UIComponent.JSON_EDITOR, component_props={"rows": 6})
  ] = SQLModelField(
      default=None, description="笔记高亮区域坐标列表",
      sa_type=JSON, nullable=True,
      sa_column_kwargs={"name": "highlight_rects", "comment": "笔记高亮区域坐标列表"}
  )

  highlight_color: Annotated[
    str | None,
    FieldOption(
        table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=False, span=2, required=False, component=UIComponent.COLOR_PICKER,
        component_props=FieldOption.ColorPickerComponentProps(showAlpha=True, colorFormat="hex", style={"width": "32px"})
    ),
  ] = SQLModelField(
      description="高亮颜色",
      sa_type=String, max_length=32, nullable=True,
      sa_column_kwargs={"name": "highlight_color", "comment": "高亮颜色"}
  )

  crop_mode: Annotated[
    bool | None,
    FieldOption(table_show=False, add_show=False, edit_show=False, detail_show=False, search_show=False)
  ] = ExtraSQLModelField(
      description="切边图模式", sa_column_exclude=True
  )


@ui_config(
    action_column_width=120,
    layout=["book_id", "source_type", "term_key", "term_explanation"],
    page_actions=[StandardAdd(dialog_width="1000px")],
    row_actions=[
      StandardDetail(), StandardEdit(dialog_width="1000px")
    ]
)
class TriHeartTermModel(StringPKeyModel, table=True):
  """术语定义表"""
  __tablename__ = "triheart_term"
  __table_args__ = (
    # 同一本书下术语不能重复
    UniqueConstraint('term_key', 'book_id', name='triheart_term_unique_1'),
  )

  book_id: Annotated[
    str | None,
    FieldOption(
        table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, required=True, search_required=True, span=12, component=UIComponent.SELECT,
        data_option=DataOption(model_cls=TriHeartBookModel, method="POST", path="/query/all", label_field="book_title", value_field="model_id")
    ),
    EnableQuery(query_type=QueryType.EQ)
  ] = ExtraSQLModelField(
      description="所属书籍",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "book_id", "comment": "所属书籍"}
  )

  source_type: Annotated[
    str | None,
    Dictionary(store_type=StoreType.DICTIONARY_VALUE, dictionary_type="term_source_type", display_field_name="source_type_display"),
    FieldOption(table_show=True, required=True, search_required=False, span=6, component=UIComponent.SELECT),
    EnableQuery(query_type=QueryType.EQ)

  ] = SQLModelField(
      default="1", description="术语来源",
      sa_type=String, max_length=36,
      sa_column_kwargs={"name": "source_type", "comment": "术语来源"}
  )

  source_type_display: Annotated[
    str,
    FieldOption(table_show=False, add_show=False, edit_show=False, detail_show=False, search_show=False)
  ] = ExtraSQLModelField(
      description="书术语来源显示", sa_column_exclude=True
  )

  term_key: Annotated[
    str | None,
    FieldOption(table_show=True, required=True, search_required=False, span=6, component=UIComponent.INPUT),
    EnableQuery(query_type=QueryType.LIKE)
  ] = SQLModelField(
      default=None, description="术语关键词",
      sa_type=String, max_length=64, index=True, nullable=False,
      sa_column_kwargs={"name": "term_key", "comment": "术语关键词"}
  )

  term_explanation: Annotated[
    str | None,
    FieldOption(table_show=False, required=True, span=24, component=UIComponent.TEXTAREA, component_props={"rows": 5})
  ] = SQLModelField(
      default=None, description="术语释义",
      sa_type=Text, nullable=False,
      sa_column_kwargs={"name": "term_explanation", "comment": "术语释义"}
  )


@ui_config(
    action_column_width=120,
    layout=["book_id", "page_no", "term_id", "rects_json"],
    page_actions=[StandardAdd(dialog_width="1000px")],
    row_actions=[
      StandardDetail(), StandardEdit(dialog_width="1000px")
    ]
)
class TriHeartPageTermModel(StringPKeyModel, table=True):
  """术语-页面 坐标关联表 (机器生成，无需 UI Config)"""
  __tablename__ = "triheart_page_term"

  book_id: Annotated[
    str | None,
    FieldOption(
        table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, search_required=True, span=12, search_span=8, component=UIComponent.SELECT_V2,
        data_option=DataOption(model_cls=TriHeartBookModel, method="POST", path="/query/all", label_field="book_title", value_field="model_id")
    ),
    EnableQuery(query_type=QueryType.EQ)
  ] = ExtraSQLModelField(
      description="所属书籍",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "book_id", "comment": "所属书籍"}
  )

  page_no: Annotated[
    int | None,
    FieldOption(
        span=6, search_span=3, component=UIComponent.SELECT_V2,
        data_option=DataOption(model_cls=TriHeartPageModel, cascade_field="book_id", lazy_load=False, method="POST", path="/query/all", label_field="page_no", value_field="page_no")
    ),
    EnableQuery(query_type=QueryType.EQ)
  ] = ExtraSQLModelField(
      description="书页页码",
      sa_type=Integer, index=True,
      sa_column_kwargs={"name": "page_no", "comment": "书页页码"}
  )

  term_id: Annotated[
    str | None,
    FieldOption(
        table_show=True, span=6, search_span=7, component=UIComponent.SELECT_V2,
        data_option=DataOption(model_cls=TriHeartTermModel, cascade_field="book_id", lazy_load=False, method="POST", path="/query/all", label_field="term_key", value_field="model_id")
    ),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="书籍术语",
      sa_type=String, max_length=36, index=True,
      sa_column_kwargs={"name": "term_id", "comment": "书籍术语"}
  )

  term_key: Annotated[
    str | None,
    FieldOption(show=False)
  ] = ExtraSQLModelField(description="术语关键字", sa_column_exclude=True)

  term_explanation: Annotated[
    str | None,
    FieldOption(show=False)
  ] = ExtraSQLModelField(
      default=None, description="术语释义", sa_column_exclude=True
  )
  # 存储坐标列表 (JSON 字符串)
  # 格式: [[x, y, w, h], [x, y, w, h]] (百分比 0.0 ~ 1.0, 相对于原图)
  rects_json: Annotated[
    list | None,
    FieldOption(label="术语坐标列表，JSON格式：[[x, y, w, h], [x, y, w, h]]", table_show=False, span=24, component=UIComponent.JSON_EDITOR, component_props={"rows": 4})
  ] = SQLModelField(
      default=None, description="术语坐标列表",
      sa_type=JSON, nullable=False,
      sa_column_kwargs={"name": "rects_json", "comment": "术语坐标列表"}
  )


@ui_config(
    module_name="页面附件管理", action_column_width=150,
    layout=[
      "book_id", "page_no", "display_name", "attachment_type", "file_path", "extra_data",
      FieldOption(prop="create_person", table_show=False, add_show=False, edit_show=False, search_show=False, detail_show=False, span=6),
      FieldOption(prop="create_timestamp", table_show=False, add_show=False, edit_show=False, search_show=False, span=6),
      FieldOption(prop="update_person", table_show=False, add_show=False, edit_show=False, search_show=False, detail_show=False, span=6),
      FieldOption(prop="update_timestamp", table_show=False, add_show=False, edit_show=False, search_show=False, span=6)
    ],
    page_actions=[StandardAdd(dialog_width="1000px")],
    row_actions=[StandardDetail(dialog_width="1000px"), StandardEdit(dialog_width="1000px"), StandardDelete()]
)
class TriHeartPageAttachmentModel(StringPKeyModel, table=True):
  __tablename__ = "triheart_page_attachment"
  __table_args__ = (
    # 同一页面下，附件名称不能重复
    UniqueConstraint('book_id', 'page_no', 'display_name', name='triheart_page_attachment_unique_1'),
  )

  book_id: Annotated[
    str | None,
    FieldOption(
        table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, required=True, search_required=True, span=18, search_span=8,
        component=UIComponent.SELECT_V2,
        data_option=DataOption(model_cls=TriHeartBookModel, method="POST", path="/query/all", label_field="book_title", value_field="model_id")
    ),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="所属书籍",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "book_id", "comment": "所属书籍"}
  )

  page_no: Annotated[
    int | None,
    FieldOption(
        table_show=True, add_show=True, edit_show=True, detail_show=True, search_show=True, required=True, search_required=False, span=6, search_span=4,
        component=UIComponent.SELECT_V2,
        data_option=DataOption(model_cls=TriHeartPageModel, cascade_field="book_id", lazy_load=False, method="POST", path="/query/all", label_field="page_no", value_field="page_no")
    ),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="所属页码",
      sa_type=Integer, nullable=False,
      sa_column_kwargs={"name": "page_no", "comment": "所属页码"}
  )

  display_name: Annotated[
    str | None,
    FieldOption(table_show=True, required=True, search_required=False, span=18, search_span=8, component=UIComponent.INPUT),
    EnableQuery(query_type=QueryType.LIKE)
  ] = SQLModelField(
      description="附件显示名称",
      sa_type=String, max_length=128, nullable=False,
      sa_column_kwargs={"name": "display_name", "comment": "附件显示名称"}
  )

  attachment_type: Annotated[
    str | None,
    Dictionary(store_type=StoreType.DICTIONARY_VALUE, dictionary_type="page_attachment_type", display_field_name="attachment_type_display"),
    FieldOption(table_show=True, required=True, search_required=False, span=6, search_span=4, component=UIComponent.SELECT),
    EnableQuery(query_type=QueryType.EQ)
  ] = SQLModelField(
      description="附件类型",
      sa_type=String, max_length=36, nullable=False,
      sa_column_kwargs={"name": "attachment_type", "comment": "附件类型"}
  )
  attachment_type_display: Annotated[
    str,
    FieldOption(table_show=False, add_show=False, edit_show=False, detail_show=False, search_show=False)
  ] = ExtraSQLModelField(description="附件类型显示", sa_column_exclude=True)

  file_path: Annotated[
    str | None,
    FieldOption(
        table_show=False, add_show=True, edit_show=True, detail_show=True, search_show=False, span=24,
        component=UIComponent.UPLOAD, component_props=FieldOption.UploadComponentProps(accept="audio/*,video/*,.zip,.rar,.tar,.gz,.txt,.py,.js,.java,.go,.cpp", max_size=50, limit=1)
    )
  ] = SQLModelField(
      description="附件文件路径 (OSS)",
      sa_type=String, max_length=256, nullable=False,
      sa_column_kwargs={"name": "file_path", "comment": "附件文件路径"}
  )

  extra_data: Annotated[
    dict[str, Any] | None,
    FieldOption(table_show=False, add_show=True, edit_show=True, detail_show=True, span=24, component=UIComponent.JSON_EDITOR, label="额外数据 (如视频封面、代码语言等)")
  ] = SQLModelField(
      default={}, description="额外数据 (JSON)",
      sa_type=JSON, nullable=True,
      sa_column_kwargs={"name": "extra_data", "comment": "额外数据 (JSON)"}
  )
