<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { onboarding as onboardingApi } from '../api'
import logoUrl from '../assets/logo.svg'

import starFilledUrl from '../assets/star-filled.svg'
import starOutlineUrl from '../assets/star-outline.svg'

const router = useRouter()

const step = ref(0)
const cycleLength = ref(28)
const periodLength = ref(5)
const lastPeriodDate = ref('')
const today = new Date().toISOString().split('T')[0]
const skipMsg = ref('')
const submitting = ref(false)
const error = ref('')

let skipTimer = null

function clearSkip() {
  clearTimeout(skipTimer)
  skipMsg.value = ''
}

onUnmounted(() => clearTimeout(skipTimer))

function goToStep(n) {
  if (n >= 1 && n <= 3) { clearSkip(); error.value = ''; step.value = n }
}

function startOnboarding() { step.value = 1 }

function skipCycle() {
  clearSkip()
  cycleLength.value = 28
  skipMsg.value = 'Ми автоматично встановимо середню медичну норму — 28 днів. Ви зможете змінити це пізніше в налаштуваннях.'
  skipTimer = setTimeout(() => { clearSkip(); step.value = 2 }, 2000)
}

function continueCycle() {
  const v = Number(cycleLength.value)
  if (!Number.isInteger(v) || v < 1 || v > 90) {
    error.value = 'Тривалість циклу: введіть число від 1 до 90 днів.'
    return
  }
  clearSkip(); error.value = ''; step.value = 2
}

function skipPeriod() {
  clearSkip()
  periodLength.value = 5
  skipMsg.value = 'Ми автоматично встановимо середню тривалість менструації — 5 днів. За потреби це можна буде змінити пізніше.'
  skipTimer = setTimeout(() => { clearSkip(); step.value = 3 }, 2000)
}

function continuePeriod() {
  const v = Number(periodLength.value)
  if (!Number.isInteger(v) || v < 1 || v > 20) {
    error.value = 'Тривалість менструації: введіть число від 1 до 20 днів.'
    return
  }
  if (v >= Number(cycleLength.value)) {
    error.value = 'Тривалість менструації має бути меншою за тривалість циклу.'
    return
  }
  clearSkip(); error.value = ''; step.value = 3
}

async function submitOnboarding() {
  if (submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    await onboardingApi.completeOnboarding({
      cycle_length: Number(cycleLength.value),
      period_length: Number(periodLength.value),
      last_period_date: lastPeriodDate.value || null,
    })
    step.value = 4
  } catch (err) {
    error.value = err.message || 'Не вдалося зберегти дані. Спробуйте ще раз.'
  } finally {
    submitting.value = false
  }
}

function goHome() { router.push({ name: 'home' }) }
</script>

