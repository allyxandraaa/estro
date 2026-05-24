<script setup>
import { reactive, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { auth } from '../api'
import { useAuth } from '../composables/useAuth.js'
import AuthShell from '../components/AuthShell.vue'
import PasswordInput from '../components/PasswordInput.vue'

const router = useRouter()
const { setToken } = useAuth()

const form = reactive({ email: '', password: '' })
const submitting = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  if (submitting.value) return
  errorMessage.value = ''
  submitting.value = true

  try {
    const data = await auth.login({ email: form.email, password: form.password })
    if (data?.token) setToken(data.token)
    router.push({ name: 'home' })
  } catch (err) {
    errorMessage.value = err.message || 'Не вдалося увійти. Спробуйте ще раз.'
  } finally {
    // Стираємо пароль зі стану форми, щоб він не залишався в памʼяті.
    form.password = ''
    submitting.value = false
  }
}
</script>

<template>
  <AuthShell title="З поверненням" subtitle="Увійдіть, щоб продовжити в Estro.">
    <form class="auth-form" novalidate @submit.prevent="handleSubmit">
      <div v-if="errorMessage" class="auth-alert" role="alert">
        {{ errorMessage }}
      </div>

      <label class="field">
        <span class="field-label">Електронна пошта</span>
        <input
          v-model="form.email"
          type="email"
          class="field-input"
          placeholder="you@estro.app"
          autocomplete="email"
          required
        />
      </label>

      <label class="field">
        <span class="field-label">Пароль</span>
        <PasswordInput
          v-model="form.password"
          placeholder="••••••••"
          autocomplete="current-password"
          required
        />
      </label>

      <button class="auth-submit" type="submit" :disabled="submitting">
        {{ submitting ? 'Входимо…' : 'Увійти' }}
      </button>
    </form>

    <p class="auth-footer">
      Ще не маєте акаунту?
      <RouterLink :to="{ name: 'register' }">Створити акаунт</RouterLink>
    </p>
  </AuthShell>
</template>
