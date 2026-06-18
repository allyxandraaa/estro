<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import { getProfile, updateProfile } from '../api/profile.js'
import logoUrl from '../assets/logo.svg'
import profileStarOutlineUrl from '../assets/profile-star-outline.svg'
import profileStarFilledUrl from '../assets/profile-star-filled.svg'

const router = useRouter()
const { logout } = useAuth()

const profile = reactive({
  name: '',
  email: '',
  average_cycle_length: null,
  average_period_length: null,
})

const initialProfile = ref(null)
const loading = ref(true)
const message = ref('')
const error = ref('')
const fieldErrors = reactive({
  name: '',
  email: '',
})

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function applyProfile(data) {
  profile.name = data.name ?? ''
  profile.email = data.email ?? ''
  profile.average_cycle_length = data.average_cycle_length
  profile.average_period_length = data.average_period_length
  initialProfile.value = { ...profile }
}

async function loadProfile() {
  loading.value = true
  error.value = ''
  try {
    applyProfile(await getProfile())
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function saveProfile(payload) {
  error.value = ''
  try {
    const updated = await updateProfile(payload)
    applyProfile(updated)
    return true
  } catch (e) {
    error.value = e.message
    return false
  }
}

function setFieldError(field, text) {
  fieldErrors[field] = text
  error.value = text
  return false
}

function clearFieldError(field) {
  fieldErrors[field] = ''
  if (!Object.values(fieldErrors).some(Boolean)) error.value = ''
}

function validateName() {
  const value = profile.name.trim()
  if (!value) return setFieldError('name', "Ім'я не може бути порожнім")
  if (value.length > 255) return setFieldError('name', "Ім'я не може бути довшим за 255 символів")
  clearFieldError('name')
  return true
}

function validateEmail() {
  const value = profile.email.trim()
  if (!value) return setFieldError('email', 'E-mail не може бути порожнім')
  if (!EMAIL_RE.test(value)) return setFieldError('email', 'Введіть коректний e-mail')
  clearFieldError('email')
  return true
}

function collectProfileChanges() {
  if (!initialProfile.value) return null

  const changes = {}
  const name = profile.name.trim()
  const email = profile.email.trim()

  if (name !== initialProfile.value.name) {
    if (!validateName()) return null
    changes.name = name
  }

  if (email !== initialProfile.value.email) {
    if (!validateEmail()) return null
    changes.email = email
  }

  return changes
}

async function savePendingChanges() {
  if (loading.value || !initialProfile.value) return true
  const changes = collectProfileChanges()
  if (!changes) return true
  if (Object.keys(changes).length === 0) return true
  return await saveProfile(changes)
}

function goHome() {
  router.push({ name: 'home' }).catch(() => {})
}

function goProfile() {
  router.push({ name: 'profile' }).catch(() => {})
}

function goBack() {
  if (window.history.length > 1) router.back()
  else goHome()
}

function handleNotifications() {
  if (router.hasRoute('notifications')) {
    router.push({ name: 'notifications' }).catch(() => {})
  }
}

async function doLogout() {
  const saved = await savePendingChanges()
  if (!saved) return
  logout()
  router.push({ name: 'login' })
}

function downloadSymptoms() {
  message.value = 'Історія симптомів поки недоступна'
  window.setTimeout(() => {
    message.value = ''
  }, 1800)
}

onMounted(loadProfile)
onBeforeRouteLeave(async () => {
  return await savePendingChanges()
})
</script>

<template>
  <div class="profile-page">
    <nav class="top-nav">
      <img class="brand" :src="logoUrl" alt="Estro" @click="goHome" />
      <div class="nav-btns">
        <button class="nav-btn nav-btn--filled" @click="goHome">До календаря</button>
        <button class="nav-btn nav-btn--outline" @click="handleNotifications">Сповіщення</button>
        <button class="nav-btn nav-btn--filled nav-btn--active" aria-current="page" @click="goProfile">Профіль</button>
      </div>
    </nav>

    <main class="profile-shell" :aria-busy="loading">
      <section class="profile-form">
        <h1>Мій профіль</h1>

        <p v-if="error" class="status status--error" role="alert">{{ error }}</p>
        <p v-else-if="message" class="status" role="status">{{ message }}</p>

        <div class="field-block">
          <label for="profile-name">Ім'я:</label>
          <div class="field-row">
            <input
              id="profile-name"
              v-model="profile.name"
              :disabled="loading"
              :aria-invalid="!!fieldErrors.name"
              type="text"
              autocomplete="name"
              maxlength="255"
              @input="clearFieldError('name')"
            />
          </div>
          <p v-if="fieldErrors.name" class="field-error">{{ fieldErrors.name }}</p>
        </div>

        <div class="field-block">
          <label for="profile-email">Мій e-mail:</label>
          <div class="field-row">
            <input
              id="profile-email"
              v-model="profile.email"
              :disabled="loading"
              :aria-invalid="!!fieldErrors.email"
              type="email"
              autocomplete="email"
              @input="clearFieldError('email')"
            />
          </div>
          <p v-if="fieldErrors.email" class="field-error">{{ fieldErrors.email }}</p>
        </div>

        <div class="metrics">
          <div class="metric-block">
            <span class="metric-label">Середня тривалість циклу</span>
            <span class="metric-value">{{ profile.average_cycle_length ?? '—' }} <span class="metric-unit">днів</span></span>
          </div>
          <div class="metric-block">
            <span class="metric-label">Середня тривалість менструації</span>
            <span class="metric-value">{{ profile.average_period_length ?? '—' }} <span class="metric-unit">днів</span></span>
          </div>
          <p class="metrics-note">Розраховується автоматично з вашої реальної статистики циклів.</p>
        </div>

        <div class="bottom-actions">
          <button class="action-btn action-btn--outline" @click="goBack">Назад</button>
          <button class="action-btn action-btn--dark" @click="doLogout">Вийти</button>
          <button class="action-btn action-btn--dark action-btn--wide" @click="downloadSymptoms">
            Завантажити історію симптомів
          </button>
        </div>
      </section>

      <img class="burst burst--outline" :src="profileStarOutlineUrl" alt="" aria-hidden="true" />
      <img class="burst burst--filled" :src="profileStarFilledUrl" alt="" aria-hidden="true" />
    </main>
  </div>
</template>

<style scoped>
.profile-page {
  position: relative;
  z-index: 1;
  height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  color: #000;
  overflow: hidden;
}

.top-nav {
  position: relative;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 40px;
  flex-shrink: 0;
}

.brand {
  width: auto;
  height: 34px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.brand:hover {
  opacity: 0.55;
}

.nav-btns {
  display: flex;
  gap: 8px;
}

.nav-btn {
  height: 42px;
  border-radius: 7px;
  padding: 0 20px;
  font-family: 'Geist', sans-serif;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 0.15s;
}

.nav-btn:hover {
  opacity: 0.8;
}

.nav-btn--filled {
  background: #000;
  color: #fff;
  border: none;
}

.nav-btn--outline {
  background: transparent;
  color: #000;
  border: 2px solid #000;
}

.action-btn {
  height: 52px;
  border-radius: 7px;
  padding: 0 30px;
  font-family: 'Geist', sans-serif;
  font-size: 15px;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 0.15s, transform 0.1s;
}

.action-btn:hover {
  opacity: 0.8;
}

.action-btn:active {
  transform: translateY(1px);
}

.action-btn--dark {
  background: #000;
  color: #fff;
  border: none;
}

.action-btn--outline {
  background: transparent;
  color: #000;
  border: 2px solid #000;
}

.profile-shell {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  padding: 72px 70px 44px;
  overflow: hidden;
}

.profile-form {
  position: relative;
  z-index: 3;
  width: min(680px, 100%);
}

h1 {
  margin: 0 0 28px;
  font-family: 'Instrument Serif', 'Times New Roman', serif;
  font-size: clamp(42px, 5.6vw, 78px);
  font-weight: 400;
  line-height: 1.05;
  letter-spacing: 0;
}

.status {
  min-height: 22px;
  margin: 0 0 10px;
  font-size: 14px;
  color: #2f5f31;
}

.status--error {
  color: #c40000;
}

.field-block {
  margin-top: 16px;
}

.field-block label,
.metric-block label {
  display: block;
  margin-bottom: 20px;
  font-size: 17px;
}

.field-row {
  width: min(410px, 100%);
}

.field-error {
  margin-top: 8px;
  min-height: 18px;
  font-size: 13px;
  line-height: 1.35;
  color: #c40000;
}

input {
  width: 100%;
  min-height: 54px;
  border: 2px solid #000;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.86);
  padding: 0 30px;
  font-size: 16px;
  outline: none;
}

input[aria-invalid='true'] {
  border-color: #c40000;
}

input:focus-visible,
button:focus-visible {
  outline: 3px solid rgba(0, 0, 0, 0.18);
  outline-offset: 3px;
}

button:disabled,
input:disabled {
  opacity: 0.52;
  cursor: not-allowed;
}

.metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px 34px;
  margin-top: 24px;
  max-width: 610px;
}

.metric-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-label {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.55);
}

.metric-value {
  font-family: 'Instrument Serif', 'Times New Roman', serif;
  font-size: 42px;
  line-height: 1;
  font-weight: 400;
}

.metric-unit {
  font-family: 'Geist', sans-serif;
  font-size: 16px;
  color: rgba(0, 0, 0, 0.6);
}

.metrics-note {
  grid-column: 1 / -1;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.45);
  margin: 0;
}