<template>
  <div class="ob-page">

    <!-- key на контейнері: при зміні step — елемент перемонтується
         і CSS-анімація grabs стартує без "порожнього" кадру між кроками -->
    <div :key="step" class="ob-screen">

      <!-- ── 0: Intro ── -->
      <div v-if="step === 0" class="ob-intro">
        <img class="ob-logo" :src="logoUrl" alt="" />
        <h1 class="ob-intro-heading">
          <span class="ob-line">Допоможіть нам</span>
          <span class="ob-line">налаштувати ваш цикл</span>
        </h1>
        <p class="ob-sub">
          Відповіді займуть менше хвилини та допоможуть створити персоналізовані прогнози й рекомендації.
        </p>
        <button class="ob-btn ob-btn--primary" @click="startOnboarding">Продовжити</button>
      </div>

      <!-- ── 1: Тривалість циклу ── -->
      <div v-else-if="step === 1" class="ob-question">
        <h1 class="ob-q-heading">
          <span class="ob-line">Скільки днів зазвичай</span>
          <span class="ob-line">триває ваш менструальний цикл?</span>
        </h1>
        <p class="ob-q-hint">**від першого дня менструації до першого дня наступної.</p>
        <div class="ob-number-box">
          <input
            v-model.number="cycleLength"
            type="number" min="1" max="99"
            class="ob-number-input"
          />
        </div>
        <p v-if="skipMsg" class="ob-skip-msg">{{ skipMsg }}</p>
        <p v-if="error" class="ob-error" role="alert">{{ error }}</p>
        <div class="ob-actions">
          <button class="ob-btn ob-btn--outlined" @click="skipCycle">Не пам'ятаю</button>
          <button class="ob-btn ob-btn--primary" @click="continueCycle">Продовжити</button>
        </div>
        <nav class="ob-stars" aria-label="Навігація по кроках">
          <button
            v-for="i in 4" :key="i"
            class="ob-star-btn"
            :aria-label="`Крок ${i}`"
            @click="goToStep(i)"
          >
            <img :src="i <= step ? starFilledUrl : starOutlineUrl" width="36" height="36" alt="" />
          </button>
        </nav>
      </div>

      <!-- ── 2: Тривалість менструації ── -->
      <div v-else-if="step === 2" class="ob-question">
        <h1 class="ob-q-heading">
          <span class="ob-line">Скільки днів зазвичай</span>
          <span class="ob-line">триває ваша менструація?</span>
        </h1>
        <p class="ob-q-hint">**від першого до останнього дня кровотечі.</p>
        <div class="ob-number-box">
          <input
            v-model.number="periodLength"
            type="number" min="1" max="20"
            class="ob-number-input"
          />
        </div>
        <p v-if="skipMsg" class="ob-skip-msg">{{ skipMsg }}</p>
        <p v-if="error" class="ob-error" role="alert">{{ error }}</p>
        <div class="ob-actions">
          <button class="ob-btn ob-btn--outlined" @click="skipPeriod">Не пам'ятаю</button>
          <button class="ob-btn ob-btn--primary" @click="continuePeriod">Продовжити</button>
        </div>
        <nav class="ob-stars" aria-label="Навігація по кроках">
          <button
            v-for="i in 4" :key="i"
            class="ob-star-btn"
            :aria-label="`Крок ${i}`"
            @click="goToStep(i)"
          >
            <img :src="i <= step ? starFilledUrl : starOutlineUrl" width="36" height="36" alt="" />
          </button>
        </nav>
      </div>

      <!-- ── 3: Дата останньої менструації ── -->
      <div v-else-if="step === 3" class="ob-question ob-question--date">
        <h1 class="ob-q-heading">
          <span class="ob-line">Коли почалася ваша</span>
          <span class="ob-line">остання менструація?</span>
        </h1>
        <div class="ob-calendar-box">
          <input v-model="lastPeriodDate" type="date" class="ob-date-input" lang="uk" :max="today" placeholder="дд/мм/рррр" />
        </div>
        <p v-if="error" class="ob-error" role="alert">{{ error }}</p>
        <div class="ob-actions">
          <button class="ob-btn ob-btn--outlined" :disabled="submitting" @click="submitOnboarding">Пропустити</button>
          <button class="ob-btn ob-btn--primary" :disabled="submitting" @click="submitOnboarding">
            {{ submitting ? 'Зберігаємо…' : 'Продовжити' }}
          </button>
        </div>
        <nav class="ob-stars" aria-label="Навігація по кроках">
          <button
            v-for="i in 4" :key="i"
            class="ob-star-btn"
            :aria-label="`Крок ${i}`"
            @click="goToStep(i)"
          >
            <img :src="i <= step ? starFilledUrl : starOutlineUrl" width="36" height="36" alt="" />
          </button>
        </nav>
      </div>

      <!-- ── 4: Успіх ── -->
      <div v-else-if="step === 4" class="ob-success">
        <img class="ob-logo" :src="logoUrl" alt="" />
        <h1 class="ob-success-heading">Профіль налаштовано</h1>
        <p class="ob-sub">
          Ми підготували для вас персональний прогноз циклу та рекомендації.
        </p>
        <button class="ob-btn ob-btn--primary" @click="goHome">Перейти до календаря</button>
        <nav class="ob-stars ob-stars--success" aria-label="Навігація по кроках">
          <button
            v-for="i in 4" :key="i"
            class="ob-star-btn"
            :aria-label="`Крок ${i}`"
            @click="goToStep(i)"
          >
            <img :src="starFilledUrl" width="36" height="36" alt="" />
          </button>
        </nav>
      </div>

    </div>
  </div>
