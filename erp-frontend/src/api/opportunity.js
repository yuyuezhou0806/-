import request from './request'

export const fetchOpportunities = (params) =>
  request.get('/opportunity/list', { params })

export const fetchOpportunity = (id) =>
  request.get(`/opportunity/${id}`)

export const createOpportunity = (data) =>
  request.post('/opportunity', data)

export const updateOpportunity = (id, data) =>
  request.put(`/opportunity/${id}`, data)

export const closeOpportunity = (id) =>
  request.post(`/opportunity/${id}/close`)

export const transferOpportunity = (id, departments) =>
  request.post(`/opportunity/${id}/transfer`, { departments })

export const fetchDepartments = () =>
  request.get('/meta/departments')
