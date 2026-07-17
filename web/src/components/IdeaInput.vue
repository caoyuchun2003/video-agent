<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
})
const emit = defineEmits(['polish'])

const idea = ref('')

function submit() {
  const value = idea.value.trim()
  if (!value || props.loading) return
  emit('polish', value)
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    submit()
  }
}
</script>

<template>
  <div class="idea-input">
    <textarea
      v-model="idea"
      rows="3"
      placeholder="说说你想要的视频,比如:一只橘猫在雨后的屋顶上看日落"
      @keydown="onKeydown"
    />
    <button class="primary" :disabled="loading || !idea.trim()" @click="submit">
      {{ loading ? '导演构思中…' : '✨ 帮我优化成专业提示词' }}
    </button>
  </div>
</template>

<style scoped>
.idea-input { display: flex; flex-direction: column; gap: 10px; }
textarea { padding: 12px 14px; resize: vertical; min-height: 80px; }
.primary {
  align-self: flex-end;
  background: var(--primary);
  color: #fff;
  border: none;
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 15px;
}
.primary:hover:not(:disabled) { background: var(--primary-hover); }
</style>
