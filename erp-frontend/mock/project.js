import Mock from 'mockjs'

const STATUSES = ['立项中', '已立项', '已驳回']

const buildSeed = () => {
  const list = []
  for (let i = 1; i <= 14; i++) {
    list.push({
      id: i,
      code: `LX-2026-${String(i).padStart(4, '0')}`,
      contractCode: `HT-2026-${String(Mock.Random.integer(1, 20)).padStart(4, '0')}`,
      name: Mock.Random.pick([
        `${Mock.Random.city()}市政道路立项`,
        `${Mock.Random.county()}水利检测立项`,
        `${Mock.Random.city()}地铁线路检测立项`,
        `${Mock.Random.county()}房建评估立项`,
      ]),
      manager: Mock.Random.cname(),
      amount: Mock.Random.float(100, 2000, 2, 2),
      department: Mock.Random.pick(['公路事业部', '水利事业部', '市政事业部', '检测事业部']),
      startDate: Mock.Random.date('yyyy-MM-dd'),
      endDate: Mock.Random.date('yyyy-MM-dd'),
      status: Mock.Random.pick(STATUSES),
      remark: Mock.Random.csentence(6, 18),
      createdAt: Mock.Random.datetime('yyyy-MM-dd HH:mm:ss'),
    })
  }
  return list
}

const store = { list: buildSeed(), nextId: 15 }
const ok = (data) => ({ code: 0, message: 'ok', data })
const fail = (m) => ({ code: 500, message: m, data: null })
const parseBody = (b) => { try { return typeof b === 'string' ? JSON.parse(b) : b || {} } catch { return {} } }
const idFromUrl = (url) => Number(url.split('?')[0].split('/').filter(Boolean).pop())

export default [
  {
    url: '/api/project/list',
    method: 'get',
    response: ({ query }) => {
      const page = Number(query.page || 1)
      const pageSize = Number(query.pageSize || 10)
      let list = store.list.slice()
      if (query.keyword)
        list = list.filter((i) => i.name.includes(query.keyword) || i.code.includes(query.keyword))
      if (query.status) list = list.filter((i) => i.status === query.status)
      return ok({
        items: list.slice((page - 1) * pageSize, page * pageSize),
        total: list.length,
        page,
        pageSize,
      })
    },
  },
  {
    url: '/api/project/:id',
    method: 'get',
    response: ({ url }) => {
      const item = store.list.find((i) => i.id === idFromUrl(url))
      return item ? ok(item) : fail('未找到')
    },
  },
  {
    url: '/api/project',
    method: 'post',
    response: ({ body }) => {
      const data = parseBody(body)
      const id = store.nextId++
      const item = {
        id,
        code: `LX-2026-${String(id).padStart(4, '0')}`,
        status: '立项中',
        createdAt: new Date().toISOString().slice(0, 19).replace('T', ' '),
        ...data,
      }
      store.list.unshift(item)
      return ok(item)
    },
  },
]
