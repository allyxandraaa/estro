<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import { getCalendarView, startCycle } from '../api/cycles.js'
import logoUrl from '../assets/logo.svg'

const router = useRouter()
const { logout } = useAuth()

const _today = new Date()

const CELL_W     = 200
const CIRC_BIG   = 174
const CIRC_SMALL = 84
const INFLUENCE  = CELL_W * 1.6

const allDays             = ref([])
const viewMonth           = ref(_today.getMonth() + 1)
const viewYear            = ref(_today.getFullYear())
const currentPhase        = ref('')
const phaseSubtitle       = ref('')
const activeCycle         = ref(null)
const errorMsg            = ref('')
const trackRef            = ref(null)
const pickingMode  = ref(null) // 'start' | 'end' | null
const choosingType = ref(false)
const pickedDay    = ref(null)

const drag = reactive({ active: false, startX: 0, startLeft: 0, moved: false })

let scrollHoldTimer    = null
let scrollHoldInterval = null
let snapTimer          = null
let backwardTimer      = null
let extendTimer        = null
let scaleRafId         = null
let isSnapping         = false

const fetchedMonths = new Set()

const MONTHS       = ['Січень','Лютий','Березень','Квітень','Травень','Червень','Липень','Серпень','Вересень','Жовтень','Листопад','Грудень']
const MONTHS_SHORT = ['січ','лют','бер','кві','тра','чер','лип','сер','вер','жов','лис','гру']
const WEEKDAYS     = ['Нд','Пн','Вт','Ср','Чт','Пт','Сб']

const monthLabel = computed(() => MONTHS[viewMonth.value - 1] + ' ' + viewYear.value)

const hasActivePeriod = computed(() => allDays.value.some(d => d.is_menstruation))

const pickingHint = computed(() => {
  if (!pickingMode.value) return ''
  if (pickedDay.value) return 'Натисніть «Підтвердити» або оберіть інший день'
  if (pickingMode.value === 'start') return 'Оберіть перший день місячних'
  return 'Оберіть останній день місячних'
})


function buildLocalDays(month, year) {
  const now   = new Date()
  const count = new Date(year, month, 0).getDate()
  return Array.from({ length: count }, (_, i) => {
    const d       = new Date(year, month - 1, i + 1)
    const num     = i + 1
    const dateStr = year + '-' + String(month).padStart(2,'0') + '-' + String(num).padStart(2,'0')
    return {
      date:                      dateStr,
      day_of_month:              num,
      weekday:                   WEEKDAYS[d.getDay()],
      mon:                       MONTHS_SHORT[d.getMonth()],
      month, year,
      is_menstruation:           false,
      is_menstruation_predicted: false,
      is_ovulation_predicted:    false,
      is_today:                  d.toDateString() === now.toDateString(),
    }
  })
}

function mergeApiDays(apiDays) {
  if (!apiDays?.length) return
  const map = new Map(apiDays.map(d => [d.date, d]))
  allDays.value = allDays.value.map(d => {
    const api = map.get(d.date)
    return api ? { ...d, ...api, is_today: d.is_today, weekday: d.weekday, mon: d.mon } : d
  })
}

async function fetchMonthData(m, y) {
  const key = y + '-' + m
  if (fetchedMonths.has(key)) return
  fetchedMonths.add(key)
  try {
    const result = await getCalendarView(m, y)
    const data = result?.days ? result : (result?.data ?? {})
    if (data.days) mergeApiDays(data.days)
  } catch { /* graceful */ }
}

function updateScales() {
  const track = trackRef.value
  if (!track) return
  const { scrollLeft, clientWidth } = track
  const viewCenterPx = scrollLeft + clientWidth / 2
  const cullLeft  = scrollLeft - INFLUENCE
  const cullRight = scrollLeft + clientWidth + INFLUENCE
  const cells = track.children

  const startIdx = Math.max(0, Math.floor((cullLeft - clientWidth / 2) / CELL_W))
  const endIdx = Math.min(
    cells.length - 1,
    Math.ceil((cullRight - clientWidth / 2) / CELL_W),
  )

  for (let i = startIdx; i <= endIdx; i++) {
    const cellCenter = clientWidth / 2 + i * CELL_W
    const dist  = Math.abs(cellCenter - viewCenterPx)
    const t     = Math.min(dist / INFLUENCE, 1)
    const sz    = CIRC_SMALL + (CIRC_BIG - CIRC_SMALL) * (1 - t)
    const scale = sz / CIRC_BIG
    const circle = cells[i].firstElementChild
    if (circle) circle.style.transform = 'scale(' + scale.toFixed(4) + ')'
  }
}

