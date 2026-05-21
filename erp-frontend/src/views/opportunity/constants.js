export const SOURCE_OPTIONS = [
  { label: '自主', value: '自主' },
  { label: '集团', value: '集团' },
]

export const TYPE_OPTIONS = [
  { label: '一般', value: '一般', tag: '' },
  { label: '中等', value: '中等', tag: 'warning' },
  { label: '重大', value: '重大', tag: 'danger' },
]

export const BID_TYPE_OPTIONS = [
  { label: '招投标', value: '招投标' },
  { label: '销售报价', value: '销售报价' },
]

export const STATUS_OPTIONS = [
  { label: '进行中', value: '进行中', tag: 'primary' },
  { label: '已闭合', value: '已闭合', tag: 'success' },
  { label: '已流转', value: '已流转', tag: 'info' },
  { label: '已关闭', value: '已关闭', tag: 'info' },
]

const optionMap = (options) => Object.fromEntries(options.map((o) => [o.value, o]))

export const typeMap = optionMap(TYPE_OPTIONS)
export const statusMap = optionMap(STATUS_OPTIONS)
