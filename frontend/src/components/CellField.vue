<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  density: { type: Number, default: 24 },
  reactive: { type: Boolean, default: true },
  showMembranes: { type: Boolean, default: true },
  showBonds: { type: Boolean, default: false },
  palette: { type: Array, default: () => ['ink', 'moss'] },
  intensity: { type: Number, default: 0.48 },
})

const PALETTE = {
  bg: '#ffffff',
  bgDeep: '#ffffff',
  ink: '#16212e',
  amber: '#d49453',
  amberDeep: '#b87431',
  plasma: '#7fb9a8',
  cyan: '#8cb6c9',
  moss: '#5d8a6b',
}

function hexToRgb(h) {
  const n = parseInt(h.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

function smoothNoise(x, y, t) {
  return (
    Math.sin(x * 1.3 + t * 0.21) * 0.5 +
    Math.sin(y * 1.7 - t * 0.17) * 0.3 +
    Math.cos((x + y) * 0.9 + t * 0.13) * 0.2
  )
}

const canvasRef = ref(null)
let rafId = 0
let frameTimerId = 0
let cells = []
let size = { w: 0, h: 0, dpr: 1 }
let ro = null

const FRAME_MS = 50
const MAX_DPR = 1.25

function init() {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR)
  size = { w: rect.width, h: rect.height, dpr }
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  const ctx = canvas.getContext('2d')
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

  cells = []
  for (let i = 0; i < props.density; i++) {
    const layer = i < props.density * 0.35 ? 0 : 1
    const baseR = layer === 0 ? 280 + Math.random() * 260 : 120 + Math.random() * 160
    cells.push({
      x: Math.random() * rect.width,
      y: Math.random() * rect.height,
      vx: (Math.random() - 0.5) * 0.035,
      vy: (Math.random() - 0.5) * 0.035,
      r: baseR,
      baseR,
      phase: Math.random() * Math.PI * 2,
      color: props.palette[Math.floor(Math.random() * props.palette.length)],
      layer,
      seedX: Math.random() * 100,
      seedY: Math.random() * 100,
    })
  }
}

let t0 = 0

function scheduleFrame() {
  frameTimerId = window.setTimeout(() => {
    rafId = requestAnimationFrame(render)
  }, FRAME_MS)
}

function render(now) {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  const t = (now - t0) / 1000
  const { w, h } = size

  ctx.fillStyle = PALETTE.bg
  ctx.fillRect(0, 0, w, h)

  ctx.globalAlpha = 0.025
  ctx.fillStyle = PALETTE.ink
  for (let i = 0; i < 32; i++) {
    const gx = (i * 97 + Math.sin(t * 0.03 + i) * 3) % w
    const gy = (i * 53 + Math.cos(t * 0.025 + i * 1.3) * 3) % h
    ctx.fillRect(gx, gy, 1, 1)
  }
  ctx.globalAlpha = 1

  for (const c of cells) {
    const nx = smoothNoise(c.seedX, c.seedY, t * 0.15)
    const ny = smoothNoise(c.seedX + 13, c.seedY + 7, t * 0.13)
    c.vx += nx * 0.001
    c.vy += ny * 0.001

    c.vx *= 0.965
    c.vy *= 0.965
    c.x += c.vx
    c.y += c.vy

    const margin = c.r * 0.4
    if (c.x < -margin) c.x = w + margin
    if (c.x > w + margin) c.x = -margin
    if (c.y < -margin) c.y = h + margin
    if (c.y > h + margin) c.y = -margin

    c.r = c.baseR * (1 + Math.sin(t * 0.22 + c.phase) * 0.035)
  }

  ctx.globalCompositeOperation = 'multiply'
  for (const c of cells) {
    if (c.layer !== 0) continue
    const rgb = hexToRgb(PALETTE[c.color])
    const g = ctx.createRadialGradient(c.x, c.y, 0, c.x, c.y, c.r)
    const a = 0.32 * props.intensity
    g.addColorStop(0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`)
    g.addColorStop(0.55, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a * 0.35})`)
    g.addColorStop(1, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`)
    ctx.fillStyle = g
    ctx.beginPath()
    ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalCompositeOperation = 'source-over'

  if (props.showBonds) {
    ctx.strokeStyle = 'rgba(22,33,46,0.10)'
    ctx.lineWidth = 0.5
    const fg = cells.filter((c) => c.layer === 1)
    for (let i = 0; i < fg.length; i++) {
      for (let j = i + 1; j < fg.length; j++) {
        const a = fg[i], b = fg[j]
        const dx = a.x - b.x, dy = a.y - b.y
        const d = Math.sqrt(dx * dx + dy * dy)
        const max = (a.baseR + b.baseR) * 0.9
        if (d < max) {
          ctx.globalAlpha = (1 - d / max) * 0.5
          ctx.beginPath()
          ctx.moveTo(a.x, a.y)
          ctx.lineTo(b.x, b.y)
          ctx.stroke()
        }
      }
    }
    ctx.globalAlpha = 1
  }

  for (const c of cells) {
    if (c.layer !== 1) continue
    const rgb = hexToRgb(PALETTE[c.color])

    ctx.globalCompositeOperation = 'multiply'
    const g = ctx.createRadialGradient(c.x, c.y, 0, c.x, c.y, c.r)
    const a = 0.45 * props.intensity
    g.addColorStop(0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`)
    g.addColorStop(0.6, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a * 0.25})`)
    g.addColorStop(1, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`)
    ctx.fillStyle = g
    ctx.beginPath()
    ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2)
    ctx.fill()
    ctx.globalCompositeOperation = 'source-over'

    if (props.showMembranes) {
      ctx.strokeStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0.55)`
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.arc(c.x, c.y, c.r * 0.62, 0, Math.PI * 2)
      ctx.stroke()

      ctx.strokeStyle = 'rgba(22,33,46,0.18)'
      ctx.lineWidth = 0.5
      ctx.beginPath()
      ctx.arc(c.x, c.y, c.r * 0.78, 0, Math.PI * 2)
      ctx.stroke()
    }
  }

  scheduleFrame()
}

onMounted(() => {
  init()
  ro = new ResizeObserver(init)
  ro.observe(canvasRef.value)
  t0 = performance.now()
  rafId = requestAnimationFrame(render)
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
  clearTimeout(frameTimerId)
  ro?.disconnect()
})
</script>

<template>
  <canvas ref="canvasRef" class="cell-field" />
</template>

<style scoped>
.cell-field {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  z-index: 0;
  pointer-events: none;
}
</style>
