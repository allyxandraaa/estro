import client from './client.js'

export function getProfile() {
  return client.get('/users/profile')
}

export function updateProfile(data) {
  return client.patch('/users/profile', data)
}
