// src/api/shelf/index.ts
import {request} from 'brtech-fusion'
import type {UnifiedBookModel, UserBookRelation} from '@/types/book'
import dayjs from 'dayjs'

export interface DictionaryItem {
  dicLabel: string
  dicValue: string
  dicSort?: number

  [key: string]: any
}

export class ShelfApi {

  static async getShelfDictionaries(types: string[] = ['book_category', 'book_sort']) {
    const formData = new FormData()
    types.forEach(t => formData.append('dic_types', t))
    const {data} = await request.post<any>('/dictionary/query/byTypes', formData)
    if (data && data.flag && data.data) {
      return data.data as Record<string, DictionaryItem[]>
    }
    return {}
  }

  /**
   * 查询书籍列表
   */
  static async searchBooks(params: { keyword?: string, categories?: string[], sort?: string, page?: number, size?: number }) {
    const queryPayload: any = {
      bookStatus: '1',
      page: params.page || 1,
      size: params.size || 96,
      sortItems: []
    }

    if (params.keyword) {
      queryPayload.mixedInput = params.keyword
      queryPayload.enableLikeQuery = true
    }
    if (params.categories && params.categories.length > 0) {
      queryPayload.bookCategories = params.categories
    }

    if (params.sort && params.sort.includes(',')) {
      const [field, direction] = params.sort.split(',')
      if (field && (direction === 'ASC' || direction === 'DESC')) {
        queryPayload.sortItems.push({fieldName: field, direction: direction})
      } else {
        queryPayload.sortItems.push({fieldName: 'updateTimestamp', direction: 'DESC'})
      }
    } else {
      queryPayload.sortItems.push({fieldName: 'updateTimestamp', direction: 'DESC'})
    }

    // 发送请求
    const {data: response} = await request.post<any>('/book/query/mixed', queryPayload)

    // 解析结果
    if (response && response.flag && response.data) {
      const content = response.data.content || []
      const total = response.data.total || 0

      return {
        list: content as UnifiedBookModel[],
        total: Number(total)
      }
    }

    return {list: [], total: 0}
  }

  static async createBookUserRelation(bookId: string, userId: string): Promise<UserBookRelation | null> {
    let rtnVal: UserBookRelation | null = null
    const {data: response} = await request.post<any>('/bookUser/add', {
      bookId: bookId,
      userId: userId,
      purchaseStatus: '0',
      lastReadPageNo: 1,
      lastReadTime: dayjs().format('YYYY-MM-DD HH:mm:ss')
    })

    if (response && response.flag && response.data) {
      rtnVal = response.data // 返回关系对象
    }
    return rtnVal
  }

  static async updateLastReadPageNo(relationId: string, pageNo: number) {
    if (!relationId) {
      return
    }
    let rtnVal: UserBookRelation | null = null
    // 调用通用 update 接口
    const {data: response} = await request.post('/bookUser/update', {
      modelId: relationId,
      lastReadPageNo: pageNo,
      lastReadTime: dayjs().format('YYYY-MM-DD HH:mm:ss')
    })
    if (response && response.flag && response.data) {
      rtnVal = response.data // 返回关系对象
    }
    return rtnVal
  }

  static async queryBookUserRelations(params: any) {
    const {data: response} = await request({
      url: '/bookUser/query/page',
      method: 'post',
      data: {page: 1, size: 20, ...params}
    })
    return response
  }

  static async getBookUserRelation(bookId: string): Promise<UserBookRelation | null> {
    let rtnVal: UserBookRelation | null = null
    const {data: response} = await request.post<any>(`/bookUser/query/all`, {
      bookId: bookId
    })
    if (response && response.flag && response.data?.length > 0) {
      rtnVal = response.data[0] as UserBookRelation
    }
    return rtnVal
  }

  static async getBookDetail(bookId: string) {
    let rtnVal: UnifiedBookModel | null = null
    const {data} = await request.post<any>(`/book/find/${bookId}`)
    if (data && data.flag) {
      rtnVal = data.data as UnifiedBookModel
    }
    return rtnVal
  }

  static async getSignedUrl(objectKey: string): Promise<string> {
    if (!objectKey) {
      return ''
    }
    if (objectKey.startsWith('http')) {
      return objectKey
    }

    try {
      const formData = new FormData()
      formData.append('objectKey', objectKey)
      const {data: signedUrlData} = await request.post<any>('/book/storage/signedUrl/download', formData, {
        headers: {'Content-Type': 'application/x-www-form-urlencoded'}
      })
      if (signedUrlData && signedUrlData.flag) {
        return signedUrlData.data
      }
    } catch (e) {
      console.error('获取签名失败', e)
    }
    return ''
  }

  static async getCoverSignUrl(bookId: string): Promise<string> {
    const {data: response} = await request.post<any>(`/book/coverSignUrl/${bookId}`)
    if (response && response.flag) {
      return response.data || ''
    }
    return ''
  }

  static async getPageWebpUrl(bookId: string, pageNo: number, type?: 'crop' | 'origin'): Promise<string> {
    try {
      const deviceType = type || (window.innerWidth < 768 ? 'crop' : 'origin');

      const {data: response} = await request.post<any>('/page/webpUrl', {
        bookId: bookId,
        pageNo: pageNo,
        webpType: deviceType
      })

      if (response && response.flag) {
        return response.data
      }
    } catch (e) {
      console.warn(`获取P${pageNo}预览图失败`, e)
    }
    return ''
  }
}