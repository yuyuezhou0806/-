import Mock from 'mockjs'

const SOURCES = ['自主', '集团']
const TYPES = ['一般', '中等', '重大']
const BID_TYPES = ['招投标', '销售报价']
const STATUSES = ['进行中', '已闭合', '已流转', '已关闭']

const DEPARTMENTS = [
  { id: 1, name: '公路事业部' },
  { id: 2, name: '水利事业部' },
  { id: 3, name: '水运事业部' },
  { id: 4, name: '市政事业部' },
  { id: 5, name: '房建事业部' },
  { id: 6, name: '检测事业部' },
  { id: 7, name: '咨询事业部' },
  { id: 8, name: '营销中心' },
]

const pad = (n) => String(n).padStart(4, '0')

const buildSeed = () => {
  const list = []
  for (let i = 1; i <= 38; i++) {
    const createdAt = Mock.Random.datetime('yyyy-MM-dd HH:mm:ss')
    const status = Mock.Random.pick(STATUSES)
    const transferDepts =
      status === '已流转' ? Mock.Random.pick([[1], [2, 3], [4, 8]]) : []
    list.push({
      id: i,
      code: `SJ-2026-${pad(i)}`,
      name: Mock.Random.pick([
        `${Mock.Random.city()}市政工程咨询`,
        `${Mock.Random.county()}水利检测项目`,
        `${Mock.Random.city()}道路改造勘察`,
        `${Mock.Random.county()}房建质量评估`,
        `${Mock.Random.city()}地铁线路检测`,
      ]),
      source: Mock.Random.pick(SOURCES),
      type: Mock.Random.pick(TYPES),
      needBid: Mock.Random.boolean(),
      bidType: Mock.Random.pick(BID_TYPES),
      customer:
        Mock.Random.cname() +
        Mock.Random.pick(['建设集团', '工程公司', '投资公司']),
      contact: Mock.Random.cname(),
      phone: Mock.mock(/^1[3-9]\d{9}$/),
      amount: Mock.Random.float(50, 2000, 2, 2),
      transferDepts,
      status,
      remark: Mock.Random.csentence(8, 20),
      attachments: [],
      createdBy: Mock.Random.cname(),
      createdAt,
      updatedAt: createdAt,
    })
  }
  return list
}

const store = { list: buildSeed(), nextId: 39 }

const ok = (data) => ({ code: 0, message: 'ok', data })
const fail = (message) => ({ code: 500, message, data: null })

const parseBody = (body) => {
  try {
    return typeof body === 'string' ? JSON.parse(body) : body || {}
  } catch {
    return {}
  }
}

const now = () => new Date().toISOString().replace('T', ' ').slice(0, 19)

const extractIdFromUrl = (url, suffix = '') => {
  const cleaned = url.split('?')[0]
  const segments = cleaned.split('/').filter(Boolean)
  if (suffix) {
    const idx = segments.indexOf(suffix)
    if (idx > 0) return Number(segments[idx - 1])
  }
  return Number(segments[segments.length - 1])
}

export default [
  {
    url: '/api/opportunity/list',
    method: 'get',
    response: ({ query }) => {
      const page = Number(query.page || 1)
      const pageSize = Number(query.pageSize || 10)
      const { keyword, status, type, source } = query
      let list = store.list.slice()
      if (keyword) {
        list = list.filter(
          (item) => item.name.includes(keyword) || item.code.includes(keyword),
        )
      }
      if (status) list = list.filter((item) => item.status === status)
      if (type) list = list.filter((item) => item.type === type)
      if (source) list = list.filter((item) => item.source === source)
      const total = list.length
      const items = list.slice((page - 1) * pageSize, page * pageSize)
      return ok({ items, total, page, pageSize })
    },
  },
  {
    url: '/api/opportunity',
    method: 'post',
    response: ({ body }) => {
      const data = parseBody(body)
      const id = store.nextId++
      const item = {
        attachments: [],
        transferDepts: [],
        status: '进行中',
        createdBy: '当前用户',
        createdAt: now(),
        updatedAt: now(),
        ...data,
        id,
        code: `SJ-2026-${pad(id)}`,
      }
      store.list.unshift(item)
      return ok(item)
    },
  },
  {
    url: '/api/opportunity/:id/close',
    method: 'post',
    response: ({ url }) => {
      const id = extractIdFromUrl(url, 'close')
      const item = store.list.find((it) => it.id === id)
      if (!item) return fail('商机不存在')
      item.status = '已关闭'
      item.updatedAt = now()
      return ok(item)
    },
  },
  {
    url: '/api/opportunity/:id/transfer',
    method: 'post',
    response: ({ url, body }) => {
      const id = extractIdFromUrl(url, 'transfer')
      const item = store.list.find((it) => it.id === id)
      if (!item) return fail('商机不存在')
      const { departments = [] } = parseBody(body)
      item.transferDepts = departments
      item.status = '已流转'
      item.updatedAt = now()
      return ok(item)
    },
  },
  {
    url: '/api/opportunity/:id',
    method: 'put',
    response: ({ url, body }) => {
      const id = extractIdFromUrl(url)
      const item = store.list.find((it) => it.id === id)
      if (!item) return fail('商机不存在')
      Object.assign(item, parseBody(body), { id, updatedAt: now() })
      return ok(item)
    },
  },
  {
    url: '/api/opportunity/:id',
    method: 'get',
    response: ({ url }) => {
      const id = extractIdFromUrl(url)
      const item = store.list.find((it) => it.id === id)
      return item ? ok(item) : fail('商机不存在')
    },
  },
  {
    url: '/api/meta/departments',
    method: 'get',
    response: () => ok(DEPARTMENTS),
  },
]
