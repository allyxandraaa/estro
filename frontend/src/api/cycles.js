import client from './client.js'

export function getCalendarView(month, year) {
  return client.get('/cycles/calendar-view', { params: { month, year } })
}

export function startCycle(date) {
  return client.post('/cycles/start', { date })
}

export function endCycle(date) {
  return client.post('/cycles/end', { date })
}

export function deleteCycle(cycleId) {
  return client.delete(`/cycles/${cycleId}`)
}

export function updateCycleEnd(cycleId, date) {
  return client.patch(`/cycles/${cycleId}/end`, { date })
}
