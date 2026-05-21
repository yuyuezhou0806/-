import request from './request'

export const fetchContracts = (params) => request.get('/contract/list', { params })
export const fetchContract = (id) => request.get(`/contract/${id}`)
export const createContract = (data) => request.post('/contract', data)
export const archiveContract = (id, archiveStatus) =>
  request.post(`/contract/${id}/archive`, { archiveStatus })
export const fetchContractMeta = () => request.get('/contract/meta')
