<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { deleteDailyLog, getDailyLog, saveDailyLog } from '../api/daily-logs.js'
import logoUrl from '../assets/logo.svg'
import starFilledUrl from '../assets/star-filled.svg'
import starOutlineUrl from '../assets/star-outline.svg'

const router = useRouter()

const today = toDateParam(new Date())
const selectedDate = ref(today)
const slide = ref(0)
const slideWidth = 1920
const saving = ref(false)
const loading = ref(false)
const message = ref('')
const error = ref('')
const touchStartX = ref(null)

const form = reactive(emptyLog())

const bleedingOptions = [
  { label: 'Відсутня', value: 0 },
  { label: 'Мізерна', value: 1 },
  { label: 'Помірна', value: 3 },
  { label: 'Рясна', value: 5 },
]

const painOptions = [
  { label: 'Немає', value: 'NONE', intensity: 0 },
  { label: 'Спазми', value: 'PELVIC', intensity: 6 },
  { label: 'Біль у спині', value: 'BACK', intensity: 4 },
  { label: 'Біль у грудях', value: 'BREAST', intensity: 4 },
  { label: 'Головний біль', value: 'HEAD', intensity: 4 },
]

const digestionOptions = [
  { label: 'Все добре', value: 'NONE' },
  { label: 'Нудота', value: 'NAUSEA' },
  { label: 'Закреп', value: 'CONSTIPATION' },
  { label: 'Діарея', value: 'DIARRHEA' },
  { label: 'Здуття', value: 'BLOATING' },
]

const appetiteOptions = [
  { label: 'Нормальний', value: 'NORMAL' },
  { label: 'Підвищений', value: 'INCREASED' },
  { label: 'Занижений', value: 'DECREASED' },
  { label: 'Хочеться солодкого', value: 'CRAVING_SWEET' },
  { label: 'Хочеться солоного', value: 'CRAVING_SALTY' },
]

const dischargeOptions = [
  { label: 'Відсутні', value: 'DRY' },
  { label: 'Липкі', value: 'STICKY' },
  { label: 'Білі', value: 'CREAMY' },
  { label: 'Прозорі', value: 'EGG_WHITE' },
  { label: 'Інше', value: 'ABNORMAL' },
]

const hasChanges = computed(() => {
  return Object.values(payload()).some((value) => {
    if (Array.isArray(value)) return value.length > 0
    return value !== null && value !== ''
  })
})

watch(selectedDate, loadLog)
onMounted(loadLog)

function emptyLog() {
  return {
    bleeding_intensity: null,
    basal_temperature: '',
    discharge_type: null,
    pain_intensity: null,
    pain_location: [],
    gastro_symptoms: [],
    appetite_state: null,
    stress_level: null,
    notes: '',
  }
}