.bottom-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 22px;
  margin-top: 52px;
}

.bottom-actions .action-btn {
  min-width: 116px;
}

.action-btn--wide {
  min-width: 326px;
}

.burst {
  position: absolute;
  pointer-events: none;
  overflow: visible;
  object-fit: contain;
  user-select: none;
}

.burst--outline {
  right: -130px;
  bottom: -20px;
  width: min(54vw, 650px);
  fill: rgba(255, 255, 255, 0.7);
}

.burst--filled {
  right: -112px;
  bottom: -86px;
  width: min(47vw, 560px);
  fill: #9e9e9e;
}

@media (max-width: 900px) {
  .top-nav {
    padding: 20px 24px;
  }

  .nav-btns {
    gap: 8px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .action-btn {
    padding: 0 18px;
    font-size: 14px;
  }

  .profile-shell {
    padding: 42px 24px 32px;
  }

  .field-row {
    width: min(410px, 100%);
  }

  .metrics {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .burst--outline {
    right: -220px;
    width: 620px;
    opacity: 0.38;
  }

  .burst--filled {
    right: -210px;
    width: 520px;
    opacity: 0.55;
  }
}

@media (max-width: 560px) {
  .top-nav {
    padding: 16px 18px;
  }

  .nav-btns {
    justify-content: flex-end;
  }

  .nav-btn {
    height: 38px;
    padding: 0 12px;
    font-size: 13px;
  }

  .profile-shell {
    padding: 28px 18px 28px;
  }

  .field-row {
    gap: 10px;
  }

  .action-btn--wide {
    width: 100%;
    min-width: 0;
  }

  .bottom-actions {
    margin-top: 30px;
    gap: 12px;
  }

  .bottom-actions .action-btn {
    flex: 1 1 130px;
  }
}
</style>
