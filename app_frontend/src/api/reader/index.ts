// src/api/services/ReaderService.ts

import {request, type Response} from "brtech-fusion";

// === 接口定义 ===

export interface PageTerm {
  bookId: string;
  pageNo: number;
  termId: string;
  termKey: string;
  termExplanation: string;
  rectsJson: number[][];
}

export interface PageNote {
  modelId: string;
  bookId: string;
  pageNo: number;
  noteContent: string;
  highlightRects: number[][]; // [[x,y,w,h]]
  highlightColor?: string;
  isPrivate: string;
}

export interface PageAttachment {
  modelId: string;
  bookId: string;
  pageNo: number;
  displayName: string;
  attachmentType: string;
  attachmentTypeDisplay: string;
  filePath: string;
  extraData?: any;
  remark?: string;
}

export interface ReaderPage {
  pageNo: number;
  status: 'allow' | 'locked' | 'loading' | 'error';
  url?: string;
  width?: number; // 如果后端没返回宽高，前端可能需要自适应
  height?: number;
  reasonCode?: string;
  message?: string;
}

export interface TriHeartBookModel {
  modelId: string;
  bookTitle: string;
  bookAuthor: string;
  bookPageCount: number;
  bookCover?: string;
}


export class Index {

  /**
   * 1. 初始化书籍信息
   * 对接接口: POST {api_prefix}/book/find/{model_id}
   */
  static async initBook(bookId: string): Promise<TriHeartBookModel> {
    try {
      const {data} = await request.post<Response<TriHeartBookModel>>(`/book/find/${bookId}`);
      return data && data.flag ? data.data : {} as TriHeartBookModel;
    } catch (error) {
      console.error('获取书籍元数据失败:', error);
      throw error;
    }
  }

  /**
   * 2. 获取单页 WebP 地址 (核心原子方法)
   * 对接接口: POST /api/v2/page/webpUrl
   */
  static async getWebpUrl(bookId: string, pageNo: number, webpType: string = 'crop'): Promise<ReaderPage> {
    let page: ReaderPage = {pageNo: pageNo, status: 'loading', url: '', height: 0, width: 0};

    try {
      const params = {bookId: bookId, pageNo: pageNo, webpType: webpType};

      const {data: response} = await request.post<Response<string>>('/page/webpUrl', params);

      if (response && response.flag) {
        // 成功获取图片
        page = {pageNo: pageNo, status: 'allow', url: response.data, width: 0, height: 0};
      } else {
        // 业务层面的拒绝 (HTTP 200, but flag=false, code=403)
        page = {pageNo: pageNo, status: 'locked', reasonCode: 'trial_limit', message: response.message || '试读结束，购买后解锁全文', url: '', width: 0, height: 0};
      }
    } catch (error: any) {
      if (error?.response?.status === 403 || error?.code === '403') {
        page = {pageNo: pageNo, status: 'locked', message: '试读结束，购买后解锁全文', url: '', width: 0, height: 0};
      } else {
        page.status = 'error';
        page.message = '网络请求失败';
      }
    }

    return page;
  }

  static async getPageTerms(bookId: string, pageNo: number, imageMode: 'crop' | 'origin' = 'crop'): Promise<PageTerm[]> {
    try {
      const {data: response} = await request.post<Response<PageTerm[]>>('/pageTerm/query/all', {
        bookId: bookId,
        pageNo: pageNo,
        imageMode: imageMode
      });

      if (response && response.flag && response.data) {
        return response.data;
      }
    } catch (e) {
      console.warn(`获取P${pageNo}术语失败`, e);
    }
    return [];
  }

  static async getPageNotes(bookId: string, pageNo: number, imageMode: 'crop' | 'origin' = 'crop'): Promise<PageNote[]> {
    try {
      const {data: response} = await request.post<Response<PageNote[]>>('/bookNote/query/all', {
        bookId: bookId,
        pageNo: pageNo,
        imageMode: imageMode // 后端 PageRectsMixinService 会根据此参数转换坐标
      });
      if (response && response.flag && response.data) {
        return response.data;
      }
    } catch (e) {
      console.warn(`获取P${pageNo}笔记失败`, e);
    }
    return [];
  }

  static async getPageAttachments(bookId: string, pageNo: number): Promise<PageAttachment[]> {
    try {
      const {data: response} = await request.post<Response<PageAttachment[]>>('/pageAttachment/query/all', {
        bookId: bookId,
        pageNo: pageNo,
      });
      if (response && response.flag && response.data) {
        return response.data;
      }
    } catch (e) {
      console.warn(`获取P${pageNo}附件失败`, e);
    }
    return [];
  }

  static async getAttachmentSignedUrl(filePath: string): Promise<string> {
    const params = new URLSearchParams({
      objectKey: filePath
    });
    const {data: response} = await request.post<Response<string>>('/pageAttachment/storage/signedUrl/download', params);

    if (response && response.flag && response.data) {
      return response.data;
    }
    return ''
  }
}