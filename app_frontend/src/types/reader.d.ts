// src/types/reader.d.ts

export interface ChapterItem {
  id: string | number;
  title: string;
  pageNo?: number; // 跳转页码
  children?: ChapterItem[];
  // 兼容 mock 数据中的字段
  content?: string;
  locked?: boolean;
  lockTitle?: string;
  lockMessage?: string;
}

export interface ReaderConfig {
  enableSidebar?: boolean; // 是否启用侧边栏
  enableSettings?: boolean; // 是否启用设置（如字号/3D切换）
  enableBack?: boolean; // 是否显示返回按钮
  catalogTitle?: string; // 目录标题
  lockActionText?: string; // 锁定时的操作文案
  startIn3D?: boolean; // 默认是否开启3D
}

export interface BookDataAdapter {
  getCatalog: (bookId: string) => Promise<{
    title: string;
    totalPages: number;
    treeData: any[];
  }>;

  // mode: 'origin' | 'crop'
  getPageUrl: (bookId: string, pageNo: number, mode: 'origin' | 'crop') => Promise<string | null>;

  // 新增：批注接口 (未来对接)
  getAnnotations?: (bookId: string, pageNo: number) => Promise<any[]>;
  saveAnnotation?: (bookId: string, pageNo: number, data: any) => Promise<boolean>;
}