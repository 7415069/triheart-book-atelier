# app/config.py
from brtech_backend.core.config import AppSettings
from brtech_backend.payment.config import PaySettings


class MyAppSettings(AppSettings, PaySettings):
  # --- 基础配置 ---
  # TITLE: str = "基于FastAPI的Web后端框架"
  TITLE: str = "三心书坊 - 实现知识自由的铲子"
  LOGO: str = "static/favicon.svg"
  VERSION: str = "1.0.0"
  DESCRIPTION: str = "三心书坊 - 接口定义 - OpenAPI 版本"
  # DESCRIPTION: str = "这是我的业务系统"

  LOGIN_TITLE: str = "欢迎使用"
  LOGIN_SUBTITLE: str = TITLE
  LOGIN_LOGO: str = LOGO

  ENABLE_CAPTCHA: bool = False
  ENABLE_REGISTER: bool = True
  ENABLE_FORGOT_PASSWORD: bool = True

  THEME_NAME: str = "light"
  THEME_PRIMARY_COLOR: str = ""
  THEME_BORDER_RADIUS: str = "10px"
  COPYRIGHT: str = "© 2026 博然低代码平台"
  ICP_CODE: str = ""

  # --- 邮件配置 (SMTP) ---
  MAIL_ENABLE: bool = True  # 开发环境默认关闭，只打印控制台
  MAIL_SERVER: str = "smtp.163.com"
  MAIL_PORT: int = 465
  MAIL_USERNAME: str = "7415069@163.com"  # 发件人邮箱
  # MAIL_PASSWORD: str = ""  # 授权码
  MAIL_FROM_NAME: str = "三心书坊"
  # 验证码有效期 (秒)
  MAIL_CODE_EXPIRE: int = 600

  # --- 网络配置 ---
  PORT: int = 9988  # 改这里，启动端口就变了

  # [新增] 日志级别，默认为 INFO
  LOG_LEVEL: str = "INFO"

  # --- 路径配置 ---
  CONTEXT_PATH: str = "/thba"
  UI_PATH: str = "/frontend"
  API_PREFIX: str = "/backend"
  ROOT_PATH: str = ""
  INIT_DATA_DIR: str = "fixtures"

  OSS_ENDPOINT: str = "192.168.0.106:9000"
  OSS_ACCESS_KEY: str = "root"
  OSS_SECRET_KEY: str = "7415069@163.com"
  OSS_BUCKET_NAME: str = "triheart-book"
  OSS_SECURE: bool = False

  AI_API_KEY: str = ""  # 必填：你的 API Key
  AI_BASE_URL: str = "https://api.deepseek.com"  # 例如 DeepSeek 的地址
  AI_MODEL_NAME: str = "deepseek-reasoner"  # 模型名称
  AI_MAX_TOKENS: int = 128000  # 最大 token 数
  AI_ENABLE: bool = True  # 总开关

  # --- 数据库 ---
  # DATABASE_URL: str = "sqlite+aiosqlite:///var/triheart_book_atelier.db"
  DATABASE_URL: str = "postgresql+asyncpg://thba:admin%40thba@localhost:5432/thba"
  JWT_SECRET_KEY: str = ""

  ENABLE_WALLET_PAYMENT: bool = False
  ENABLE_MOCK_PAYMENT: bool = True

  ENABLE_DATA_PERMISSION_VALIDATION: bool = True
  ENABLE_FUNC_PERMISSION_VALIDATION: bool = True

# my_app_settings = MyAppSettings()
