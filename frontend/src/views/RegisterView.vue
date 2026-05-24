<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { auth } from '../api'
import { useAuth } from '../composables/useAuth.js'
import AuthShell from '../components/AuthShell.vue'
import PasswordInput from '../components/PasswordInput.vue'

const router = useRouter()
const { setToken } = useAuth()

const form = reactive({ name: '', email: '', password: '', confirm: '' })
const submitting = ref(false)
const errorMessage = ref('')
const fieldError = ref('')

const passwordsMatch = computed(
  () => form.password.length > 0 && form.password === form.confirm,
)

function validate() {
  if (form.name.trim().length < 2) return 'Будь ласка, введіть ваше імʼя.'
  if (!/^\S+@\S+\.\S+$/.test(form.email)) return 'Будь ласка, введіть коректну електронну пошту.'
  if (form.password.length < 8) return 'Пароль має містити щонайменше 8 символів.'
  if (form.password !== form.confirm) return 'Паролі не співпадають.'
  return ''
}

async function handleSubmit() {
  if (submitting.value) return
  errorMessage.value = ''
  fieldError.value = ''

  const issue = validate()
  if (issue) {
    fieldError.value = issue
    return
  }

  submitting.value = true
  try {
    const data = await auth.register({
      name: form.name.trim(),
      email: form.email.trim(),
      password: form.password,
    })
    if (data?.token) setToken(data.token)
    router.push({ name: 'home' })
  } catch (err) {
    errorMessage.value = err.message || 'Не вдалося створити акаунт. Спробуйте ще раз.'
  } finally {
    form.password = ''
    form.confirm = ''
    submitting.value = false
  }
}
</script>

<template>
  <AuthShell title="Створіть акаунт" subtitle="Приєднуйтесь до Estro за лічені секунди.">
    <form class="auth-form" novalidate @submit.prevent="handleSubmit">
      <div v-if="errorMessage" class="auth-alert" role="alert">
        {{ errorMessage }}
      </div>
      <div v-else-if="fieldError" class="auth-alert" role="alert">
        {{ fieldError }}
      </div>

      <label class="field">
        <span class="field-label">Імʼя</span>
        <input
          v-model="form.name"
          type="text"
          class="field-input"
          placeholder="Ваше імʼя"
          autocomplete="name"
          required
        />
      </label>

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
          placeholder="Щонайменше 8 символів"
          autocomplete="new-password"
          minlength="8"
          required
        />
      </label>

      <label class="field">
        <span class="field-label">Підтвердження паролю</span>
        <PasswordInput
          v-model="form.confirm"
          placeholder="Повторіть пароль"
          autocomplete="new-password"
          required
          :has-error="form.confirm.length > 0 && !passwordsMatch"
        />
        <span v-if="form.confirm.length > 0 && !passwordsMatch" class="field-error">
          Паролі поки не співпадають.
        </span>
      </label>

      <button class="auth-submit" type="submit" :disabled="submitting">
        {{ submitting ? 'Створюємо акаунт…' : 'Створити акаунт' }}
      </button>
    </form>

    <p class="auth-footer">
      Вже маєте акаунт?
      <RouterLink :to="{ name: 'login' }">Увійти</RouterLink>
    </p>
  </AuthShell>
</template>