function updateMonthLabel() {
  const track = trackRef.value
  if (!track) return
  const centerIdx = Math.round(track.scrollLeft / CELL_W)
  if (centerIdx >= 0 && centerIdx < allDays.value.length) {
    const d = allDays.value[centerIdx]
    viewMonth.value = d.month
    viewYear.value  = d.year
  }
}

function snapToNearest() {
  const track = trackRef.value
  if (!track) return
  updateMonthLabel()
  const nearestIdx = Math.round(track.scrollLeft / CELL_W)
  const target = nearestIdx * CELL_W
  if (Math.abs(target - track.scrollLeft) < 2) { isSnapping = false; return }
  isSnapping = true
  track.scrollTo({ left: target, behavior: 'smooth' })
  setTimeout(() => { isSnapping = false }, 400)
}

// ── Нескінченне розширення ────────────────────────
// Буфер 14 клітинок — щоб нові дні рендерились заздалегідь
function maybeExtendForward() {
  const track = trackRef.value
  if (!track) return
  if (track.scrollLeft + track.clientWidth < track.scrollWidth - CELL_W * 14) return
  const last = allDays.value[allDays.value.length - 1]
  let nm = last.month + 1, ny = last.year
  if (nm > 12) { nm = 1; ny++ }
  allDays.value = [...allDays.value, ...buildLocalDays(nm, ny)]
  fetchMonthData(nm, ny)
}

async function maybeExtendBackward() {
  const track = trackRef.value
  if (!track || track.scrollLeft > CELL_W * 14) return
  const first = allDays.value[0]
  let pm = first.month - 1, py = first.year
  if (pm < 1) { pm = 12; py-- }
  const prevDays = buildLocalDays(pm, py)
  allDays.value = [...prevDays, ...allDays.value]
  await nextTick()
  track.scrollLeft += prevDays.length * CELL_W
  updateScales()
  fetchMonthData(pm, py)
}

function onTrackScroll() {
  if (!scaleRafId) {
    scaleRafId = requestAnimationFrame(() => {
      updateScales()
      scaleRafId = null
    })
  }
  if (!isSnapping) {
    clearTimeout(snapTimer)
    snapTimer = setTimeout(snapToNearest, 130)
  }
  clearTimeout(extendTimer)
  clearTimeout(backwardTimer)
  extendTimer = setTimeout(() => {
    maybeExtendForward()
    backwardTimer = setTimeout(maybeExtendBackward, 50)
  }, 60)
}

function onTimelineWheel(e) {
  const track = trackRef.value
  if (!track) return
  e.preventDefault()

  let delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY
  if (e.deltaMode === WheelEvent.DOM_DELTA_LINE) delta *= 24
  if (e.deltaMode === WheelEvent.DOM_DELTA_PAGE) delta *= track.clientWidth
  track.scrollLeft += delta
}

// scrollTo without snap interference; after scroll: extend if needed
function gotoMonth(m, y) {
  const idx = allDays.value.findIndex(d => d.month === m && d.year === y)
  if (idx < 0 || !trackRef.value) return
  clearTimeout(snapTimer)
  isSnapping = true
  trackRef.value.scrollTo({ left: idx * CELL_W, behavior: 'smooth' })
  setTimeout(() => {
    isSnapping = false
    updateMonthLabel()
    maybeExtendForward()   // ensure buffer exists after navigation
  }, 750)
}

