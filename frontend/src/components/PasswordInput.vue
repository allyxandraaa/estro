<script setup>
import { ref } from 'vue'

defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  autocomplete: { type: String, default: 'current-password' },
  required: { type: Boolean, default: false },
  minlength: { type: [String, Number], default: null },
  hasError: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])

const visible = ref(false)
</script>

<template>
  <div class="password-input">
    <input
      :value="modelValue"
      :type="visible ? 'text' : 'password'"
      class="field-input"
      :class="{ 'has-error': hasError }"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      :required="required"
      :minlength="minlength"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <button
      type="button"
      class="password-toggle"
      :aria-label="visible ? 'Приховати пароль' : 'Показати пароль'"
      :aria-pressed="visible"
      @click="visible = !visible"
    >
      <svg
        v-if="!visible"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
      <svg
        v-else
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M9.9 4.24A10.5 10.5 0 0 1 12 4c6.5 0 10 7 10 7a17.7 17.7 0 0 1-3.2 4.4" />
        <path d="M6.6 6.6A17.4 17.4 0 0 0 2 11s3.5 7 10 7a10.4 10.4 0 0 0 5.4-1.6" />
        <path d="M1 1l22 22" />
        <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.password-input {
  position: relative;
}

.password-input .field-input {
  padding-right: 3rem;
}

.password-toggle {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  color: var(--ink-500);
  transition: color 0.15s ease, background 0.15s ease;
}

.password-toggle:hover {
  color: var(--matcha-600);
  background: var(--matcha-50);
}

.password-toggle:focus-visible {
  outline: 2px solid var(--matcha-400);
  outline-offset: 1px;
}

.password-toggle svg {
  width: 18px;
  height: 18px;
}
</style>
