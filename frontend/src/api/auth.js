// Auth endpoints. The plain password is passed straight to fetch (which puts it in the TLS-encrypted
// request body) and never persisted: callers should overwrite their local copy after the promise resolves.

import { api } from './client.js'
import { setToken, clearToken } from './auth-storage.js'

export async function login({ email, password }) {
  const data = await api.post('/auth/login', { email, password }, { auth: false })
  if (data?.token) setToken(data.token)
  return data
}

export async function register({ name, email, password }) {
  const data = await api.post('/auth/register', { name, email, password }, { auth: false })
  if (data?.token) setToken(data.token)
  return data
}

export function logout() {
  clearToken()
}