// Ensure month m/y is in allDays; also pre-load the following month
async function ensureMonthLoaded(m, y) {
  if (!allDays.value.some(d => d.month === m && d.year === y)) {
    const first = allDays.value[0]
    if (y < first.year || (y === first.year && m < first.month)) {
      const prevDays = buildLocalDays(m, y)
      allDays.value = [...prevDays, ...allDays.value]
      await nextTick()
      if (trackRef.value) trackRef.value.scrollLeft += prevDays.length * CELL_W
    } else {
      allDays.value = [...allDays.value, ...buildLocalDays(m, y)]
    }
    fetchMonthData(m, y)
    await nextTick()
  }
  // Pre-load the month after m/y so forward navigation is instant
  let nm = m + 1, ny = y
  if (nm > 12) { nm = 1; ny++ }
  if (!allDays.value.some(d => d.month === nm && d.year === ny)) {
    allDays.value = [...allDays.value, ...buildLocalDays(nm, ny)]
    fetchMonthData(nm, ny)
    await nextTick()
  }
}

async function prevMonth() {
  let pm = viewMonth.value - 1, py = viewYear.value
  if (pm < 1) { pm = 12; py-- }
  // For backward, just ensure target month exists (no pre-load needed)
  if (!allDays.value.some(d => d.month === pm && d.year === py)) {
    const prevDays = buildLocalDays(pm, py)
    allDays.value = [...prevDays, ...allDays.value]
    await nextTick()
    if (trackRef.value) trackRef.value.scrollLeft += prevDays.length * CELL_W
    fetchMonthData(pm, py)
    await nextTick()
  }
  gotoMonth(pm, py)
}
async function nextMonth() {
  let nm = viewMonth.value + 1, ny = viewYear.value
  if (nm > 12) { nm = 1; ny++ }
  await ensureMonthLoaded(nm, ny)
  gotoMonth(nm, ny)
}

function startScroll(dir) {
  stopScroll()
  const track = trackRef.value
  if (!track) return
  isSnapping = false
  track.scrollBy({ left: dir * CELL_W, behavior: 'smooth' })
  scrollHoldTimer = setTimeout(() => {
    scrollHoldInterval = setInterval(() => {
      if (!trackRef.value) { stopScroll(); return }
      trackRef.value.scrollLeft += dir * 7
    }, 16)
  }, 350)
}
function stopScroll() {
  clearTimeout(scrollHoldTimer)
  clearInterval(scrollHoldInterval)
  scrollHoldTimer = scrollHoldInterval = null
}

function onDragStart(e) {
  if (e.button !== 0) return
  isSnapping     = false
  drag.active    = true
  drag.moved     = false
  drag.startX    = e.clientX
  drag.startLeft = trackRef.value.scrollLeft
}
function onDragMove(e) {
  if (!drag.active) return
  if (Math.abs(e.clientX - drag.startX) > 4) drag.moved = true
  if (!drag.moved) return
  e.preventDefault()
  trackRef.value.scrollLeft = drag.startLeft - (e.clientX - drag.startX)
}
function onDragEnd() { drag.active = false }

// ── Вибір дня менструації прямо в таймлайні ──────
function enterChooseMode() {
  pickedDay.value = null
  choosingType.value = true
}

function enterStartMode() {
  choosingType.value = false
  pickedDay.value = null
  pickingMode.value = 'start'
}

function enterEndMode() {
  choosingType.value = false
  pickedDay.value = null
  pickingMode.value = 'end'
}

function cancelPickingMode() {
  choosingType.value = false
  pickingMode.value = null
  pickedDay.value = null
}

function onDayClick(day) {
  if (drag.moved) return
  const idx = allDays.value.findIndex(d => d.date === day.date)
  if (idx >= 0 && trackRef.value) {
    clearTimeout(snapTimer)
    isSnapping = true
    trackRef.value.scrollTo({ left: idx * CELL_W, behavior: 'smooth' })
    setTimeout(() => { isSnapping = false; updateMonthLabel() }, 600)
  }
  if (!pickingMode.value) return
  if (pickingMode.value === 'end' && !day.is_menstruation) return
  pickedDay.value = day.date
}

async function confirmStart() {
  if (!pickedDay.value) return
  const date = pickedDay.value
  pickingMode.value = null
  pickedDay.value = null
  errorMsg.value = ''
  try {
    await startCycle(date)
    await loadCalendar()
  } catch {
    errorMsg.value = 'Не вдалося зберегти. Перевірте з\'єднання.'
  }
}

