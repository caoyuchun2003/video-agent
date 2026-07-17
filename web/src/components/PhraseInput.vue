<script setup>
import { ref, watch } from 'vue'
import { loadPhrase, savePhrase } from '../lib/phrase.js'

const phrase = ref(loadPhrase())

watch(phrase, (v) => savePhrase(v.trim()))
</script>

<template>
  <label class="phrase">
    <span class="label">访问口令</span>
    <input
      v-model="phrase"
      type="password"
      autocomplete="off"
      placeholder="请输入口令后再创作"
    />
  </label>
</template>

<style scoped>
.phrase {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.label { font-size: 13px; color: var(--text-dim); }
input {
  padding: 10px 12px;
  width: 100%;
}
</style>
