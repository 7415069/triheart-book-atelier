# /main.py
import logging
from typing import Any

from brtech_backend import get_session_maker
from brtech_backend.a4.routers import A4UserRouter, A4RoleRouter, A4FuncPermissionRouter, A4DataPermissionRouter, A4RoleUserRouter, A4RoleFuncPermissionRouter, A4RoleDataPermissionRouter
from brtech_backend.a4.scanner import A4PermissionScanner
from brtech_backend.core.application import Application
from brtech_backend.core.config import app_settings
from brtech_backend.core.config import install_all_settings
from brtech_backend.core.routers import Public
from brtech_backend.core.storage import MinioStorageClient, StorageProvider
from brtech_backend.dictionary.routers import DictionaryRouter, DictionaryRouteKey
from brtech_backend.logger.middlewares import OperateLogMiddleware
from brtech_backend.logger.routers import a4_logger_router_classes
from brtech_backend.payment.routers import payment_router_classes
from brtech_backend.task.routers import TaskRecordRouter
from brtech_backend.ui.routers import ui_router_classes

from app.config import MyAppSettings
from app.routers import thba_router_classes

Public(DictionaryRouteKey.QUERY_BY_TYPES)(DictionaryRouter)

logger = logging.getLogger("application")


class MyApplication(Application):

  def __init__(self, settings: Any, router_classes=None, **kwargs):
    install_all_settings(MyAppSettings())
    super().__init__(settings, router_classes, **kwargs)

  def prepare(self):
    super().prepare()

    StorageProvider.set(MinioStorageClient(
        endpoint=app_settings.OSS_ENDPOINT,
        access_key=app_settings.OSS_ACCESS_KEY,
        secret_key=app_settings.OSS_SECRET_KEY,
        bucket_name=app_settings.OSS_BUCKET_NAME,
        secure=app_settings.OSS_SECURE
    ))

    self.app.add_middleware(OperateLogMiddleware)

    self.router_classes.append(DictionaryRouter)
    self.router_classes.extend(a4_logger_router_classes)
    self.router_classes.extend([A4UserRouter, A4RoleRouter, A4FuncPermissionRouter, A4DataPermissionRouter, A4RoleUserRouter, A4RoleFuncPermissionRouter, A4RoleDataPermissionRouter])
    self.router_classes.extend(payment_router_classes)
    self.router_classes.extend(ui_router_classes)
    self.router_classes.extend([TaskRecordRouter])

    self.router_classes.extend(thba_router_classes)

  # def mount_frontend(self):
  #   custom_static_path = "static"
  #
  #   if os.path.exists(custom_static_path) and not os.path.exists("static/index.htm"):
  #     self.app.mount(f"{self.ui_path}/static", StaticFiles(directory=custom_static_path), name=f"{self.ui_path}-static")
  #   super().mount_frontend()

  async def on_startup(self):
    await super().on_startup()
    session_maker = get_session_maker()
    async with session_maker() as db:
      logger.info(">>> [System] 正在自动同步接口权限...")
      await A4PermissionScanner.sync_to_db(self.app, db, self.api_prefix)


creator = MyApplication(app_settings)

# [新增] 必须暴露这个变量，uvicorn 才能通过字符串导入它
app = creator.get_app()

if __name__ == "__main__":
  # [修改] 传入 import string，开启完美的热重载
  # creator.run(app_str="main:app")
  creator.run(app_str="main:app", reload_dirs=["app"], reload=False)