async function confirmEnd() {
  if (!pickedDay.value) return
  pickingMode.value = null
  pickedDay.value = null
  // TODO: потребує ендпоінту POST /api/cycles/end на бекенді
}

function handleSymptoms()      { router.push({ name: 'symptoms'      }).catch(() => {}) }
function handleCalendar()      { router.push({ name: 'home'          }).catch(() => {}) }
function handleNotifications() { router.push({ name: 'notifications' }).catch(() => {}) }
function handleProfile()       { router.push({ name: 'profile'       }).catch(() => {}) }
function doLogout()            { logout(); router.push({ name: 'login' }) }

async function loadCalendar() {
  const today = new Date()
  const days  = []
  for (let delta = -1; delta <= 1; delta++) {
    let m = today.getMonth() + 1 + delta, y = today.getFullYear()
    if (m < 1)  { m += 12; y-- }
    if (m > 12) { m -= 12; y++ }
    days.push(...buildLocalDays(m, y))
  }
  allDays.value = days

  const cm = today.getMonth() + 1, cy = today.getFullYear()
  fetchedMonths.add(cy + '-' + cm)
  try {
    const result = await getCalendarView(cm, cy)
    const data   = result?.days ? result : (result?.data ?? {})
    if (data.current_phase)        currentPhase.value  = data.current_phase
    if (data.phase_subtitle)       phaseSubtitle.value = data.phase_subtitle
    if (data.active_cycle != null) activeCycle.value   = data.active_cycle
    if (data.days)                 mergeApiDays(data.days)
  } catch {
    errorMsg.value = 'Дані недоступні, перевірте з\'єднання.'
  }

  await nextTick()
  const todayIdx = allDays.value.findIndex(d => d.is_today)
  if (todayIdx >= 0 && trackRef.value) {
    trackRef.value.scrollLeft = todayIdx * CELL_W
  }
  updateScales()
  updateMonthLabel()
}

function onGlobalMouseUp() { drag.active = false; stopScroll() }

onMounted(() => {
  loadCalendar()
  window.addEventListener('mouseup', onGlobalMouseUp)
})
onBeforeUnmount(() => {
  window.removeEventListener('mouseup', onGlobalMouseUp)
  if (scaleRafId) { cancelAnimationFrame(scaleRafId); scaleRafId = null }
  stopScroll()
  clearTimeout(snapTimer)
  clearTimeout(backwardTimer)
  clearTimeout(extendTimer)
})
</script>

