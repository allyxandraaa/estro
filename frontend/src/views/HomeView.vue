<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import { auth } from '../api'

const router = useRouter()
const { logout } = useAuth()

function handleLogout() {
  auth.logout()
  logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <main class="home">
    <h1 class="home-heading">
      <span class="home-heading-line">Ви у</span>
      <span class="home-heading-line"><em>своєму ритмі</em>.</span>
    </h1>
    <button class="home-logout" type="button" @click="handleLogout">Вийти</button>
  </main>
</template>

<style scoped>
.home {
  height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 32px;
  background: #fff;
  color: #000;
}

.home-heading {
  font-family: 'Instrument Serif', 'Times New Roman', serif;
  font-weight: 400;
  font-size: clamp(40px, 6vh, 65px);
  line-height: 1;
  text-align: center;
  letter-spacing: -0.005em;
}

.home-heading-line {
  display: block;
}

.home-heading em {
  font-style: italic;
}

.home-logout {
  font-family: 'Geist', sans-serif;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.4);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.home-logout:hover {
  color: rgba(0, 0, 0, 0.7);
}
</style>
