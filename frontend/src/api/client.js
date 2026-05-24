// Thin fetch wrapper used by every per-page api module.
// - Base URL is configurable via VITE_API_BASE_URL (defaults to /api so a Vite proxy can forward to the backend in dev).
// - Confidentiality of request bodies (e.g. passwords) relies on TLS; never call this client over plain http in production.
// - Attaches the JWT from the auth store when present.
// - Normalises errors so callers can `catch (err) { err.status, err.data, err.message }`.

import { getToken, clearToken } from './auth-storage.js'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

export class ApiError extends Error {
  constructor(message, { status, data } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

async function request(path, { method = 'GET', body, headers = {}, auth = true } = {}) {
  const finalHeaders = { Accept: 'application/json', ...headers }
  let payload

  if (body !== undefined) {
    finalHeaders['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  if (auth) {
    const token = getToken()
    if (token) finalHeaders.Authorization = `Bearer ${token}`
  }

  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: finalHeaders,
      body: payload,
      credentials: 'same-origin',
    })
  } catch {
    throw new ApiError('Помилка мережі. Перевірте підключення.', { status: 0 })
  }

  const isJson = response.headers.get('content-type')?.includes('application/json')
  const data = isJson ? await response.json().catch(() => null) : null

  if (!response.ok) {
    if (response.status === 401) clearToken()
    const message = data?.message || data?.error || `Запит не вдався (${response.status})`
    throw new ApiError(message, { status: response.status, data })
  }

  return data
}

export const api = {
  get: (path, opts) => request(path, { ...opts, method: 'GET' }),
  post: (path, body, opts) => request(path, { ...opts, method: 'POST', body }),
  put: (path, body, opts) => request(path, { ...opts, method: 'PUT', body }),
  patch: (path, body, opts) => request(path, { ...opts, method: 'PATCH', body }),
  delete: (path, opts) => request(path, { ...opts, method: 'DELETE' }),
}
