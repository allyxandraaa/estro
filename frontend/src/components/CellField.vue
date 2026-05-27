<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  density: { type: Number, default: 24 },
  reactive: { type: Boolean, default: true },
  showMembranes: { type: Boolean, default: true },
  showBonds: { type: Boolean, default: true },
  palette: { type: Array, default: () => ['ink', 'moss'] },
  intensity: { type: Number, default: 0.7 },
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
let cells = []
let mouse = { x: -9999, y: -9999, active: false }
let size = { w: 0, h: 0, dpr: 1 }
let ro = null

function init() {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
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
      vx: (Math.random() - 0.5) * 0.06,
      vy: (Math.random() - 0.5) * 0.06,
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

function onMouseMove(e) {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  mouse = { x: e.clientX - rect.left, y: e.clientY - rect.top, active: true }
}

function onMouseLeave() {
  mouse = { x: -9999, y: -9999, active: false }
}

let t0 = 0

function render(now) {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const t = (now - t0) / 1000
  const { w, h } = size
  const m = mouse

  const bgGrad = ctx.createLinearGradient(0, 0, 0, h)
  bgGrad.addColorStop(0, PALETTE.bg)
  bgGrad.addColorStop(1, PALETTE.bgDeep)
  ctx.fillStyle = bgGrad
  ctx.fillRect(0, 0, w, h)

  ctx.globalAlpha = 0.04
  ctx.fillStyle = PALETTE.ink
  for (let i = 0; i < 80; i++) {
    const gx = (i * 97 + Math.sin(t * 0.05 + i) * 4) % w
    const gy = (i * 53 + Math.cos(t * 0.04 + i * 1.3) * 4) % h
    ctx.fillRect(gx, gy, 1, 1)
  }
  ctx.globalAlpha = 1

  for (const c of cells) {
    const nx = smoothNoise(c.seedX, c.seedY, t * 0.15)
    const ny = smoothNoise(c.seedX + 13, c.seedY + 7, t * 0.13)
    c.vx += nx * 0.0025
    c.vy += ny * 0.0025

    if (m.active && props.reactive) {
      const dx = m.x - c.x
      const dy = m.y - c.y
      const d2 = dx * dx + dy * dy
      const d = Math.sqrt(d2) || 1
      const reach = c.layer === 0 ? 600 : 380
      if (d < reach) {
        const norm = 1 - d / reach
        const attract = norm * 0.04
        c.vx += (dx / d) * attract
        c.vy += (dy / d) * attract
        const close = c.layer === 0 ? 140 : 90
        if (d < close) {
          const rep = (1 - d / close) * 0.9
          c.vx -= (dx / d) * rep
          c.vy -= (dy / d) * rep
        }
      }
    }

    c.vx *= 0.94
    c.vy *= 0.94
    c.x += c.vx
    c.y += c.vy

    const margin = c.r * 0.4
    if (c.x < -margin) c.x = w + margin
    if (c.x > w + margin) c.x = -margin
    if (c.y < -margin) c.y = h + margin
    if (c.y > h + margin) c.y = -margin

    c.r = c.baseR * (1 + Math.sin(t * 0.6 + c.phase) * 0.06)
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

  if (m.active && props.reactive) {
    const h1 = ctx.createRadialGradient(m.x, m.y, 0, m.x, m.y, 220)
    h1.addColorStop(0, 'rgba(22,33,46,0.06)')
    h1.addColorStop(1, 'rgba(22,33,46,0)')
    ctx.fillStyle = h1
    ctx.fillRect(0, 0, w, h)
  }

  rafId = requestAnimationFrame(render)
}

onMounted(() => {
  init()
  ro = new ResizeObserver(init)
  ro.observe(canvasRef.value)
  if (props.reactive) {
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseleave', onMouseLeave)
  }
  t0 = performance.now()
  rafId = requestAnimationFrame(render)
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
  ro?.disconnect()
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseleave', onMouseLeave)
})
</script>

<template>
  <canvas ref="canvasRef" class="cell-field" />
</template>

<style scoped>
.cell-field {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
}
</style>
