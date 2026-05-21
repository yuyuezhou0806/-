import request from './request'

export const fetchDepartmentTasks = (params) => request.get('/department/list', { params })
export const fetchDepartmentTask = (id) => request.get(`/department/${id}`)
export const submitDepartmentTask = (id, data) => request.post(`/department/${id}/submit`, data)
