import client from './client.js'

export function getDailyLog(date) {
  return client.get(`/daily-logs/${date}`)
}

export function saveDailyLog(date, data) {
  return client.put(`/daily-logs/${date}`, data)
}

export function deleteDailyLog(date) {
  return client.delete(`/daily-logs/${date}`)
}
