import Mock from 'mockjs'

const TYPES = ['公路', '水利', '水运', '市政', '房建']
const PRICE_TYPES = ['合同单价', '总价包干']
const LEVELS = ['一般', '中等', '重大']
const STATUSES = ['未提交', '审批中', '已完成']
const ARCHIVES = ['未归档', '部分归档', '已归档']
const DIVISIONS = ['公路', '水利', '水运', '市政', '房建', '检测', '咨询']

const cname = () => Mock.Random.cname()

const buildSeed = () => {
  const list = []
  for (let i = 1; i <= 20; i++) {
    const total = Mock.Random.float(100, 3000, 2, 2)
    const divisionAmounts = {}
    let left = total
    DIVISIONS.forEach((d, idx) => {
      if (idx === DIVISIONS.length - 1) divisionAmounts[d] = Number(left.toFixed(2))
      else {
        const a = Number((Math.random() * left * 0.3).toFixed(2))
        divisionAmounts[d] = a
        left -= a
      }
    })
    const level = Mock.Random.pick(LEVELS)
    const status = Mock.Random.pick(STATUSES)
    list.push({
      id: i,
      code: `HT-2026-${String(i).padStart(4, '0')}`,
      archiveNumber: `BA2026${String(Mock.Random.integer(1000, 9999))}`,
      oppCode: `SJ-2026-${String(Mock.Random.integer(1, 38)).padStart(4, '0')}`,
      name: Mock.Random.pick([
        `${Mock.Random.city()}市政工程合同`,
        `${Mock.Random.county()}水利检测服务合同`,
        `${Mock.Random.city()}道路改造勘察合同`,
        `${Mock.Random.county()}房建检测合同`,
      ]),
      customer: cname() + Mock.Random.pick(['建设集团', '工程公司', '投资公司']),
      manager: cname(),
      contractType: Mock.Random.pick(TYPES),
      priceType: Mock.Random.pick(PRICE_TYPES),
      level,
      discount: Number(Mock.Random.float(0.85, 1.0, 2, 2).toFixed(2)),
      revenue: total,
      divisionAmounts,
      cost: {
        labor: Number((total * 0.3).toFixed(2)),
        coop: Number((total * 0.2).toFixed(2)),
        material: Number((total * 0.15).toFixed(2)),
        other: Number((total * 0.05).toFixed(2)),
      },
      coopMembers: [cname(), cname()],
      materialMembers: [cname()],
      hasArchiveContract: Mock.Random.boolean(),
      hasPaymentContract: Mock.Random.boolean(),
      payee: Mock.Random.pick(['甲方账户A', '甲方账户B', '甲方账户C']),
      archiveStatus: Mock.Random.pick(ARCHIVES),
      status,
      approvals: status === '已完成'
        ? [
            { role: '营销中心负责人', name: cname(), action: '分配项目经理', time: '2026-04-20 10:00' },
            { role: '项目经理', name: cname(), action: '填写合同信息', time: '2026-04-22 14:30' },
            { role: '配合费/材料费成员', name: '多人', action: '填写费用', time: '2026-04-25 11:00' },
            { role: '营销中心负责人', name: cname(), action: '审核通过', time: '2026-04-28 09:15' },
            ...(level === '重大'
              ? [{ role: '总经理', name: cname(), action: '终审通过', time: '2026-04-30 16:00' }]
              : []),
          ]
        : status === '审批中'
        ? [
            { role: '营销中心负责人', name: cname(), action: '分配项目经理', time: '2026-05-08 10:00' },
            { role: '项目经理', name: cname(), action: '提交合同信息', time: '2026-05-10 14:30' },
          ]
        : [],
      attachments: [],
      createdAt: Mock.Random.datetime('yyyy-MM-dd HH:mm:ss'),
    })
  }
  return list
}

const store = { list: buildSeed(), nextId: 21 }

const ok = (data) => ({ code: 0, message: 'ok', data })
const fail = (m) => ({ code: 500, message: m, data: null })
const parseBody = (b) => { try { return typeof b === 'string' ? JSON.parse(b) : b || {} } catch { return {} } }
const idFromUrl = (url) => Number(url.split('?')[0].split('/').filter(Boolean).pop())

export default [
  {
    url: '/api/contract/list',
    method: 'get',
    response: ({ query }) => {
      const page = Number(query.page || 1)
      const pageSize = Number(query.pageSize || 10)
      let list = store.list.slice()
      if (query.keyword)
        list = list.filter((i) => i.name.includes(query.keyword) || i.code.includes(query.keyword))
      if (query.status) list = list.filter((i) => i.status === query.status)
      if (query.level) list = list.filter((i) => i.level === query.level)
      if (query.archiveStatus) list = list.filter((i) => i.archiveStatus === query.archiveStatus)
      return ok({
        items: list.slice((page - 1) * pageSize, page * pageSize),
        total: list.length,
        page,
        pageSize,
      })
    },
  },
  {
    url: '/api/contract/meta',
    method: 'get',
    response: () => ok({ types: TYPES, priceTypes: PRICE_TYPES, levels: LEVELS, divisions: DIVISIONS }),
  },
  {
    url: '/api/contract/:id',
    method: 'get',
    response: ({ url }) => {
      const item = store.list.find((i) => i.id === idFromUrl(url))
      return item ? ok(item) : fail('未找到')
    },
  },
  {
    url: '/api/contract',
    method: 'post',
    response: ({ body }) => {
      const data = parseBody(body)
      const id = store.nextId++
      const item = {
        id,
        code: `HT-2026-${String(id).padStart(4, '0')}`,
        archiveStatus: '未归档',
        status: '审批中',
        approvals: [{ role: '营销中心负责人', name: '当前用户', action: '发起合同', time: new Date().toISOString().slice(0, 19).replace('T', ' ') }],
        attachments: [],
        createdAt: new Date().toISOString().slice(0, 19).replace('T', ' '),
        ...data,
      }
      store.list.unshift(item)
      return ok(item)
    },
  },
  {
    url: '/api/contract/:id/archive',
    method: 'post',
    response: ({ url, body }) => {
      const id = idFromUrl(url.replace('/archive', ''))
      const item = store.list.find((i) => i.id === id)
      if (!item) return fail('未找到')
      const { archiveStatus } = parseBody(body)
      item.archiveStatus = archiveStatus
      return ok(item)
    },
  },
]
