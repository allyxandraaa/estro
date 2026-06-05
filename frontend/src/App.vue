<script setup>
import { RouterView } from 'vue-router'
import CellField from './components/CellField.vue'
</script>

<template>
  <CellField :density="24" :palette="['ink', 'moss']" :intensity="0.7" />
  <RouterView v-slot="{ Component }">
    <Transition name="page" mode="out-in">
      <component :is="Component" :key="$route.name" />
    </Transition>
  </RouterView>
</template>

<style>
/*
 * Глобальний page-transition для всіх змін роутів.
 * Не scoped: класи застосовуються Vue зовні до кореневих елементів компонентів.
 * mode="out-in": поточна сторінка зникає → фон (CellField) видно → нова з'являється.
 */
.page-enter-active { transition: opacity 0.35s ease; }
.page-leave-active  { transition: opacity 0.25s ease; }
.page-enter-from,
.page-leave-to      { opacity: 0; }
</style>
