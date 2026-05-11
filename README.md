# 三心书坊 (TriHeart Book Atelier)

> 硬核技术书籍的沉浸式数字阅读与创作平台 —— 让创作安心、省心、有利心；使阅读舒心、会心、能定心。

**网站地址**: [https://thba.brtech.top](https://thba.brtech.top)

---

## 项目愿景

**三心书坊** 是为技术书籍作者和深度阅读者打造的一站式平台，核心解决三大痛点：

| 角色 | 痛点 | 解决方案 |
| :--- | :--- | :--- |
| **创作者** | PDF 易被盗版传播，移动端排版差 | PyMuPDF 矢量切片 → WebP 物理切片 + 流式签名 URL，不暴露原始 PDF |
| **阅读者** | 专业术语频繁查阅打断思路 | DeepSeek AI 提取术语 + 坐标扫描，术语释义"缝合"到书页，即点即看 |
| **开发者** | 中后台 CRUD 占 70% 开发时间 | Brtech Fusion 低代码底座，注解驱动自动生成管理界面 |

本项目是 **Brtech Fusion 底座** 的标杆级应用，展示了如何利用底座能力在极短时间内构建包含 PDF 矢量解析、AI 知识提取、3D 阅读引擎及复杂支付体系的全栈系统。

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                     │
│  Element Plus + Pinia + Vue Router + brtech-fusion SDK  │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌─────────┐  │
│  │  Portal  │ │  Shelf   │ │ Reader v4  │ │  Admin  │  │
│  │  门户首页 │ │  书架浏览  │ │  3D 阅读器  │ │  管理后台  │  │
│  └──────────┘ └──────────┘ └────────────┘ └─────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │ /thba/backend/*
┌──────────────────────┴──────────────────────────────────┐
│                  Backend (FastAPI)                      │
│          Brtech Fusion Low-Code Platform                │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ PDF 引擎  │ │ AI 中心  │ │ 视频渲染  │ │ 支付体系   │  │
│  │ PyMuPDF  │ │ DeepSeek │ │ MoviePy  │ │ Alipay/   │  │
│  │ WebP切片  │ │ 术语提取  │ │ Edge-TTS │ │ WechatPay │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ 4A 权限  │ │ 异步任务  │ │ CDN 签名 │ │ 字典/配置  │  │
│  │ 认证授权  │ │ Task Mgr │ │ URL防盗链 │ │ 数据字典   │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│                   Data & Storage                        │
│  PostgreSQL / MySQL  │  MinIO / Aliyun OSS  │  Redis    │
└─────────────────────────────────────────────────────────┘
```

---

## 技术栈

| 层级 | 技术 | 说明 |
| :--- | :--- | :--- |
| **后端框架** | FastAPI + Brtech Fusion | 低代码底座，注解驱动 CRUD |
| **数据库** | PostgreSQL / MySQL (via SQLAlchemy 2.0 + SQLModel) | asyncpg 异步驱动 |
| **对象存储** | MinIO / 阿里云 OSS | 图片、视频、附件存储 |
| **PDF 处理** | PyMuPDF 1.26 | 页面渲染为 WebP，智能裁剪，护眼染色 |
| **AI 服务** | DeepSeek R1/V3 (via OpenAI SDK) | 术语提取、视频脚本生成 |
| **视频渲染** | MoviePy + FFmpeg | Ken Burns 运镜特效，音视频合成 |
| **语音合成** | Edge-TTS | 微软免费 TTS，音质接近真人 |
| **CDN 鉴权** | EdgeOne / Gcore | 签名 URL，防盗链 |
| **支付** | 支付宝 / 微信支付 | 底座统一支付弹窗 + 自动分发 |
| **前端框架** | Vue 3 + TypeScript | Composition API |
| **UI 组件** | Element Plus | 管理后台 + 阅读器 UI |
| **状态管理** | Pinia | 用户认证状态 |
| **构建工具** | Vite 7 | 开发服务器 + 生产构建 |
| **代码规范** | ESLint + Prettier | 代码格式化和检查 |

---

## 项目结构

```
triheart_book_atelier/
├── app_backend/                    # Python 后端
│   ├── main.py                     # 应用入口，注册路由/中间件/存储
│   ├── requirements.in             # 直接依赖声明
│   ├── requirements.txt            # 锁定依赖 (uv pip compile)
│   ├── .env                        # 环境变量配置
│   ├── fixtures/                   # 启动自动加载的种子数据
│   │   ├── dictionaries.json       #   数据字典
│   │   ├── roles.json              #   角色/权限
│   │   ├── users.json              #   默认用户
│   │   └── menus.json              #   菜单结构
│   └── app/
│       ├── config.py               # 配置类 (DB/OSS/AI/CDN/TTS/Video)
│       ├── models.py               # 9 个 SQLModel 数据模型 + @ui_config 注解
│       ├── schemas.py              # 查询 Schema (自定义 SQL 查询)
│       ├── crud.py                 # 数据库访问层 (含 JOIN 权限查询)
│       ├── services.py             # 核心业务逻辑 (500+ 行)
│       ├── routers.py              # API 路由 (自定义端点 + 底座 CRUD)
│       ├── ai_helper.py            # DeepSeek API 客户端
│       ├── pdf_helper.py           # PyMuPDF PDF 处理引擎
│       ├── tts_helper.py           # Edge-TTS 语音合成
│       ├── video_script_helper.py  # AI 视频脚本生成
│       └── video_renderer.py       # MoviePy 视频渲染引擎
│
├── app_frontend/                   # Vue 3 前端
│   ├── package.json                # 依赖: Vue 3, Element Plus, brtech-fusion
│   ├── vite.config.ts              # Vite 配置 (proxy /thba/backend → :9988)
│   └── src/
│       ├── main.ts                 # 应用入口
│       ├── App.vue                 # 根组件
│       ├── router/index.ts         # 路由: /, /reader/:bookId/:pageNo?, /login, /admin/*
│       ├── stores/user.ts          # Pinia 用户状态
│       ├── api/                    # API 调用封装
│       │   ├── portal/index.ts     #   门户 API
│       │   ├── reader/index.ts     #   阅读器 API
│       │   └── shelf/index.ts      #   书架 API
│       ├── components/
│       │   ├── portal/Header.vue   #   网站头部
│       │   ├── shelf/              #   书架组件 (Card/Grid/Row)
│       │   └── reader/
│       │       ├── v1/             #   初版 (基础页面)
│       │       ├── v2/             #   第二版 (3D 基础)
│       │       ├── v3/             #   第三版 (3D 优化)
│       │       └── v4/             #   生产版 (完整 3D 书模)
│       │           ├── Book3DEngine.vue    # 3D 渲染主引擎
│       │           ├── Book3DLeaf.vue      # 单页叶片
│       │           ├── BookPage.vue        # 页面内容 + 术语标注
│       │           ├── BookReader.vue      # 阅读器容器
│       │           ├── LeafSegment.vue     # 翻页分段形变
│       │           ├── GroundPlane.vue     # 3D 桌面平面
│       │           ├── VideoGuidePlayer.vue # 视频导读播放器
│       │           └── types.ts           # 类型定义
│       └── views/
│           ├── portal/             #   门户页面 (首页/书架/书籍详情)
│           ├── space/Bookshelf.vue  #   个人书架
│           ├── admin/Index.vue     #   管理后台壳
│           └── Login.vue           #   登录页
│
└── app_doc/                        # 文档
```

---

## 数据模型

| 模型 | 表名 | 说明 |
| :--- | :--- | :--- |
| `TriHeartBookModel` | `triheart_book` | 书籍元数据 (标题/作者/ISBN/价格/试读限制/解析状态) |
| `TriHeartChapterModel` | `triheart_chapter` | 章节树 (支持递归父子结构，关联起止页码) |
| `TriHeartPageModel` | `triheart_page` | 书页 (WebP 原图/裁剪图路径，页面文本内容，切边参数) |
| `TriHeartChapterPageModel` | `triheart_chapter_page` | 章节-页面 多对多关联 |
| `TriHeartBookUserModel` | `triheart_book_user` | 用户书架 (购买状态/最后阅读页码/时间) |
| `TriHeartBookNoteModel` | `triheart_book_note` | 读书笔记 (高亮坐标/颜色/内容/私密标记) |
| `TriHeartTermModel` | `triheart_term` | 术语定义 (关键词/释义/来源) |
| `TriHeartPageTermModel` | `triheart_page_term` | 术语-页面 坐标关联 (百分比坐标 JSON) |
| `TriHeartChapterVideoModel` | `triheart_chapter_video` | 章节视频导读 (脚本/视频路径/音色/时长/状态) |

**通用字段**: 所有模型继承 `StringPKeyModel`，自带 UUID 主键、`create_person`、`create_timestamp`、`update_person`、`update_timestamp`、`remark`。

---

## 核心功能

### 1. PDF 书籍解析引擎 (`pdf_helper.py` + `services.py`)

- **WebP 矢量切片**: 将 PDF 每页渲染为 WebP 图片，采用 method 6 强力压缩，平衡画质与加载速度
- **智能裁剪**: 自动检测页面内容 BBox，去除冗余白边，提升移动端阅读面积利用率
- **护眼染色**: 正片叠底算法，降低纯白背景的视觉疲劳
- **目录树提取**: 自动递归提取 PDF 原生目录 (TOC)，同步至数据库章节表
- **异步任务追踪**: 底座 `TaskRecord` 体系提供实时进度条，后台线程池处理 CPU 密集型渲染

### 2. AI 术语中心 (`ai_helper.py`)

- **DeepSeek 集成**: 利用大模型长上下文能力，精准识别领域关键词并生成释义
- **坐标自动化**: 扫描全书文本，将 AI 返回的术语映射到页面图像像素坐标
- **即点即看**: 前端点击术语高亮区域，弹出释义浮窗，无需跳出阅读流程

### 3. 3D 阅读引擎 — Reader v4 (`components/reader/v4/`)

- **物理仿真翻页**: 自研 `LeafSegment` 组件实现书页微弧度形变，模拟真实翻书质感
- **书块厚度模型**: 动态计算左右页堆叠厚度 (Z-index 视觉差)，还原书籍物理厚度
- **双模式阅读**: Spread (双页扩展) / Single (单页模式)
- **术语交互**: 页面上直接标注术语高亮区域，点击查看释义
- **附件伴读**: 支持代码/音频/视频等附件下载和播放

### 4. AI 章节视频导读系统 (`video_script_helper.py` + `tts_helper.py` + `video_renderer.py`)

- **AI 导演**: 多模态 AI 分析书页图片，自动生成包含旁白、运镜指令、聚焦区域的 JSON 脚本
- **语音合成**: Edge-TTS 将旁白转为自然语音，支持多种中文音色
- **动态视频渲染**: MoviePy 实现 Ken Burns 效果 (平移/缩放)，叠加字幕和半透明高亮块
- **章节级生成**: 以章节为单位，一键生成短视频，支持移动端快速消费和社交分发

### 5. 支付与版权保护 (`services.py`)

- **CDN 签名 URL**: 支持 EdgeOne 和 Gcore CDN 提供商，Token 鉴权防盗链
- **试读控制**: 游客试读页数 (`guest_preview_limit`) 和注册用户试读页数 (`user_preview_limit`) 可配置
- **支付自动分发**: 继承 `PaymentServiceMixin`，支付成功后自动将书籍加入用户书架
- **微信/支付宝**: 底座统一收银台弹窗

---

## 低代码底座开发范式

本项目深度展示了 Brtech Fusion 底座的核心开发模式：

### 注解驱动 UI (`@ui_config`)

在 `models.py` 中通过注解声明管理后台界面，无需编写前端代码：

```python
@ui_config(
    module_name="书籍管理",
    layout=["book_title", "book_author", "book_cover", ...],
    row_actions=[
        Action(code="read", label="阅读", type=ActionType.LINK,
               router_path="/reader/{bookId}/{pageNo}"),
        Action(code="parse", label="书籍解析", type=ActionType.API,
               api_url="/book/parse/{modelId}", method="POST"),
        StandardEdit(dialog_width="1200px"),
    ]
)
class TriHeartBookModel(StringPKeyModel, table=True): ...
```

### 通用 CRUD 路由

继承 `StringPKeyRouter[Model, Crud, Query, Service]` 即可自动获得完整的 RESTful API (增删改查/分页/排序/搜索)，自定义端点通过 `_register_routes()` 添加。

### 异步任务框架

耗时操作 (PDF 解析、AI 提取、视频渲染) 通过底座 `task_manager.create_task()` 创建任务，线程池中执行，`update_progress()` 实时更新进度。

### 业务 Mixin 与支付分发

支付成功后底座根据 `business_type` 自动定位到 `PaymentServiceMixin.resolve_pay_order()`，无需在支付模块写 `if-else`。

### 坐标转换 Mixin

后端存储基于原图的百分比坐标，前端请求带 `imageMode=crop` 时，`PageRectsMixinService` 自动根据 `crop_box_data` 进行仿射变换。

---

## 开发指南

### 环境要求

- Python 3.11+
- Node.js 20+
- PostgreSQL (推荐) 或 MySQL
- MinIO 或阿里云 OSS

### 后端启动

```bash
cd app_backend

# 创建虚拟环境
uv venv --python 3.11
source .venv/bin/activate


# 安装依赖
uv pip compile requirements.in -o requirements.txt
uv pip install -r requirements.txt
uv pip install pex

# 配置环境变量 (参考 app/config.py)
cp .env.example .env   # 编辑数据库连接、OSS 配置等

# 启动 (端口 9988)
python main.py
```

启动后底座自动扫描 `fixtures/` 目录加载种子数据（字典、角色、用户、菜单、权限）。

### 前端启动

```bash
cd app_frontend

# 安装依赖 (需要 brtech-fusion 本地包)
npm install

# 开发模式 (端口 5173, 代理 /thba/backend → :9988)
npm run dev

# 生产构建 (输出到 app_backend/static/)
npm run build

# 代码检查与格式化
npm run lint
npm run format
```

### 整体打包
```bash
cd app_frontend && nvm use 20 && npm install && npm run build
cd app_backend && ./build_pex.sh
```

### URL 结构

| 路径 | 说明 |
| :--- | :--- |
| `/thba/backend/...` | API 端点 |
| `/thba/frontend/...` | 前端页面 |
| `/thba/frontend/admin/...` | 管理后台 |
| `/thba/frontend/reader/:bookId/:pageNo?` | 阅读器 |

`CONTEXT_PATH`、`API_PREFIX`、`UI_PATH` 可通过 `config.py` 配置。

---

## API 端点概览

| 路由前缀 | 说明 |
| :--- | :--- |
| `/book` | 书籍 CRUD + 自定义: `/parse/{id}` `/extract/{id}` `/scanCoords/{id}` `/webpUrl` `/coverSignUrl` |
| `/chapter` | 章节树 CRUD (递归结构) |
| `/page` | 书页 CRUD |
| `/chapterPage` | 章节-页面关联 |
| `/bookUser` | 用户书架 |
| `/bookNote` | 读书笔记 |
| `/term` | 术语定义 |
| `/pageTerm` | 术语坐标关联 |
| `/pageAttachment` | 页面附件 |
| `/chapterVideo` | 视频导读: `/generate/{id}` 触发生成 |

所有端点通过底座框架自动获得标准 CRUD 操作，自定义端点由 `routers.py` 注册。

---

## 关键约定

- **页码**: 全书统一 1-based
- **坐标**: 百分比 `[x, y, w, h]` (0.0–1.0)，基于原图；请求带 `imageMode=crop` 时自动变换为裁剪图坐标
- **处理状态**: `"0"` 待处理, `"1"` 处理中, `"2"` 成功, `"9"` 失败
- **认证**: `AuthContext` 提供 `user_id`，`None` 表示匿名游客
- **API 调用**: 前端统一使用 `brtech-fusion` SDK 的 `request` 对象

---

## 未来规划

- [ ] **AI 伴读对话**: 基于当前书页内容的 RAG 问答
- [ ] **多端适配**: 移动端原生翻页手势
- [ ] **社交分享**: 读书笔记海报生成
- [ ] **视频导出**: 9:16 竖屏格式，适配抖音/视频号分发
- [ ] **协作批注**: 多用户书页批注与讨论

---

## License

Proprietary. Copyright 三心书坊 (TriHeart Book Atelier).
