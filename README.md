# 📖 三心书坊 (TriHeart Book Atelier)

---
## ⭕ 项目愿景

### —— 网站地址: https://thba.brtech.top

### —— 实现知识自由的铲子

**三心书坊** 是一款专注于硬核技术书籍、学术著作的沉浸式数字阅读与创作平台。其核心理念是：**让创作安心（防盗版）、省心（零排版）、有利心（高分成）；使阅读舒心（拟真质感）、会心（术语交互）、能定心（专注阅读）。**

本项目是 **Brtech Fusion 底座** 的标杆级应用，展示了如何利用底座能力在极短时间内构建包含 **PDF 矢量解析、AI 知识提取、3D 阅读引擎及复杂支付体系** 的全栈系统。

---

## 🛠 解决的核心问题

### 1. 创作者的护城河：版权与排版
*   **痛点**：PDF 电子书极易被直接复制传播，且移动端排版体验极差。
*   **解决方案**：底座集成 `PyMuPDF` 矢量切片技术。PDF 上传后自动进行 **WebP 物理切片 + 智能白边裁剪 + 正片叠底护眼染色**。前端通过流式签名 URL 加载图片，不暴露原始 PDF，实现像素级还原的同时保护版权。

### 2. 硬核阅读的门槛：术语与伴读
*   **痛点**：阅读技术书籍时，遇到专业术语频繁查阅干扰思路；实验代码和视频资料分散。
*   **解决方案**：集成 **DeepSeek R1/V3** 大模型，实现一键章节术语提取。结合坐标扫描算法，将术语释义“缝合”到书页坐标上。读者“即点即看”，并支持代码附件下载与视频窗口伴读。

### 3. 开发效率的瓶颈：底座驱动
*   **痛点**：中后台管理系统的 CRUD（增删改查）占据了 70% 的开发时间。
*   **解决方案**：全面应用 Brtech Fusion 架构。
    *   **管理后台**：0 代码编写界面。通过 Python 模型注解直接生成书籍管理、章节管理、笔记审计等界面。
    *   **权限模型**：直接继承底座 4A 体系，自动获得组织架构、按书授权的数据权限。

---

## 🏗 基于博然低代码底座的开发范式 (Fusion In Action)

本项目深度演示了如何“正确地使用底座进行开发”：

### 1. 元数据声明 (配置即界面)
在 `models.py` 中，通过简单的注解定义复杂的 UI 行为：
```python
@ui_config(
    module_name="书页管理",
    # 定义关联查询，前端自动生成带搜索的下拉框
    layout=[
      "book_id", "page_no", "page_image_path", 
      FieldOption(prop="page_content", component=UIComponent.TEXTAREA)
    ],
    # 自定义行操作，直接关联后台 API 或跳转路由
    row_actions=[
      Action(code="read", label="阅读", type=ActionType.LINK, router_path="/reader/{bookId}/{pageNo}"),
      Action(code="scan", label="坐标扫描", type=ActionType.API, api_url="/book/scanCoords/{modelId}")
    ]
)
class TriHeartPageModel(StringPKeyModel, table=True): ...
```

### 2. 异步任务追踪 (Task Framework)
利用底座内置的 `TaskRecord` 体系，处理耗时的 PDF 解析：
1.  **创建任务**：`task_manager.create_task(...)`。
2.  **执行逻辑**：在线程池中运行 CPU 密集型的图片处理。
3.  **实时进度**：调用 `update_progress`，前端管理后台的“任务管理”菜单即可自动看到实时进度条。

### 3. 业务 Mixin 与支付分发
实现“购买书籍后自动入库”仅需两步：
*   **Mixin 实现**：在 `TriHeartBookUserService` 中继承 `PaymentServiceMixin`，实现 `resolve_pay_order`。
*   **自动分发**：无需在支付模块写 `if-else`。底座在支付成功后，根据 `business_type` 自动定位到 Mixin 并执行业务落库。

### 4. 坐标转换 Mixin (算法下沉)
针对“切边图”与“原图”坐标不一致的问题，利用底座的 `PageRectsMixinService`：
*   后端存储原始坐标，前端请求时带上 `imageMode=crop`。
*   Service 层自动拦截并根据 `crop_box_data` 进行仿射变换，确保无论用户看哪种图，高亮位置永远精准。

---

## 🧩 核心功能模块

### 📘 书籍解析引擎 (PDF Helper)
*   **智能裁剪**：自动检测 PDF 内容 BBox，去除冗余白边，提升移动端阅读面积利用率。
*   **WebP 压缩**：采用 method 6 强力压缩，平衡画质与加载速度。
*   **目录树提取**：自动递归提取 PDF 原生目录，并同步至数据库。

### 🤖 AI 术语中心
*   **DeepSeek 集成**：利用大模型长上下文能力，精准识别领域关键词。
*   **坐标自动化**：扫描全书文本，自动将 AI 返回的术语映射到图像像素坐标。

### 🎨 3D 阅读引擎 (Reader v4)
*   **物理仿真**：支持双页扩展（Spread）、单页模式（Single）。
*   **分段翻页**：自研 `LeafSegment` 组件，实现翻页时书页的微弧度形变。
*   **书块模型**：动态计算左右页堆叠厚度（Z-index 视觉差），还原真实书籍厚度感。

### 💰 支付与书架
*   **收银台**：集成底座统一支付弹窗。
*   **阅读历史**：自动保存每本书的最后阅读页码，跨端同步。

---

## 🚀 启动指引

### 环境要求
*   Python 3.11+
*   Node.js 20+
*   MinIO (或阿里云 OSS)
*   PostgreSQL / MySQL

### 后端 (App Backend)
1.  安装依赖：`pip install -r requirements.txt`
2.  配置 `.env`：参考 `app/config.py` 修改数据库和 OSS 连接。
3.  初始化数据：启动后底座会自动扫描 `fixtures/` 下的 JSON 并执行数据注入。
4.  运行：`python main.py`

### 前端 (App Frontend)
1.  安装依赖：`npm install` (需确保 `brtech-fusion` 本地包路径正确)
2.  运行开发：`npm run dev`
3.  编译生产：`npm run build` (产物将自动输出至后端 static 目录)

---

## 📈 未来规划
- [ ] **AI 伴读对话**：基于当前书页内容的 RAG 问答。
- [ ] **多端同步**：适配移动端原生操作的翻页手势。
- [ ] **社交分享**：支持生成精美的读书笔记海报。

---

**三心书坊** —— *不仅仅是阅读，是与知识的深度对话。*