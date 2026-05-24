import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '../composables/useAuth.js'

const BRAND = 'Estro'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { guestOnly: true, title: 'Вхід' },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { guestOnly: true, title: 'Реєстрація' },
  },
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: { requiresAuth: true, title: 'Головна' },
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const authed = isAuthenticated()
  if (to.meta.requiresAuth && !authed) return { name: 'login' }
  if (to.meta.guestOnly && authed) return { name: 'home' }
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · ${BRAND}` : BRAND
})

export default router
