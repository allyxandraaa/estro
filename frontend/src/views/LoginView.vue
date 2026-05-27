<script setup>
import { reactive, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { auth } from '../api'

const router = useRouter()

const form = reactive({ email: '', password: '' })
const submitting = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  if (submitting.value) return
  errorMessage.value = ''
  submitting.value = true

  try {
    await auth.login({ email: form.email, password: form.password })
    router.push({ name: 'home' })
  } catch (err) {
    errorMessage.value = err.message || 'Не вдалося увійти. Спробуйте ще раз.'
  } finally {
    form.password = ''
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
      <span>Sign in to keep listening to you cycle, hormones</span>
      <span>and the patterns underneath.</span>
    </p>

    <form class="auth-form" novalidate @submit.prevent="handleSubmit">
      <p v-if="errorMessage" class="auth-error" role="alert">{{ errorMessage }}</p>

      <div class="field">
        <label class="field-label" for="login-email">email</label>
        <input
          id="login-email"
          v-model="form.email"
          type="email"
          class="field-input"
          autocomplete="email"
          required
        />
      </div>

      <div class="field">
        <label class="field-label" for="login-password">password</label>
        <input
          id="login-password"
          v-model="form.password"
          type="password"
          class="field-input"
          autocomplete="current-password"
          required
        />
        <a class="field-meta" href="#" @click.prevent>forgot your password?</a>
      </div>

      <button class="auth-submit" type="submit" :disabled="submitting">
        {{ submitting ? 'Signing in…' : 'Continue' }}
      </button>
    </form>

    <p class="auth-footer">
      New here?
      <RouterLink :to="{ name: 'register' }">Create an account.</RouterLink>
    </p>
  </div>
</template>

<style scoped>
/*
 * Figma frame is 1440×1024 with these vertical gaps (px → % of 670 total gap budget):
 *   top-of-frame → heading       203  (30.3%)
 *   heading      → subtitle       28  ( 4.2%)
 *   subtitle     → form           84  (12.5%)
 *   field        → field          26  ( 3.9%)
 *   form         → button         84  (12.5%)
 *   button       → footer        178  (26.6%)
 *   footer       → bottom-of-frame 67 (10.0%)
 * Fixed content (heading 130 + subtitle 44 + 2×field 104 + button 54 + footer 22) = 354px.
 * Each gap is a share of the remaining viewport, * 0.92 so a sliver of slack is left over.
 */
.auth-page {
  --fixed-content: 354px;
  --gap-budget: max(0px, calc((100vh - var(--fixed-content)) * 0.92));

  height: 100vh;
  width: 100%;
  overflow: hidden;
  background: #fff;
  color: #000;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 24px;
}

.auth-heading {
  font-family: 'Instrument Serif', 'Times New Roman', serif;
  font-weight: 400;
  font-size: 65px;
  line-height: 1;
  text-align: center;
  letter-spacing: -0.005em;
  margin-top: calc(var(--gap-budget) * 0.303);
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
  margin-top: calc(var(--gap-budget) * 0.042);
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
  margin-top: calc(var(--gap-budget) * 0.125);
}

.auth-error {
  font-family: 'Geist', sans-serif;
  font-size: 13px;
  color: #c4365b;
  text-align: center;
}

.field + .field {
  margin-top: calc(var(--gap-budget) * 0.039);
}

.field {
  position: relative;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid rgba(0, 0, 0, 0.4);
  padding-bottom: 6px;
  height: 52px;
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

.field-meta {
  position: absolute;
  right: 0;
  bottom: 8px;
  font-family: 'Geist', sans-serif;
  font-size: 11px;
  color: rgba(0, 0, 0, 0.4);
}

.field-meta:hover {
  color: rgba(0, 0, 0, 0.7);
}

.auth-submit {
  margin-top: calc(var(--gap-budget) * 0.125);
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
  margin-top: calc(var(--gap-budget) * 0.266);
  margin-bottom: calc(var(--gap-budget) * 0.100);
}

.auth-footer a {
  text-decoration: underline;
  text-underline-offset: 2px;
}

.auth-footer a:hover {
  opacity: 0.7;
}
</style>
