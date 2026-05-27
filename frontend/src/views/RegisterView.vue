<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { auth } from '../api'

const router = useRouter()

const form = reactive({ email: '', password: '', confirm: '' })
const submitting = ref(false)
const errorMessage = ref('')

const mismatched = computed(
  () => form.confirm.length > 0 && form.password !== form.confirm,
)

function validate() {
  if (!/^\S+@\S+\.\S+$/.test(form.email)) return 'Введіть коректну електронну пошту.'
  if (form.password.length < 8) return 'Пароль має містити щонайменше 8 символів.'
  if (form.password !== form.confirm) return 'Паролі не збігаються.'
  return ''
}

async function handleSubmit() {
  if (submitting.value) return
  errorMessage.value = ''

  const issue = validate()
  if (issue) {
    errorMessage.value = issue
    return
  }

  submitting.value = true
  try {
    await auth.register({
      name: form.email.trim().split('@')[0],
      email: form.email.trim(),
      password: form.password,
    })
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
  <div class="auth-page">
    <h1 class="auth-heading">
      <span class="auth-heading-line">Welcome back</span>
      <span class="auth-heading-line">to <em>your rhythm</em>.</span>
    </h1>
    <p class="auth-subtitle">
      <span>Register to keep listening to you cycle, hormones</span>
      <span>and the patterns underneath.</span>
    </p>

    <form class="auth-form" novalidate @submit.prevent="handleSubmit">
      <p v-if="errorMessage" class="auth-error" role="alert">{{ errorMessage }}</p>

      <div class="field">
        <label class="field-label" for="register-email">email</label>
        <input
          id="register-email"
          v-model="form.email"
          type="email"
          class="field-input"
          autocomplete="email"
          required
        />
      </div>

      <div class="field">
        <label class="field-label" for="register-password">password</label>
        <input
          id="register-password"
          v-model="form.password"
          type="password"
          class="field-input"
          autocomplete="new-password"
          minlength="8"
          required
        />
      </div>

      <div class="field" :class="{ 'field--error': mismatched }">
        <label class="field-label" for="register-confirm">confirm your password</label>
        <input
          id="register-confirm"
          v-model="form.confirm"
          type="password"
          class="field-input"
          autocomplete="new-password"
          required
        />
      </div>

      <button class="auth-submit" type="submit" :disabled="submitting">
        {{ submitting ? 'Creating account…' : 'Register' }}
      </button>
    </form>

    <p class="auth-footer">
      Already have an account?
      <RouterLink :to="{ name: 'login' }">Sign in.</RouterLink>
    </p>
  </div>
</template>

<style scoped>
/*
 * Same gap ratios as the Figma login frame, but with one extra field-gap factored in
 * (3 fields instead of 2). Gap-budget percentages sum to 1.0 over the 696px total.
 *   top                203  (29.2%)
 *   heading→subtitle    28  ( 4.0%)
 *   subtitle→form       84  (12.1%)
 *   field-gap each      26  ( 3.7%)  ×2 instances
 *   form→button         84  (12.1%)
 *   button→footer      178  (25.6%)
 *   footer→bottom       67  ( 9.6%)
 * Fixed content (heading 130 + subtitle 44 + 3×field 156 + button 54 + footer 22) = 406px.
 */
.auth-page {
  --fixed-content: 406px;
  --gap-budget: max(0px, calc((100vh - var(--fixed-content)) * 0.92));

  position: relative;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  background: transparent;
  color: #000;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 24px;
}

.auth-heading,
.auth-subtitle,
.auth-form,
.auth-footer {
  position: relative;
  z-index: 1;
}

.auth-page {
  animation: fade-in 0.6s ease both;
}

@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.auth-heading {
  font-family: 'Instrument Serif', 'Times New Roman', serif;
  font-weight: 400;
  font-size: 65px;
  line-height: 1;
  text-align: center;
  letter-spacing: -0.005em;
  margin-top: calc(var(--gap-budget) * 0.292);
}

.auth-heading-line {
  display: block;
  white-space: nowrap;
}

.auth-heading em {
  font-style: italic;
}

.auth-subtitle {
  font-family: 'Geist', sans-serif;
  font-size: 17px;
  line-height: 1.3;
  text-align: center;
  margin-top: calc(var(--gap-budget) * 0.040);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.auth-subtitle > span {
  display: block;
  white-space: nowrap;
}

.auth-form {
  width: 100%;
  max-width: 359px;
  display: flex;
  flex-direction: column;
  margin-top: calc(var(--gap-budget) * 0.121);
}

.auth-error {
  font-family: 'Geist', sans-serif;
  font-size: 13px;
  color: #c4365b;
  text-align: center;
}

.field + .field {
  margin-top: calc(var(--gap-budget) * 0.037);
}

.field {
  position: relative;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid rgba(0, 0, 0, 0.4);
  padding-bottom: 6px;
  height: 52px;
  transition: border-color 0.15s ease;
}

.field--error {
  border-bottom-color: #c4365b;
}

.field-label {
  font-family: 'Geist', sans-serif;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.4);
}

.field-input {
  background: transparent;
  border: none;
  outline: none;
  padding: 4px 0 0;
  font-family: 'Geist', sans-serif;
  font-size: 16px;
  color: #000;
  width: 100%;
}

.auth-submit {
  margin-top: calc(var(--gap-budget) * 0.121);
  height: 54px;
  flex-shrink: 0;
  border-radius: 7px;
  background: #000;
  color: #fff;
  font-family: 'Geist', sans-serif;
  font-size: 17px;
  border: none;
  cursor: pointer;
  transition: background 0.15s ease, transform 0.1s ease;
}

.auth-submit:hover:not(:disabled) {
  background: #1a1a1a;
}

.auth-submit:active:not(:disabled) {
  transform: translateY(1px);
}

.auth-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-footer {
  font-family: 'Geist', sans-serif;
  font-size: 17px;
  text-align: center;
  margin-top: calc(var(--gap-budget) * 0.256);
  margin-bottom: calc(var(--gap-budget) * 0.096);
}

.auth-footer a {
  text-decoration: underline;
  text-underline-offset: 2px;
}

.auth-footer a:hover {
  opacity: 0.7;
}
</style>
