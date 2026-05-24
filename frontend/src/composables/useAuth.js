// Reactive wrapper around the token in localStorage. Single source of truth for "is the user logged in".
// Stays in sync across tabs via the `storage` event.

import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { getToken, setToken, clearToken } from '../api/auth-storage.js'

const token = ref(getToken())

export function useAuth() {
  const onStorage = (event) => {
    if (event.key === 'estro.auth.token') token.value = event.newValue
  }

  onMounted(() => window.addEventListener('storage', onStorage))
  onBeforeUnmount(() => window.removeEventListener('storage', onStorage))

  return {
    token: computed(() => token.value),
    isAuthenticated: computed(() => !!token.value),
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

// Non-reactive helper for places without a component context (e.g. router guards).
export function isAuthenticated() {
  return !!getToken()
}
