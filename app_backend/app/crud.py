# /app/crud.py
from brtech_backend.core.crud import StringPKeyCrud, StringPKeyRecurseCrud
from sqlalchemy import delete, select, and_, Row

from .models import TriHeartBookModel, TriHeartChapterModel, TriHeartPageModel, TriHeartChapterPageModel, TriHeartBookUserModel, TriHeartBookNoteModel, TriHeartTermModel, TriHeartPageTermModel, TriHeartPageAttachmentModel


class TriHeartBookCrud(StringPKeyCrud[TriHeartBookModel]):
  pass


class TriHeartChapterCrud(StringPKeyRecurseCrud[TriHeartChapterModel]):
  async def remove_by_book_id(self, book_id: str) -> int:
    """根据 book_id 删除章节，返回删除数量"""
    if not book_id:
      return 0
    # 使用 returning 确认删除行数 (Postgres支持，MySQL低版本可能不支持，若不支持可改用 rowcount)
    stmt = delete(self.model).where(getattr(self.model, 'book_id') == book_id).returning(getattr(self.model, 'model_id'))
    result = await self.db.execute(stmt)
    return len(result.scalars().all())


class TriHeartPageCrud(StringPKeyCrud[TriHeartPageModel]):
  async def remove_by_book_id(self, book_id: str) -> int:
    """根据 book_id 删除书页，返回删除数量"""
    if not book_id:
      return 0
    stmt = delete(self.model).where(getattr(self.model, 'book_id') == book_id).returning(getattr(self.model, 'model_id'))
    result = await self.db.execute(stmt)
    return len(result.scalars().all())

  async def remove_by_chapter_id(self, chapter_id: str) -> int:
    """根据 chapter_id 删除书页，返回删除数量"""
    if not chapter_id:
      return 0
    stmt = delete(self.model).where(getattr(self.model, 'chapter_id') == chapter_id).returning(getattr(self.model, 'model_id'))
    result = await self.db.execute(stmt)
    return len(result.scalars().all())

  async def custom_query_book_user_page(self, book_id: str, user_id: str | None, page_no: int) -> Row | None:
    stmt = (
      select(
          # 1. Page 表字段
          TriHeartPageModel.page_image_path,
          TriHeartPageModel.page_image_crop_path,
          # 2. Book 表字段
          TriHeartBookModel.guest_preview_limit,
          TriHeartBookModel.user_preview_limit,
          # 3. User Relation 表字段
          TriHeartBookUserModel.purchase_status
      )
      .join(TriHeartBookModel, TriHeartPageModel.book_id == TriHeartBookModel.model_id)
      .outerjoin(TriHeartBookUserModel, and_(TriHeartBookUserModel.book_id == TriHeartPageModel.book_id, TriHeartBookUserModel.user_id == user_id))
      .where(TriHeartPageModel.book_id == book_id, TriHeartPageModel.page_no == page_no)
    )

    result = await self.db.execute(stmt)
    return result.first()


class TriHeartChapterPageCrud(StringPKeyCrud[TriHeartChapterPageModel]):
  pass


class TriHeartBookUserCrud(StringPKeyCrud[TriHeartBookUserModel]):
  pass


class TriHeartBookNoteCrud(StringPKeyCrud[TriHeartBookNoteModel]):
  pass


class TriHeartTermCrud(StringPKeyCrud[TriHeartTermModel]):
  async def get_by_book_id(self, book_id: str) -> list[TriHeartTermModel]:
    """查询全局术语 + 该书专用术语"""
    stmt = select(self.model).where(
        (self.model.book_id == book_id) | (self.model.book_id.is_(None)) | (self.model.book_id == '')
    )
    return await self.select_all(stmt)


class TriHeartPageTermCrud(StringPKeyCrud[TriHeartPageTermModel]):
  async def remove_by_book_id(self, book_id: str) -> int:
    if not book_id: return 0
    stmt = delete(self.model).where(getattr(self.model, 'book_id') == book_id)
    await self.db.execute(stmt)
    return 0

  async def get_by_page_no(self, book_id: str, page_no: int) -> list[TriHeartPageTermModel]:
    stmt = select(self.model).where(self.model.book_id == book_id, self.model.page_no == page_no)
    return await self.select_all(stmt)


class TriHeartPageAttachmentCrud(StringPKeyCrud[TriHeartPageAttachmentModel]):
  pass
