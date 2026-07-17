<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  card: { type: Object, required: true }, // {title, polished_prompt, style}
  busy: { type: Boolean, default: false },
})
const emit = defineEmits(['generate', 'repolish'])

const prompt = ref(props.card.polished_prompt)
watch(() => props.card.polished_prompt, (v) => { prompt.value = v })
</script>

<template>
  <div class="prompt-card">
    <div class="head">
      <span class="title">🎬 {{ card.title }}</span>
      <span v-if="card.style" class="style">{{ card.style }}</span>
    </div>
    <textarea v-model="prompt" rows="5" />
    <div class="actions">
      <button class="ghost" :disabled="busy" @click="emit('repolish')">🔄 重新优化</button>
      <button class="primary" :disabled="busy || !prompt.trim()" @click="emit('generate', prompt.trim())">
        {{ busy ? '提交中…' : '🎥 生成视频' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.prompt-card {
  background: var(--surface);
  border: 1px solid var(--primary);
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.head { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
.title { font-weight: 600; font-size: 16px; }
.style { font-size: 12px; color: var(--text-dim); }
textarea { padding: 12px 14px; resize: vertical; line-height: 1.7; }
.actions { display: flex; justify-content: flex-end; gap: 10px; }
.ghost {
  background: none;
  border: 1px solid var(--border);
  color: var(--text-dim);
  padding: 8px 16px;
  border-radius: 10px;
}
.ghost:hover:not(:disabled) { color: var(--text); }
.primary {
  background: var(--primary);
  color: #fff;
  border: none;
  padding: 8px 20px;
  border-radius: 10px;
}
.primary:hover:not(:disabled) { background: var(--primary-hover); }
</style>
