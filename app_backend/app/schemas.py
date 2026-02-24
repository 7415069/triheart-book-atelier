# /app/schemas.py
from typing import Annotated, Any

from brtech_backend.core.annotations import FieldOption
from brtech_backend.core.models import M
from brtech_backend.core.schemas import StringPKeyRecurseQuery, StringPKeyQuery
from pydantic import Field
from sqlalchemy import Select, asc, desc, or_

from .models import TriHeartBookModel, TriHeartChapterModel, TriHeartPageModel, TriHeartChapterPageModel, TriHeartBookNoteModel, TriHeartBookUserModel, TriHeartTermModel, TriHeartPageTermModel, TriHeartPageAttachmentModel


class TriHeartBookQuery(StringPKeyQuery[TriHeartBookModel]):
  # 1. 定义混合查询字段
  mixed_input: Annotated[
    str | None,
    FieldOption(show=False, search_show=False)
  ] = Field(default=None, description="混合查询输入(书名/作者/ISBN)")

  # 2. 定义分类列表字段
  book_categories: Annotated[
    list[str] | None,
    FieldOption(show=False, search_show=False)
  ] = Field(default=None, description="书籍分类列表")

  def __init__(self, /, **data: Any) -> None:
    super().__init__(**data)
    # 告诉框架不要自动处理这两个字段，我们要自己在 custom_spec 里处理
    self._skip_fields.add("mixed_input")
    self._skip_fields.add("book_categories")

  def custom_spec(self, stmt: Select, model: type[TriHeartBookModel]) -> Select:
    stmt = super().custom_spec(stmt, model)

    if self.mixed_input:
      # 使用 or_ 实现：标题 包含 OR 作者 包含 OR 副标题 包含
      # 注意：这里必须用 model.book_title，不能用 model.name
      stmt = stmt.where(or_(
          model.book_title.like(f"%{self.mixed_input}%"),
          model.book_author.like(f"%{self.mixed_input}%"),
          model.book_subtitle.like(f"%{self.mixed_input}%")
      ))

    if self.book_categories:
      # 前端传数组过来，这里用 in_ 查询
      stmt = stmt.where(model.book_category.in_(self.book_categories))

    return stmt


class TriHeartChapterQuery(StringPKeyRecurseQuery[TriHeartChapterModel]):

  def apply_sorting(self, stmt: Select, model: type[M]) -> Select:
    return stmt.order_by(asc(getattr(model, 'from_page_no')))


class TriHeartPageQuery(StringPKeyQuery[TriHeartPageModel]):
  begin_page_no: Annotated[
    int | None,
    FieldOption(show=False, search_show=True, search_span=6)
  ] = Field(default=None, description="开始页码")

  end_page_no: Annotated[
    int | None,
    FieldOption(show=False, search_show=True, search_span=6)
  ] = Field(default=None, description="结束页码")

  page_numbers: Annotated[
    list[int] | None,
    FieldOption(show=False, search_show=False, search_span=4)
  ] = Field(default=None, description="页码列表")

  def __init__(self, /, **data: Any) -> None:
    super().__init__(**data)
    self._skip_fields.add('begin_page_no')
    self._skip_fields.add('end_page_no')
    self._skip_fields.add('page_numbers')

  def custom_spec(self, stmt: Select, model: type[TriHeartPageModel]) -> Select:
    stmt: Select = super().custom_spec(stmt, model)
    if self.begin_page_no:
      stmt = stmt.where(model.page_no >= self.begin_page_no)  # type: ignore
    if self.end_page_no:
      stmt = stmt.where(model.page_no <= self.end_page_no)  # type: ignore
    if self.page_numbers:
      stmt = stmt.where(model.page_no.in_(self.page_numbers))  # type: ignore
    return stmt

  def apply_sorting(self, stmt: Select, model: type[M]) -> Select:
    return stmt.order_by(asc(getattr(model, 'page_no')))


class TriHeartChapterPageQuery(StringPKeyQuery[TriHeartChapterPageModel]):
  pass


class TriHeartBookUserQuery(StringPKeyQuery[TriHeartBookUserModel]):

  def apply_sorting(self, stmt: Select, model: type[M]) -> Select:
    return stmt.order_by(desc(getattr(model, 'purchase_status')), desc(getattr(model, 'last_read_time')))


class TriHeartBookNoteQuery(StringPKeyQuery[TriHeartBookNoteModel]):
  image_mode: Annotated[
    str | None,
    FieldOption(show=False, search_show=False)
  ] = Field(default=None, description="图片模式：crop; origin")

  def __init__(self, /, **data: Any) -> None:
    super().__init__(**data)
    self._skip_fields.add('image_mode')

  def apply_sorting(self, stmt: Select, model: type[M]) -> Select:
    # 按照页码和创建时间升序排列，方便前端展示
    return stmt.order_by(asc(getattr(model, 'book_id')), asc(getattr(model, 'page_no')), asc(getattr(model, 'create_timestamp')))


class TriHeartTermQuery(StringPKeyQuery[TriHeartTermModel]):
  pass


class TriHeartPageTermQuery(StringPKeyQuery[TriHeartPageTermModel]):
  begin_page_no: Annotated[
    int | None,
    FieldOption(show=False, search_show=True, search_span=3)
  ] = Field(default=None, description="开始页码")

  end_page_no: Annotated[
    int | None,
    FieldOption(show=False, search_show=True, search_span=3)
  ] = Field(default=None, description="结束页码")

  image_mode: Annotated[
    str | None,
    FieldOption(show=False)
  ] = Field(default=None, description="图片模式")

  def __init__(self, /, **data: Any) -> None:
    super().__init__(**data)
    self._skip_fields.add('begin_page_no')
    self._skip_fields.add('end_page_no')
    self._skip_fields.add('image_mode')

  def custom_spec(self, stmt: Select, model: type[TriHeartPageTermModel]) -> Select:
    stmt: Select = super().custom_spec(stmt, model)
    if self.begin_page_no:
      stmt = stmt.where(model.page_no >= self.begin_page_no)  # type: ignore
    if self.end_page_no:
      stmt = stmt.where(model.page_no <= self.end_page_no)  # type: ignore
    return stmt

  def apply_sorting(self, stmt: Select, model: type[M]) -> Select:
    return stmt.order_by(asc(getattr(model, 'book_id')), asc(getattr(model, 'page_no')))


class TriHeartPageAttachmentQuery(StringPKeyQuery[TriHeartPageAttachmentModel]):
  pass