function toDateParam(value) {
  const y = value.getFullYear()
  const m = String(value.getMonth() + 1).padStart(2, '0')
  const d = String(value.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function displayDate(value) {
  const [y, m, d] = value.split('-')
  return `${d}.${m}.${y}`
}

function resetForm(log = null) {
  Object.assign(form, emptyLog(), log ?? {})
  form.basal_temperature = log?.basal_temperature ?? ''
  form.pain_location = normalizeArray(log?.pain_location)
  form.gastro_symptoms = Array.isArray(log?.gastro_symptoms) ? [...log.gastro_symptoms] : []
  form.notes = log?.notes ?? ''
}

function normalizeArray(value) {
  if (Array.isArray(value)) return [...value]
  if (typeof value === 'string' && value.includes(',')) return value.split(',').map((item) => item.trim()).filter(Boolean)
  return value ? [value] : []
}

async function loadLog() {
  loading.value = true
  error.value = ''
  message.value = ''
  try {
    const log = await getDailyLog(selectedDate.value)
    resetForm(log)
  } catch (err) {
    resetForm()
    error.value = err.message || 'Не вдалося завантажити запис'
  } finally {
    loading.value = false
  }
}

function payload() {
  const tempText = String(form.basal_temperature ?? '').trim()
  return {
    bleeding_intensity: form.bleeding_intensity,
    basal_temperature: tempText === '' ? null : Number(tempText).toFixed(2),
    discharge_type: form.discharge_type,
    pain_intensity: form.pain_intensity,
    pain_location: form.pain_location.length ? form.pain_location : null,
    gastro_symptoms: form.gastro_symptoms.length ? form.gastro_symptoms : null,
    appetite_state: form.appetite_state,
    stress_level: form.stress_level,
    notes: form.notes.trim() || null,
  }
}

async function submitLog() {
  if (saving.value) return false
  saving.value = true
  error.value = ''
  message.value = ''
  try {
    const saved = await saveDailyLog(selectedDate.value, payload())
    resetForm(saved)
    message.value = 'Збережено'
    return true
  } catch (err) {
    error.value = err.message || 'Не вдалося зберегти запис'
    return false
  } finally {
    saving.value = false
  }
}

async function clearLog() {
  if (saving.value || !hasChanges.value) return
  saving.value = true
  error.value = ''
  message.value = ''
  try {
    await deleteDailyLog(selectedDate.value)
    resetForm()
    message.value = 'Очищено'
  } catch (err) {
    error.value = err.message || 'Не вдалося очистити запис'
  } finally {
    saving.value = false
  }
}

function setBleeding(value) {
  form.bleeding_intensity = form.bleeding_intensity === value ? null : value
}

function setPain(option) {
  if (option.value === 'NONE') {
    form.pain_location = form.pain_location.includes('NONE') ? [] : ['NONE']
    form.pain_intensity = form.pain_location.length ? 0 : null
    return
  }

  form.pain_location = form.pain_location.filter((item) => item !== 'NONE')
  form.pain_location = form.pain_location.includes(option.value)
    ? form.pain_location.filter((item) => item !== option.value)
    : [...form.pain_location, option.value]
  form.pain_intensity = form.pain_location.length
    ? Math.max(...painOptions.filter((item) => form.pain_location.includes(item.value)).map((item) => item.intensity))
    : null
}

function setValue(field, value) {
  form[field] = form[field] === value ? null : value
}

function toggleGastro(value) {
  if (value === 'NONE') {
    form.gastro_symptoms = form.gastro_symptoms.includes('NONE') ? [] : ['NONE']
    return
  }
  form.gastro_symptoms = form.gastro_symptoms.filter((item) => item !== 'NONE')
  form.gastro_symptoms = form.gastro_symptoms.includes(value)
    ? form.gastro_symptoms.filter((item) => item !== value)
    : [...form.gastro_symptoms, value]
}

function goSlide(value) {
  slide.value = Math.max(0, Math.min(1, value))
}

function onTouchStart(event) {
  touchStartX.value = event.touches?.[0]?.clientX ?? null
}

function onTouchEnd(event) {
  if (touchStartX.value === null) return
  const endX = event.changedTouches?.[0]?.clientX ?? touchStartX.value
  const delta = endX - touchStartX.value
  touchStartX.value = null
  if (Math.abs(delta) > 48) goSlide(slide.value + (delta < 0 ? 1 : -1))
}

async function goHome() {
  if (hasChanges.value && !saving.value) {
    const saved = await submitLog()
    if (!saved) return
  }
  router.push({ name: 'home' })
}

function goProfile() {
  router.push({ name: 'profile' })
}
</script>

<template>
  <div class="daily-page" @touchstart.passive="onTouchStart" @touchend.passive="onTouchEnd">
    <nav class="top-nav">
      <img class="brand" :src="logoUrl" alt="Estro" @click="goHome" />
      <div class="nav-btns">
        <button class="nav-btn nav-btn--filled" @click="goHome">До календаря</button>
        <button class="nav-btn nav-btn--outline">Сповіщення</button>
        <button class="nav-btn nav-btn--filled" @click="goProfile">Профіль</button>
      </div>
    </nav>

    <main class="daily-stage" :class="{ 'is-loading': loading }">
      <button class="side-arrow side-arrow--left" :disabled="slide === 0" @click="goSlide(slide - 1)">‹</button>
      <button class="side-arrow side-arrow--right" :disabled="slide === 1" @click="goSlide(slide + 1)">›</button>

      <div class="viewport-fit">
        <div class="slides" :style="{ transform: `translateX(-${slide * slideWidth}px)` }">
        <section class="daily-slide">
          <header class="title-row">
            <h1>Щоденник симптомів</h1>
            <label class="date-label">
              <span>{{ displayDate(selectedDate) }}</span>
              <input v-model="selectedDate" type="date" :max="today" />
            </label>
          </header>

          <div class="daily-grid daily-grid--balanced">
            <div class="daily-column">
              <section class="field-block">
                <h2>Кровотеча:</h2>
                <div class="pills">
                  <button
                    v-for="option in bleedingOptions"
                    :key="option.label"
                    class="pill"
                    :class="{ 'is-active': form.bleeding_intensity === option.value }"
                    @click="setBleeding(option.value)"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </section>

              <section class="field-block">
                <h2>Біль:</h2>
                <div class="pills">
                  <button
                    v-for="option in painOptions"
                    :key="option.label"
                    class="pill"
                    :class="{ 'is-active': form.pain_location.includes(option.value) }"
                    @click="setPain(option)"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </section>

            </div>

            <div class="daily-column daily-column--right">
              <section class="field-block">
                <h2>Базальна температура:</h2>
                <input v-model="form.basal_temperature" class="number-box" inputmode="decimal" placeholder="36.70" />
              </section>

              <section class="field-block">
                <h2>Стрес: {{ form.stress_level ?? 0 }}/10</h2>
                <input v-model.number="form.stress_level" class="range" type="range" min="0" max="10" step="1" />
              </section>

              <section class="field-block">
                <h2>Травлення:</h2>
                <div class="pills">
                  <button
                    v-for="option in digestionOptions"
                    :key="option.label"
                    class="pill"
                    :class="{ 'is-active': form.gastro_symptoms.includes(option.value) }"
                    @click="toggleGastro(option.value)"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </section>
            </div>
          </div>
        </section>

        <section class="daily-slide">
          <header class="title-row">
            <h1>Щоденник симптомів</h1>
            <label class="date-label">
              <span>{{ displayDate(selectedDate) }}</span>
              <input v-model="selectedDate" type="date" :max="today" />
            </label>
          </header>

          <div class="daily-grid">
            <div class="daily-column">
              <section class="field-block">
                <h2>Апетит:</h2>
                <div class="pills">
                  <button
                    v-for="option in appetiteOptions"
                    :key="option.label"
                    class="pill"
                    :class="{ 'is-active': form.appetite_state === option.value }"
                    @click="setValue('appetite_state', option.value)"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </section>

              <section class="field-block">
                <h2>Виділення:</h2>
                <div class="pills">
                  <button
                    v-for="option in dischargeOptions"
                    :key="option.label"
                    class="pill"
                    :class="{ 'is-active': form.discharge_type === option.value }"
                    @click="setValue('discharge_type', option.value)"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </section>
            </div>

            <div class="daily-column daily-column--right">
              <section class="field-block">
                <h2>Нотатки:</h2>
                <textarea v-model="form.notes" class="notes" maxlength="2000" />
              </section>
            </div>
          </div>
        </section>
        </div>
      </div>
    </main>

    <nav class="bottom-stars" aria-label="Сторінки щоденника">
      <button class="star-btn" @click="goSlide(0)">
        <img :src="slide === 0 ? starFilledUrl : starOutlineUrl" alt="" />
      </button>
      <button class="star-btn" @click="goSlide(1)">
        <img :src="slide === 1 ? starFilledUrl : starOutlineUrl" alt="" />
      </button>
    </nav>

    <div class="bottom-actions" :class="{ 'is-open': message || error || saving }">
      <p v-if="message" class="status">{{ message }}</p>
      <p v-if="error" class="status status--error">{{ error }}</p>
      <button class="action-btn action-btn--outline" :disabled="saving || !hasChanges" @click="clearLog">Очистити</button>
      <button class="action-btn action-btn--dark" :disabled="saving" @click="submitLog">
        {{ saving ? 'Збереження...' : 'Зберегти' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.daily-page {
  position: relative;
  width: 100%;
  min-height: 100vh;
  overflow: hidden;
  background: transparent;
  color: #000;
}

.top-nav {
  position: fixed;
  inset: 0 0 auto;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 40px;
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

.nav-btn:hover,
.action-btn:hover,
.pill:hover {
  opacity: 0.8;
}

.nav-btn--filled,
.action-btn--dark {
  background: #000;
  color: #fff;
  border: none;
}

.nav-btn--outline,
.action-btn--outline {
  background: rgba(255, 255, 255, 0.86);
  color: #000;
  border: 2px solid #000;
}

.daily-stage {
  width: 100vw;
  min-height: 100vh;
  transition: opacity 0.15s;
}

.daily-stage.is-loading {
  opacity: 0.58;
  pointer-events: none;
}

.viewport-fit {
  --base-w: 1920;
  --base-h: 840;
  --nav-h: 86px;
  --scale: min(
    calc(100vw / (var(--base-w) * 1px)),
    calc((100vh - var(--nav-h)) / (var(--base-h) * 1px))
  );
  width: calc(var(--base-w) * 1px);
  height: calc(var(--base-h) * 1px);
  overflow: hidden;
  transform: translateX(max(0px, calc((100vw - (var(--base-w) * 1px * var(--scale))) / 2))) scale(var(--scale));
  transform-origin: top left;
}

.slides {
  display: flex;
  width: calc(var(--base-w) * 2px);
  transition: transform 0.36s cubic-bezier(.22, .61, .36, 1);
}

.daily-slide {
  flex: 0 0 calc(var(--base-w) * 1px);
  width: calc(var(--base-w) * 1px);
  height: calc(var(--base-h) * 1px);
  padding: 118px 118px 84px;
}

.title-row {
  display: flex;
  align-items: baseline;
  gap: 24px;
  margin-bottom: 28px;
}

.title-row h1 {
  margin: 0;
  font-family: 'Instrument Serif', 'Times New Roman', serif;
  font-size: clamp(42px, 5.6vw, 78px);
  font-weight: 400;
  line-height: 1.05;
  letter-spacing: 0;
}

.date-label {
  position: relative;
  display: inline-flex;
  align-items: center;
  margin-left: 12px;
  transform: translateY(10px);
  font-family: 'Geist', sans-serif;
  font-size: 16px;
  color: rgba(0, 0, 0, 0.62);
}

.date-label input {
  position: absolute;
  inset: -14px -8px;
  opacity: 0;
  cursor: pointer;
}

.daily-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(380px, 0.95fr);
  gap: 68px;
  max-width: 1500px;
}

.daily-grid--balanced {
  grid-template-columns: minmax(0, 0.98fr) minmax(420px, 1.02fr);
}

.field-block {
  margin-bottom: 30px;
}

.field-block h2 {
  margin: 0 0 18px;
  font-family: 'Geist', sans-serif;
  font-size: 20px;
  font-weight: 400;
  line-height: 1;
}

.pills {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 22px;
}

.pill {
  min-width: 124px;
  height: 48px;
  padding: 0 26px;
  border: 2px solid #000;
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.86);
  color: #000;
  font-family: 'Geist', sans-serif;
  font-size: 16px;
  white-space: nowrap;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s, background 0.12s, color 0.12s;
}

.pill.is-active {
  background: #000;
  color: #fff;
}

.pill:active,
.action-btn:active {
  transform: translateY(1px);
}

.number-box,
.notes {
  border: 2px solid #000;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.86);
  color: #000;
  font-family: 'Geist', sans-serif;
  outline: none;
}

.number-box {
  width: 168px;
  height: 50px;
  padding: 0 18px;
  font-size: 20px;
}

.range {
  width: min(430px, 100%);
  accent-color: #000;
}

.notes {
  width: min(496px, 100%);
  height: 128px;
  padding: 14px;
  font-size: 17px;
  line-height: 1.45;
  resize: none;
}

.bottom-stars {
  position: fixed;
  left: 50%;
  bottom: 20px;
  z-index: 5;
  display: flex;
  gap: 13px;
  transform: translateX(-50%);
}

.star-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.star-btn img {
  display: block;
  width: 36px;
  height: 36px;
}

.bottom-actions {
  position: fixed;
  right: 50px;
  bottom: 32px;
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 0;
  pointer-events: none;
  transform: translateY(10px);
  transition: opacity 0.16s, transform 0.16s;
}

.daily-page:hover .bottom-actions,
.bottom-actions.is-open {
  opacity: 1;
  pointer-events: auto;
  transform: none;
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

.action-btn:disabled {
  opacity: 0.42;
  cursor: default;
}

.status {
  margin: 0 8px 0 0;
  font-family: 'Geist', sans-serif;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.62);
}

.status--error {
  color: #c4365b;
}

.side-arrow {
  position: fixed;
  top: 50%;
  z-index: 6;
  width: 42px;
  height: 62px;
  border: 2px solid #000;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.86);
  color: #000;
  font-size: 32px;
  opacity: 0;
  cursor: pointer;
  transform: translateY(-50%);
  transition: opacity 0.14s, transform 0.1s;
}

.daily-page:hover .side-arrow:not(:disabled) {
  opacity: 1;
}

.side-arrow:disabled {
  pointer-events: none;
}

.side-arrow--left {
  left: 14px;
}

.side-arrow--right {
  right: 14px;
}

@media (max-width: 900px) {
  .top-nav {
    padding: 16px 18px;
  }

  .nav-btn {
    height: 38px;
    padding: 0 12px;
    font-size: 13px;
  }

  .daily-slide {
    padding: 104px 24px 130px;
    overflow-y: auto;
  }

  .title-row {
    display: block;
    margin-bottom: 28px;
  }

  .title-row h1 {
    margin-bottom: 14px;
    font-size: 42px;
  }

  .daily-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .field-block {
    margin-bottom: 34px;
  }

  .pill {
    min-width: 0;
    height: 46px;
    padding: 0 18px;
    font-size: 14px;
  }

  .bottom-actions {
    left: 14px;
    right: 14px;
    justify-content: flex-end;
  }
}
</style>
