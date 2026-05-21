import request from './request'

export const fetchBiddings = (params) => request.get('/bidding/list', { params })
export const fetchBidding = (id) => request.get(`/bidding/${id}`)
export const assignBiddingTask = (id, data) => request.post(`/bidding/${id}/assign`, data)
export const updateBiddingResult = (id, isWon) => request.post(`/bidding/${id}/result`, { isWon })
export const fetchTemplates = () => request.get('/bidding/templates')
export const uploadTemplate = (data) => request.post('/bidding/templates', data)
