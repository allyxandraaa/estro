import axios from 'axios'
import { getToken, clearToken } from './auth-storage.js'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) clearToken()
    const message =
      error.response?.data?.message ||
      error.response?.data?.error ||
      error.message ||
      'Щось пішло не так. Спробуйте ще раз.'
    return Promise.reject(new Error(message))
  },
)

export default client
