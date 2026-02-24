// src/types/book.d.ts

/**
 * 对应后端 TriHeartBookModel (转驼峰命名)
 */
export interface TriHeartBookModel {
  modelId: string; // 主键

  // 基本信息
  bookTitle: string;
  bookSubtitle?: string;
  bookIsbn?: string;
  bookAuthor?: string;
  bookTranslator?: string;
  bookCover?: string; // 对应后端相对路径，需配合 resolveUrl 使用
  bookSummary?: string; // 摘要/简介
  bookPageCount?: number;

  // 目录信息
  tocBeginPage?: number;
  tocEndPage?: number;
  bodyPageOffset?: number; // 正文起始页码（目录页不计入）

  // 分类与状态
  bookCategory?: string; // 字典值
  bookCategoryDisplay?: string; // 字典显示文本
  bookStatus?: string; // 上架、下架等
  bookStatusDisplay?: string;

  // 价格体系
  bookListPrice?: number; // 定价 (划线价)
  bookSalePrice?: number; // 售价 (实际价格)

  // 所有者信息
  ownerId?: string;
  ownerName?: string;

  // --- 前端辅助字段 (非后端数据库字段) ---
  // 用于 UI 展示的扩展字段
  tags?: string[];   // 可以由 category 或 status 转换而来
  bgColor?: string;  // 封面加载前的背景色
}

/**
 * 用户与书的关联状态 (来自 UserShelf 接口)
 */
export class UserBookRelation {
  modelId: string; // 主键
  bookId: string;
  userId: string;
  lastReadTime?: string;
  lastReadPageNo?: number;
  purchaseStatus: string;
  bookModel: TriHeartBookModel;

  // 原来的 readStatus 被注释了，我们通过下面的 getter 动态计算
  // readStatus: 'unread' | 'reading' | 'finished';

  // 构造函数：必不可少，用于将数据塞入实例
  constructor(data: Partial<UserBookRelation>) {
    this.bookId = data.bookId || '';
    this.userId = data.userId || '';
    this.lastReadTime = data.lastReadTime;
    this.lastReadPageNo = data.lastReadPageNo;
    this.purchaseStatus = data.purchaseStatus || '0';
    // 确保 bookModel 存在，防止调用时报错
    this.bookModel = data.bookModel || {bookPageCount: 0};
  }

  // 1. 判断是否购买
  isPurchased(): boolean {
    return this.purchaseStatus === '1';
  }

  /**
   * 2. 获取阅读进度字符串 (修正版)
   * 逻辑：处理 undefined 情况，返回 "当前页/总页数"
   */
  getReadProgress(): string {
    // 使用 ?? 0 处理 undefined 或 null 的情况
    const current = this.lastReadPageNo ?? 0;
    const total = this.bookModel?.bookPageCount ?? 0;

    return `${current}/${total}`;
  }

  /**
   * 3. 获取阅读状态文案 (修正版 - 智能计算)
   * 逻辑：不再依赖后端字段，而是根据 页码 自动判断
   */
  getReadStatus(): string {
    const current = this.lastReadPageNo ?? 0;
    const total = this.bookModel?.bookPageCount ?? 0;

    // 情况1: 没读过或者页码为0 -> 未读
    if (!this.lastReadTime || current === 0) {
      return '未读';
    }

    // 情况2: 当前页码 >= 总页数 -> 已读
    // (注意：防止总页数为0导致的误判，加一个 total > 0 的判断)
    if (total > 0 && current >= total) {
      return '已读';
    }

    // 情况3: 既不是0也不是满 -> 在读
    return '在读';
  }

  // 补充一个：获取进度的百分比数字（0-100），用于进度条
  getProgressPercentage(): number {
    const current = this.lastReadPageNo ?? 0;
    const total = this.bookModel?.bookPageCount ?? 0;
    if (total === 0) {
      return 0;
    }

    // 结果保留整数，例如 45
    return Math.min(Math.floor((current / total) * 100), 100);
  }
}

/**
 * 统一书籍模型 (UI组件使用的最终对象)
 * 组件内部根据 mode 决定渲染哪些字段
 */
export type UnifiedBookModel = TriHeartBookModel & Partial<UserBookRelation> & {
  // 辅助字段：当前展示模式
  displayMode?: 'public' | 'personal';
};