<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'

const router = useRouter()
const { logout } = useAuth()

function handleLogout() {
  logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <main class="home">
    <div class="card">
      <h1>Вітаємо в Estro</h1>
      <p>Ви успішно увійшли.</p>
      <button class="link" type="button" @click="handleLogout">Вийти</button>
    </div>
  </main>
</template>

<style scoped>
.home {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 2rem;
}

.card {
  background: var(--surface-strong);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 3rem;
  box-shadow: var(--shadow-card);
  text-align: center;
  max-width: 400px;
}

h1 {
  font-size: 1.75rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--ink-900);
}

p {
  color: var(--ink-700);
  margin-bottom: 1.5rem;
}

.link {
  color: var(--matcha-600);
  font-weight: 500;
  font-size: 0.95rem;
}

.link:hover {
  color: var(--matcha-500);
}
</style>
