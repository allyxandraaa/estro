import { ref, onMounted, onBeforeUnmount } from 'vue'
import { getToken, setToken, clearToken } from '../api/auth-storage.js'

const token = ref(getToken())

export function useAuth() {
  const onStorage = (event) => {
    if (event.key === 'estro.auth.token') token.value = event.newValue
  }

  onMounted(() => window.addEventListener('storage', onStorage))
  onBeforeUnmount(() => window.removeEventListener('storage', onStorage))

  return {
    setToken: (t) => {
      setToken(t)
      token.value = t
    },
    logout: () => {
      clearToken()
      token.value = null
    },
  }
}

export function isAuthenticated() {
  return !!getToken()
}