<template>
  <div class="home">
    <nav class="top-nav">
      <img class="brand" :src="logoUrl" alt="Estro" @click="doLogout" title="Вийти" />
      <div class="nav-btns">
        <button class="nav-btn nav-btn--filled nav-btn--active" aria-current="page" @click="handleCalendar">До календаря</button>
        <button class="nav-btn nav-btn--outline" @click="handleNotifications">Сповіщення</button>
        <button class="nav-btn nav-btn--filled"  @click="handleProfile">Профіль</button>
      </div>
    </nav>

    <div class="phase">
      <h1 class="phase-title">
        <em v-if="currentPhase">{{ currentPhase }}</em>
        <span v-else class="phase-loading">…</span>
      </h1>
      <p class="phase-sub" v-if="phaseSubtitle">{{ phaseSubtitle }}</p>
    </div>

    <!-- Picking mode hint — завжди займає місце, щоб layout не стрибав -->
    <div class="picking-hint" :class="{ 'picking-hint--on': !!pickingMode }">
      {{ pickingHint }}
    </div>

    <div class="timeline-wrap">
      <button class="tl-arrow tl-arrow--left"
              @mousedown.prevent="startScroll(-1)"
              @mouseup="stopScroll" @mouseleave="stopScroll"
              @touchstart.prevent="startScroll(-1)" @touchend="stopScroll">&#8249;</button>

      <div class="timeline-track"
           ref="trackRef"
           :class="{ 'is-dragging': drag.active, 'is-picking': !!pickingMode }"
           @scroll.passive="onTrackScroll"
           @wheel="onTimelineWheel"
           @mousedown="onDragStart"
           @mousemove="onDragMove"
           @mouseup="onDragEnd">
        <div v-for="day in allDays" :key="day.date"
             class="day-cell"
             :class="{
               'day-cell--today':  day.is_today,
               'day-cell--picked': !!pickingMode && day.date === pickedDay,
               'day-cell--muted':  pickingMode === 'end' && !day.is_menstruation,
             }"
             @click="onDayClick(day)">
          <div class="day-circle">
            <span class="dc-num">{{ day.day_of_month }}</span>
            <span class="dc-sub">{{ day.weekday }}, {{ day.mon }}</span>
          </div>
          <div class="star-row">
            <span v-if="day.is_menstruation || day.is_menstruation_predicted"
                  class="star-tip"
                  :data-tip="day.is_menstruation ? 'Менструація' : 'Передбачена менструація'">
              <svg class="star" :class="{ 'star--faded': day.is_menstruation_predicted && !day.is_menstruation }"
                   viewBox="0 0 37 37" fill="none">
                <path d="M18.0774 0.0771484L19.8569 11.436L27.0774 2.48869L22.939 13.2155L33.6658 9.07715L24.7185 16.2977L36.0774 18.0771L24.7185 19.8566L33.6658 27.0771L22.939 22.9388L27.0774 33.6656L19.8569 24.7183L18.0774 36.0771L16.2979 24.7183L9.07739 33.6656L13.2158 22.9388L2.48894 27.0771L11.4363 19.8566L0.0773926 18.0771L11.4363 16.2977L2.48894 9.07715L13.2158 13.2155L9.07739 2.48869L16.2979 11.436L18.0774 0.0771484Z"
                      fill="#D50000" stroke="#000" stroke-width="0.5"/>
              </svg>
            </span>
            <span v-if="day.is_ovulation_predicted" class="star-tip" data-tip="Передбачена овуляція">
              <svg class="star" viewBox="0 0 37 37" fill="none">
                <path d="M18.0774 0.0771484L19.8569 11.436L27.0774 2.48869L22.939 13.2155L33.6658 9.07715L24.7185 16.2977L36.0774 18.0771L24.7185 19.8566L33.6658 27.0771L22.939 22.9388L27.0774 33.6656L19.8569 24.7183L18.0774 36.0771L16.2979 24.7183L9.07739 33.6656L13.2158 22.9388L2.48894 27.0771L11.4363 19.8566L0.0773926 18.0771L11.4363 16.2977L2.48894 9.07715L13.2158 13.2155L9.07739 2.48869L16.2979 11.436L18.0774 0.0771484Z"
                      fill="#FF34A7" stroke="#000" stroke-width="0.5"/>
              </svg>
            </span>
          </div>
        </div>
      </div>

      <button class="tl-arrow tl-arrow--right"
              @mousedown.prevent="startScroll(1)"
              @mouseup="stopScroll" @mouseleave="stopScroll"
              @touchstart.prevent="startScroll(1)" @touchend="stopScroll">&#8250;</button>
    </div>

    <div class="month-nav">
      <button class="month-arrow" @click="prevMonth">&#8249;</button>
      <span class="month-lbl">{{ monthLabel }}</span>
      <button class="month-arrow" @click="nextMonth">&#8250;</button>
    </div>

    <p v-if="errorMsg" class="err" role="alert">{{ errorMsg }}</p>

    <!-- Normal actions -->
    <div v-if="!choosingType && !pickingMode" class="actions">
      <button class="btn btn--filled" @click="enterChooseMode">Відмітити менструацію</button>
      <button class="btn btn--outline" @click="handleSymptoms">Симптоми</button>
    </div>

    <!-- Choose: start or end -->
    <div v-else-if="choosingType" class="actions">
      <button class="btn btn--outline" @click="cancelPickingMode">Скасувати</button>
      <button class="btn btn--filled" @click="enterStartMode">Початок</button>
      <button class="btn btn--outline" :disabled="!hasActivePeriod" @click="enterEndMode">Кінець</button>
    </div>

    <!-- Picking mode actions -->
    <div v-else class="actions picking-actions">
      <button class="btn btn--outline" @click="cancelPickingMode">Скасувати</button>
      <button v-if="pickingMode === 'start'" class="btn btn--menstruation"
              :disabled="!pickedDay" @click="confirmStart">
        Підтвердити початок
      </button>
      <button v-else class="btn btn--menstruation"
              :disabled="!pickedDay" @click="confirmEnd">
        Підтвердити кінець
      </button>
    </div>
  </div>
