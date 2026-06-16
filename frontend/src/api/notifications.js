import client from './client.js'

export function getNotifications() {
  return client.get('/notifications')
}

export function markAllRead() {
  return client.post('/notifications/read')
}
