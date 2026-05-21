import Mock from 'mockjs'

const STATUSES = ['待领取', '执行中', '已完成']
const ROLES = ['配合费成员', '材料费成员', '检测人员']

const buildSeed = () => {
  const list = []
  for (let i = 1; i <= 18; i++) {
    list.push({
      id: i,
      code: `BM-2026-${String(i).padStart(4, '0')}`,
      contractCode: `HT-2026-${String(Mock.Random.integer(1, 20)).padStart(4, '0')}`,
      name: Mock.Random.pick([
        `${Mock.Random.city()}市政工程`,
        `${Mock.Random.county()}水利检测`,
        `${Mock.Random.city()}道路改造`,
        `${Mock.Random.county()}房建评估`,
      ]),
      department: Mock.Random.pick(['公路事业部', '水利事业部', '市政事业部', '检测事业部']),
      role: Mock.Random.pick(ROLES),
      assignee: Mock.Random.cname(),
      amount: Mock.Random.float(5, 80, 2, 2),
      coopFee: Mock.Random.float(2, 20, 2, 2),
      materialFee: Mock.Random.float(1, 15, 2, 2),
      status: Mock.Random.pick(STATUSES),
      assignDate: Mock.Random.date('yyyy-MM-dd'),
      requireDate: Mock.Random.date('yyyy-MM-dd'),
      remark: Mock.Random.csentence(4, 12),
    })
  }
  return list
}

const store = { list: buildSeed() }
const ok = (data) => ({ code: 0, message: 'ok', data })
const fail = (m) => ({ code: 500, message: m, data: null })
const parseBody = (b) => { try { return typeof b === 'string' ? JSON.parse(b) : b || {} } catch { return {} } }
const idFromUrl = (url) => Number(url.split('?')[0].split('/').filter(Boolean).pop())

export default [
  {
    url: '/api/department/list',
    method: 'get',
    response: ({ query }) => {
      const page = Number(query.page || 1)
      const pageSize = Number(query.pageSize || 10)
      let list = store.list.slice()
      if (query.keyword)
        list = list.filter((i) => i.name.includes(query.keyword) || i.code.includes(query.keyword))
      if (query.status) list = list.filter((i) => i.status === query.status)
      if (query.department) list = list.filter((i) => i.department === query.department)
      return ok({
        items: list.slice((page - 1) * pageSize, page * pageSize),
        total: list.length,
        page,
        pageSize,
      })
    },
  },
  {
    url: '/api/department/:id',
    method: 'get',
    response: ({ url }) => {
      const item = store.list.find((i) => i.id === idFromUrl(url))
      return item ? ok(item) : fail('未找到')
    },
  },
  {
    url: '/api/department/:id/submit',
    method: 'post',
    response: ({ url, body }) => {
      const id = idFromUrl(url.replace('/submit', ''))
      const item = store.list.find((i) => i.id === id)
      if (!item) return fail('未找到')
      Object.assign(item, parseBody(body))
      item.status = '已完成'
      return ok(item)
    },
  },
]
