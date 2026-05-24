// Lives separately from auth.js so client.js can read the token without a circular import.
// Plaintext passwords are NEVER written here — only the JWT returned by the backend.

const TOKEN_KEY = 'estro.auth.token'

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // localStorage can throw in private mode / quota exceeded — swallow so login still proceeds in-memory.
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch {
    // ignore
  }
}