</template>

<style scoped>
/*
 * Gap-budget система: кожен тип екрану має --gap = max(0, 100vh − fixed_px).
 * Всі відступи — частки --gap, тому однорідно стискаються на будь-якому екрані.
 *
 * Пропорції взяті з Figma (розміри у 1440×1024):
 *   intro   fixed=290px  gap=734  top=40.1% logo→h=1.9% h→sub=7.6% sub→btn=10.3%
 *   q       fixed=443px  gap=581  top=28.7% h→hint=9.3% hint→box=15.8% box→act=16% act→★=9.3%
 *   q-date  fixed=619px  gap=405  top=31.9% h→cal=11.1% cal→act=10.4% act→★=13.3%
 *   success fixed=261px  gap=763  top=47.7% logo→h=1.8% h→sub=6.9% sub→btn=10% btn→★=19.1%
 */

/* ── Page ── */
.ob-page {
  position: relative;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  background: transparent;
  color: #000;
}

/* ── Screen: CSS-анімація при перемонтуванні (key=step) ── */
.ob-screen {
  height: 100%;
  width: 100%;
  animation: ob-fadein 0.28s ease both;
}
@keyframes ob-fadein {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: none; }
}

/* ── Shared ── */
.ob-line { display: block; white-space: nowrap; }
.ob-logo { width: 93px; height: 57px; object-fit: contain; }

/* ═══════════════════════════
   INTRO  fixed=290px
═══════════════════════════ */
.ob-intro {
  --gap: max(0px, calc(100vh - 290px));
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0 24px;
}

.ob-intro .ob-logo {
  margin-top: calc(var(--gap) * 0.401);
  margin-bottom: calc(var(--gap) * 0.019);
}

.ob-intro-heading {
  font-family: 'Instrument Serif', 'Times New Roman', serif;
  font-weight: 400;
  font-size: 65px;
  line-height: 1;
  letter-spacing: -0.005em;
  margin: 0 0 calc(var(--gap) * 0.076);
}

.ob-sub {
  font-family: 'Geist', sans-serif;
  font-size: 17px;
  line-height: 1.45;
  color: rgba(0, 0, 0, 0.7);
  max-width: 516px;
  text-align: center;
}

.ob-intro .ob-sub { margin: 0 0 calc(var(--gap) * 0.103); }

/* ═══════════════════════════
   ПИТАННЯ  fixed=443px
   (цикл і менструація)
═══════════════════════════ */
.ob-question {
  --gap: max(0px, calc(100vh - 443px));
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 24px;
  padding-top: calc(var(--gap) * 0.287);
}

.ob-q-heading {
  font-family: 'Instrument Serif', 'Times New Roman', serif;
  font-weight: 400;
  font-size: 64px;
  line-height: 1.05;
  letter-spacing: -0.005em;
  text-align: center;
  margin: 0 0 calc(var(--gap) * 0.093);
}

.ob-q-hint {
  font-family: 'Geist', sans-serif;
  font-size: 17px;
  line-height: 1.3;
  color: rgba(0, 0, 0, 0.55);
  text-align: center;
  margin: 0 0 calc(var(--gap) * 0.158);
}

.ob-number-box {
  width: 149px;
  height: 135px;
  border: 2px solid #000;
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin: 0 0 calc(var(--gap) * 0.160);
}

/* Коли повідомлення активне — стискаємо відступ рамки,
   щоб message + actions + зірочки все одно влазили */
.ob-number-box + .ob-skip-msg {
  margin-top: calc(var(--gap) * -0.100); /* поглинаємо частину нижнього відступу box */
  margin-bottom: calc(var(--gap) * 0.060);
}

