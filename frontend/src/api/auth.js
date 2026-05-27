import client from './client.js'
import { setToken, clearToken } from './auth-storage.js'

export async function login({ email, password }) {
  const data = await client.post('/auth/login', { email, password })
  if (data?.token) setToken(data.token)
  return data
}

export async function register({ name, email, password }) {
  const data = await client.post('/auth/register', { name, email, password })
  if (data?.token) setToken(data.token)
  return data
}

export function logout() {
  clearToken()
}
