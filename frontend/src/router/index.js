import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '../composables/useAuth.js'
import { clearToken } from '../api/auth-storage.js'
import { getProfile } from '../api/profile.js'

const BRAND = 'Estro'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { guestOnly: true, title: 'Увійти' },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { guestOnly: true, title: 'Реєстрація' },
  },
  {
    path: '/onboarding',
    name: 'onboarding',
    component: () => import('../views/OnboardingView.vue'),
    meta: { requiresAuth: true, title: 'Налаштування' },
  },
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: { requiresAuth: true, title: 'Головна' },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../views/ProfileView.vue'),
    meta: { requiresAuth: true, title: 'Профіль' },
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

async function hasActiveSession() {
  if (!isAuthenticated()) return false
  try {
    await getProfile()
    return true
  } catch {
    clearToken()
    return false
  }
}

router.beforeEach(async (to) => {
  const authed = isAuthenticated()
  if (to.meta.requiresAuth && !authed) return { name: 'login' }

  if (to.meta.requiresAuth) {
    const active = await hasActiveSession()
    if (!active) return { name: 'login' }
  }

  if (to.meta.guestOnly && authed) {
    const active = await hasActiveSession()
    if (active) return { name: 'home' }
  }
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · ${BRAND}` : BRAND
})

export default router