.ob-skip-msg {
  font-family: 'Geist', sans-serif;
  font-size: 14px;
  line-height: 1.4;
  color: rgba(0, 0, 0, 0.55);
  text-align: center;
  max-width: 359px;
  flex-shrink: 0;
  animation: ob-fadein 0.35s ease both;
}

.ob-number-input {
  width: 100%;
  height: 100%;
  text-align: center;
  font-family: 'Instrument Serif', 'Times New Roman', serif;
  font-weight: 400;
  font-size: 80px;
  line-height: 1;
  color: #000;
  background: transparent;
  border: none;
  outline: none;
  padding: 0;
  -moz-appearance: textfield;
}
.ob-number-input::-webkit-inner-spin-button,
.ob-number-input::-webkit-outer-spin-button { -webkit-appearance: none; }

.ob-question .ob-actions { margin-bottom: calc(var(--gap) * 0.093); }

/* ═══════════════════════════
   ДАТА  fixed=619px
═══════════════════════════ */
.ob-question--date {
  --gap: max(0px, calc(100vh - 619px));
  padding-top: calc(var(--gap) * 0.319);
}

.ob-question--date .ob-q-heading {
  margin-bottom: calc(var(--gap) * 0.111);
}

.ob-calendar-box {
  width: min(772px, calc(100vw - 48px));
  height: 333px;
  border: 2px solid #000;
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin: 0 0 calc(var(--gap) * 0.104);
}

.ob-date-input {
  font-family: 'Geist', sans-serif;
  font-size: 22px;
  color: #000;
  background: transparent;
  border: none;
  outline: none;
  cursor: pointer;
}

.ob-question--date .ob-actions { margin-bottom: calc(var(--gap) * 0.133); }

/* ── Дії (спільне) ── */
.ob-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 359px;
  flex-shrink: 0;
}

/* ── Кнопки ── */
.ob-btn {
  width: 100%;
  max-width: 359px;
  height: 54px;
  flex-shrink: 0;
  border-radius: 7px;
  font-family: 'Geist', sans-serif;
  font-size: 17px;
  cursor: pointer;
  transition: opacity 0.15s ease, transform 0.1s ease;
}
.ob-btn--primary  { background: #000; color: #fff; border: none; }
.ob-btn--outlined { background: transparent; color: #000; border: 2px solid #000; }
.ob-btn:hover:not(:disabled)  { opacity: 0.82; }
.ob-btn:active:not(:disabled) { transform: translateY(1px); }
.ob-btn:disabled { opacity: 0.55; cursor: not-allowed; }

/* ── Помилка ── */
.ob-error {
  font-family: 'Geist', sans-serif;
  font-size: 13px;
  color: #c4365b;
  text-align: center;
  margin-bottom: 8px;
  align-self: center;
}

/* ── Зірочки ── */
.ob-stars {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-shrink: 0;
}
.ob-star-btn {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  transition: opacity 0.15s ease;
}
.ob-star-btn:hover { opacity: 0.6; }

/* ═══════════════════════════
   УСПІХ  fixed=261px
═══════════════════════════ */
.ob-success {
  --gap: max(0px, calc(100vh - 261px));
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0 24px;
}

.ob-success .ob-logo {
  margin-top: calc(var(--gap) * 0.477);
  margin-bottom: calc(var(--gap) * 0.018);
}

.ob-success-heading {
  font-family: 'Instrument Serif', 'Times New Roman', serif;
  font-weight: 400;
  font-size: 65px;
  line-height: 1;
  letter-spacing: -0.005em;
  white-space: nowrap;
  margin: 0 0 calc(var(--gap) * 0.069);
}

.ob-success .ob-sub    { margin: 0 0 calc(var(--gap) * 0.100); }
.ob-success .ob-btn    { margin-bottom: calc(var(--gap) * 0.191); }

/* ── Responsive ── */
@media (max-width: 640px) {
  .ob-intro-heading,
  .ob-success-heading { font-size: 42px; }
  .ob-q-heading       { font-size: 38px; }
  .ob-line            { white-space: normal; }
  .ob-number-input    { font-size: 60px; }
  .ob-calendar-box    { height: 200px; }
}
</style>
