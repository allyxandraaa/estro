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
