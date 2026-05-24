<script setup>
import soniaWelcoming from '../assets/mascot/sonia-welcoming.png'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <main class="auth-shell">
    <div class="auth-stage">
      <img :src="soniaWelcoming" alt="" class="auth-mascot" aria-hidden="true" />

      <div class="auth-card">
        <div class="auth-brand">
          <span class="auth-brand-dot" />
          <span>Estro</span>
        </div>
        <h1 class="auth-title">{{ title }}</h1>
        <p v-if="subtitle" class="auth-subtitle">{{ subtitle }}</p>
        <slot />
      </div>
    </div>
  </main>
</template>

<style scoped>
.auth-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3rem;
  max-width: 1040px;
  width: 100%;
}

/* The PNG asset is pre-cropped to Соня's alpha bounding box (~378×488), so the layout box
   is already tight around her — no transparent padding inflating it. Driving size off
   height keeps her natural proportions; width follows automatically (~349px at 450h).
   Stacked drop-shadow() filters trace her alpha silhouette (not the box) for the glow. */
.auth-mascot {
  height: 250px;
  width: auto;
  flex-shrink: 0;
  filter:
    drop-shadow(0 0 4px rgba(255, 255, 255, 1))
    drop-shadow(0 0 18px rgba(255, 255, 255, 0.85))
    drop-shadow(0 0 48px rgba(255, 255, 255, 0.65))
    drop-shadow(0 0 90px rgba(255, 255, 255, 0.4))
    drop-shadow(0 28px 36px rgba(67, 96, 46, 0.32));
}

@media (max-width: 860px) {
  .auth-stage {
    flex-direction: column;
    gap: 1rem;
  }
  .auth-mascot {
    height: 220px;
  }
}
</style>
