import request from './request'

export const fetchProjects = (params) => request.get('/project/list', { params })
export const fetchProject = (id) => request.get(`/project/${id}`)
export const createProject = (data) => request.post('/project', data)
