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
    return Promise.reject(new Error(extractMessage(error)))
  },
)

function extractMessage(error) {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) return friendlyValidation(detail[0])
  return error.response?.data?.message
    || error.response?.data?.error
    || 'Щось пішло не так. Спробуйте ще раз.'
}

const FIELD_NAMES = {
  cycle_length:     'Тривалість циклу',
  period_length:    'Тривалість менструації',
  last_period_date: 'Дата останньої менструації',
  email:            'Пошта',
  password:         'Пароль',
}

const TYPE_MESSAGES = {
  'missing':                    "обов'язкове поле",
  'string_too_short':           'занадто коротке',
  'string_too_long':            'занадто довге',
  'greater_than_equal':         'занадто мале значення',
  'less_than_equal':            'занадто велике значення',
  'date_from_datetime_parsing': 'введіть коректну дату',
  'value_error.email':          'введіть коректну електронну пошту',
}

function friendlyValidation(err) {
  const field = err.loc?.at(-1)
  const fieldLabel = FIELD_NAMES[field] ?? field

  if (err.type === 'value_error') {
    return err.msg.replace(/^Value error,\s*/i, '')
  }

  const typeMsg = TYPE_MESSAGES[err.type]
  if (typeMsg) {
    return fieldLabel ? `${fieldLabel}: ${typeMsg}.` : `${typeMsg}.`
  }

  return err.msg || 'Перевірте правильність введених даних.'
}

export default client
