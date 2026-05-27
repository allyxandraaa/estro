<script setup>
import { RouterView } from 'vue-router'
import CellField from './components/CellField.vue'
</script>

<template>
  <CellField :density="24" :palette="['ink', 'moss']" :intensity="0.7" />
  <RouterView />
</template>
