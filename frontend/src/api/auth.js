import client from './client.js'
import { setToken, clearToken } from './auth-storage.js'

export async function login({ email, password }) {
  const data = await client.post('/auth/login', { email, password })
  if (data?.access_token) setToken(data.access_token)
  return data
}

export async function register({ email, password }) {
  return await client.post('/auth/register', { email, password })
}

export function logout() {
  clearToken()
}
