import Mock from 'mockjs'

const STATUSES = ['制作中', '待提交', '已提交', '已中标', '未中标']
const TASK_TYPES = ['技术方案', '清单', '技术标', '其它']

const buildSeed = () => {
  const list = []
  for (let i = 1; i <= 16; i++) {
    const status = Mock.Random.pick(STATUSES)
    list.push({
      id: i,
      code: `ZB-2026-${String(i).padStart(4, '0')}`,
      oppCode: `SJ-2026-${String(Mock.Random.integer(1, 38)).padStart(4, '0')}`,
      name: Mock.Random.pick([
        `${Mock.Random.city()}市政道路标书`,
        `${Mock.Random.county()}水利检测报价`,
        `${Mock.Random.city()}地铁标段评标`,
        `${Mock.Random.county()}房建检测投标`,
      ]),
      bidType: Mock.Random.pick(['招投标', '销售报价']),
      needQuery: Mock.Random.boolean(),
      queryTime: Mock.Random.datetime('yyyy-MM-dd HH:mm'),
      deadline: Mock.Random.date('yyyy-MM-dd'),
      isWon: status === '已中标' ? true : status === '未中标' ? false : null,
      tasks: TASK_TYPES.filter(() => Mock.Random.boolean()).slice(0, 2),
      assignees: [Mock.Random.cname(), Mock.Random.cname()].slice(0, Mock.Random.integer(1, 2)),
      assignDate: Mock.Random.date('yyyy-MM-dd'),
      requireDate: Mock.Random.date('yyyy-MM-dd'),
      status,
      remark: Mock.Random.csentence(6, 18),
      createdAt: Mock.Random.datetime('yyyy-MM-dd HH:mm:ss'),
    })
  }
  return list
}

const TEMPLATES = [
  { id: 1, name: '市政工程招标范本.docx', type: '招投标', size: 245680, uploader: '张工', updatedAt: '2026-04-12 09:22' },
  { id: 2, name: '水利检测投标书范本.docx', type: '招投标', size: 312410, uploader: '李工', updatedAt: '2026-03-25 14:51' },
  { id: 3, name: '销售报价模板(通用).xlsx', type: '销售报价', size: 89230, uploader: '王工', updatedAt: '2026-05-02 10:00' },
  { id: 4, name: '房建检测技术方案模板.docx', type: '招投标', size: 412508, uploader: '赵工', updatedAt: '2026-04-30 16:38' },
  { id: 5, name: '道路工程清单模板.xlsx', type: '招投标', size: 76410, uploader: '孙工', updatedAt: '2026-05-05 11:20' },
]

const store = { list: buildSeed(), nextId: 17, templates: TEMPLATES, nextTemplateId: 6 }

const ok = (data) => ({ code: 0, message: 'ok', data })
const fail = (message) => ({ code: 500, message, data: null })

const parseBody = (body) => {
  try {
    return typeof body === 'string' ? JSON.parse(body) : body || {}
  } catch {
    return {}
  }
}

const idFromUrl = (url) => {
  const path = url.split('?')[0]
  const seg = path.split('/').filter(Boolean)
  return Number(seg[seg.length - 1])
}

export default [
  {
    url: '/api/bidding/list',
    method: 'get',
    response: ({ query }) => {
      const page = Number(query.page || 1)
      const pageSize = Number(query.pageSize || 10)
      let list = store.list.slice()
      if (query.keyword)
        list = list.filter((i) => i.name.includes(query.keyword) || i.code.includes(query.keyword))
      if (query.status) list = list.filter((i) => i.status === query.status)
      if (query.bidType) list = list.filter((i) => i.bidType === query.bidType)
      const total = list.length
      return ok({ items: list.slice((page - 1) * pageSize, page * pageSize), total, page, pageSize })
    },
  },
  {
    url: '/api/bidding/templates',
    method: 'get',
    response: () => ok(store.templates),
  },
  {
    url: '/api/bidding/templates',
    method: 'post',
    response: ({ body }) => {
      const data = parseBody(body)
      const item = {
        id: store.nextTemplateId++,
        size: data.size || 100000,
        uploader: '当前用户',
        updatedAt: new Date().toISOString().slice(0, 16).replace('T', ' '),
        ...data,
      }
      store.templates.unshift(item)
      return ok(item)
    },
  },
  {
    url: '/api/bidding/:id',
    method: 'get',
    response: ({ url }) => {
      const item = store.list.find((i) => i.id === idFromUrl(url))
      return item ? ok(item) : fail('未找到')
    },
  },
  {
    url: '/api/bidding/:id/assign',
    method: 'post',
    response: ({ url, body }) => {
      const id = idFromUrl(url.replace('/assign', ''))
      const item = store.list.find((i) => i.id === id)
      if (!item) return fail('未找到')
      Object.assign(item, parseBody(body))
      item.status = '制作中'
      return ok(item)
    },
  },
  {
    url: '/api/bidding/:id/result',
    method: 'post',
    response: ({ url, body }) => {
      const id = idFromUrl(url.replace('/result', ''))
      const item = store.list.find((i) => i.id === id)
      if (!item) return fail('未找到')
      const { isWon } = parseBody(body)
      item.isWon = isWon
      item.status = isWon ? '已中标' : '未中标'
      return ok(item)
    },
  },
]