</template>

<style scoped>
.home {
  position: relative;
  min-height: 100vh; width: 100%;
  display: flex; flex-direction: column;
  background: transparent; color: #000;
  overflow-x: hidden;
}
.top-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 22px 40px; flex-shrink: 0;
}
.brand { height: 34px; cursor: pointer; transition: opacity .15s; }
.brand:hover { opacity: .55; }
.nav-btns { display: flex; gap: 8px; }
.nav-btn {
  height: 42px; padding: 0 20px; border-radius: 7px;
  font-family: 'Geist', sans-serif; font-size: 14px; cursor: pointer;
  white-space: nowrap; transition: opacity .15s;
}
.nav-btn:hover    { opacity: .8; }
.nav-btn--filled  { background: #000; color: #fff; border: none; }
.nav-btn--outline { background: transparent; color: #000; border: 2px solid #000; }

.phase {
  text-align: center; padding: 52px 60px 28px; flex-shrink: 0;
}
.phase-title {
  font-family: 'Instrument Serif', 'Times New Roman', serif;
  font-weight: 400; font-size: clamp(38px, 5.6vw, 78px);
  line-height: 1.05; margin: 0 0 16px;
}
.phase-loading { font-style: italic; color: rgba(0,0,0,.2); }
.phase-sub {
  font-family: 'Geist', sans-serif; font-size: clamp(13px, 1.1vw, 16px);
  color: rgba(0,0,0,.6); margin: 0 auto; line-height: 1.5; max-width: 560px;
}

/* ── Picking mode hint ── */
.picking-hint {
  text-align: center;
  font-family: 'Geist', sans-serif; font-size: 13px;
  color: transparent; padding: 0 24px 8px; flex-shrink: 0;
  transition: color .25s;
}
.picking-hint--on { color: #D50000; }

/* ── Timeline ── */
.timeline-wrap {
  position: relative; display: flex; align-items: center;
  flex-shrink: 0; padding: 20px 0 12px;
}
.tl-arrow {
  position: absolute; top: 50%; transform: translateY(-50%); z-index: 3;
  width: 42px; height: 42px; border-radius: 50%; background: #fff;
  border: 1.5px solid rgba(0,0,0,.18); font-size: 20px; color: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; user-select: none; transition: color .15s, box-shadow .12s;
}
.tl-arrow:hover  { color: #000; box-shadow: 0 2px 10px rgba(0,0,0,.12); }
.tl-arrow--left  { left: 12px; }
.tl-arrow--right { right: 12px; }

.timeline-track {
  width: 100%; display: flex; align-items: center;
  overflow-x: scroll; scrollbar-width: none;
  -webkit-overflow-scrolling: touch; cursor: grab; user-select: none;
  padding: 20px calc(50% - 100px);
}
.timeline-track::-webkit-scrollbar { display: none; }
.timeline-track.is-dragging        { cursor: grabbing; }
.timeline-track.is-picking         { cursor: pointer; }

.day-cell {
  flex: 0 0 200px; display: flex; flex-direction: column;
  align-items: center; gap: 10px; user-select: none;
  contain: layout paint style;
}

/* ── Circle — two-line label ── */
.day-circle {
  width: 174px; height: 174px; border-radius: 50%;
  border: 1.5px solid #000; background: rgba(255,255,255,0.82);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 4px;
  flex-shrink: 0; will-change: transform; transform-origin: center center;
  backface-visibility: hidden;
  transition: background .2s, border-color .2s;
}
.dc-num {
  font-family: 'Geist', sans-serif; font-size: 22px;
  font-weight: 400; color: #000; line-height: 1;
}
.dc-sub {
  font-family: 'Geist', sans-serif; font-size: 9.5px;
  color: rgba(0,0,0,.4); line-height: 1; letter-spacing: .02em;
}

/* today: чорний */
.day-cell--today .day-circle           { background: #000; border: none; }
.day-cell--today .dc-num,
.day-cell--today .dc-sub               { color: #fff; }

/* picked: червоний */
.day-cell--picked .day-circle          { background: #D50000 !important; border-color: #D50000 !important; }
.day-cell--picked .dc-num,
.day-cell--picked .dc-sub              { color: #fff !important; }

/* end-mode: не-менструальні дні приглушені */
.day-cell--muted                       { pointer-events: none; }
.day-cell--muted .day-circle           { opacity: 0.22; }

.star-row {
  height: 26px; display: flex; align-items: center; justify-content: center; gap: 4px;
  flex-shrink: 0;
}
.star-tip {
  position: relative;
  display: inline-flex; align-items: center; justify-content: center;
}
.star-tip::after {
  content: attr(data-tip);
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  font-family: 'Geist', sans-serif; font-size: 11px;
  background: rgba(22,33,46,.82); color: #fff;
  padding: 4px 9px; border-radius: 6px;
  pointer-events: none; opacity: 0;
  transition: opacity .15s;
  z-index: 20;
}
.star-tip:hover::after { opacity: 1; }
.star        { width: 26px; height: 26px; display: block; }
.star--faded { opacity: .38; }

/* ── Month nav ── */
.month-nav {
  display: flex; align-items: center; justify-content: center;
  gap: 14px; padding: 4px 0 0; flex-shrink: 0;
}
.month-arrow {
  font-family: 'Geist', sans-serif; font-size: 22px;
  color: rgba(0,0,0,.28); padding: 4px 10px; border-radius: 4px;
  cursor: pointer; transition: color .15s;
}
.month-arrow:hover { color: #000; }
.month-lbl {
  font-family: 'Geist', sans-serif; font-size: 13px;
  color: rgba(0,0,0,.45); min-width: 128px; text-align: center;
}

/* ── Actions ── */
.err { font-family: 'Geist', sans-serif; font-size: 13px; color: #c4365b; text-align: center; padding: 8px 24px 0; }
.actions {
  display: flex; justify-content: center; gap: 8px;
  padding: 28px 40px 44px; flex-shrink: 0; flex-wrap: wrap;
  margin-top: auto;
}
.picking-actions { align-items: center; }
.btn {
  height: 52px; padding: 0 30px; border-radius: 7px;
  font-family: 'Geist', sans-serif; font-size: 15px;
  cursor: pointer; white-space: nowrap; transition: opacity .15s, transform .1s;
}
.btn:hover  { opacity: .8; }
.btn:active { transform: translateY(1px); }
.btn--filled       { background: #000; color: #fff; border: none; }
.btn--outline      { background: transparent; color: #000; border: 2px solid #000; }
.btn--menstruation { background: #D50000; color: #fff; border: none; }
.btn--menstruation:disabled { background: rgba(213,0,0,.25); cursor: default; pointer-events: none; }
.btn--done    { background: rgba(0,0,0,.1); color: rgba(0,0,0,.4); border: none; cursor: default; }
.btn:disabled { pointer-events: none; }

@media (max-width: 860px) {
  .timeline-track { padding: 16px calc(50% - 76px); }
  .day-cell   { flex: 0 0 152px; }
  .day-circle { width: 132px; height: 132px; }
  .dc-num     { font-size: 18px; }
}
@media (max-width: 520px) {
  .top-nav    { padding: 16px 18px; }
  .nav-btn    { padding: 0 12px; font-size: 13px; height: 38px; }
  .phase      { padding: 32px 20px 20px; }
  .timeline-track { padding: 12px calc(50% - 44px); }
  .day-cell   { flex: 0 0 88px; }
  .day-circle { width: 76px; height: 76px; }
  .dc-num     { font-size: 14px; }
  .dc-sub     { font-size: 8px; }
  .tl-arrow   { width: 34px; height: 34px; font-size: 18px; }
}
</style>
