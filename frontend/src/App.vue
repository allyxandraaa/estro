<script setup>
import { RouterView } from 'vue-router'
import CellField from './components/CellField.vue'
</script>

<template>
  <CellField
    :density="14"
    :reactive="false"
    :show-bonds="false"
    :palette="['ink', 'moss']"
    :intensity="0.48"
  />
  <RouterView v-slot="{ Component }">
    <Transition name="page">
      <component :is="Component" :key="$route.name" />
    </Transition>
  </RouterView>
</template>

<style>
.page-enter-active,
.page-leave-active { transition: opacity 0.22s ease; }
.page-leave-active {
  position: absolute;
  inset: 0;
  width: 100%;
}
.page-enter-from,
.page-leave-to      { opacity: 0; }
</style>
