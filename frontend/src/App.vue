<script setup>
import { ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import CellField from './components/CellField.vue'

const route    = useRoute()
const bgFrozen = ref(false)
let   freezeTimer = null

// На сторінці home: заморожуємо фон після завершення page-transition (~800ms)
// На решті — анімація жива (логін, онбординг)
watch(() => route.name, (name) => {
  clearTimeout(freezeTimer)
  if (name === 'home') {
    freezeTimer = setTimeout(() => { bgFrozen.value = true }, 850)
  } else {
    bgFrozen.value = false
  }
})
</script>

<template>
  <CellField
    :density="24"
    :palette="['ink', 'moss']"
    :intensity="0.7"
    :frozen="bgFrozen"
  />
  <RouterView v-slot="{ Component }">
    <Transition name="page" mode="out-in">
      <component :is="Component" :key="$route.name" />
    </Transition>
  </RouterView>
</template>

<style>
.page-enter-active { transition: opacity 0.35s ease; }
.page-leave-active  { transition: opacity 0.25s ease; }
.page-enter-from,
.page-leave-to      { opacity: 0; }
</style>
