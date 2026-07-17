<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import IdeaInput from './components/IdeaInput.vue'
import PhraseInput from './components/PhraseInput.vue'
import PromptCard from './components/PromptCard.vue'
import TaskCard from './components/TaskCard.vue'
import { createVideo, getVideoStatus, polishPrompt } from './lib/api.js'
import { loadPhrase } from './lib/phrase.js'
import { loadTasks, saveTasks } from './lib/store.js'

const polishing = ref(false)
const submitting = ref(false)
const card = ref(null) // {title, polished_prompt, style}
const lastIdea = ref('')
const tasks = ref([])
const toast = ref('')

const POLL_INTERVAL = 5000
let pollTimer = null

function showToast(msg) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, 4000)
}

function requirePhrase() {
  if (!loadPhrase().trim()) {
    showToast('生成视频前请先填写访问口令')
    return false
  }
  return true
}

# ---- 创作流 ----
async function onPolish(idea) {
  lastIdea.value = idea
  polishing.value = true
  try {
    card.value = await polishPrompt(idea)
  } catch (err) {
    showToast(`优化失败:${err.message}`)
  } finally {
    polishing.value = false
  }
}

async function onGenerate(prompt) {
  if (!requirePhrase()) return
  submitting.value = true
  try {
    const { task_id } = await createVideo(prompt)
    tasks.value.unshift({
      task_id,
      title: card.value?.title || '',
      prompt,
      status: 'queued',
      created_at: Date.now(),
    })
    saveTasks(tasks.value)
    card.value = null
    ensurePolling()
  } catch (err) {
    showToast(`提交失败:${err.message}`)
  } finally {
    submitting.value = false
  }
}

function onRetry(task) {
  card.value = { title: task.title, polished_prompt: task.prompt, style: '' }
}

function onRemove(taskId) {
  tasks.value = tasks.value.filter((t) => t.task_id !== taskId)
  saveTasks(tasks.value)
}

// ---- 轮询 ----
function activeTasks() {
  return tasks.value.filter((t) => t.status === 'queued' || t.status === 'running')
}

async function pollOnce() {
  for (const task of activeTasks()) {
    try {
      const res = await getVideoStatus(task.task_id)
      task.status = res.status
      if (res.video_url) task.video_url = res.video_url
      if (res.error) task.error = res.error
    } catch { /* 单次失败忽略,下轮再试 */ }
  }
  saveTasks(tasks.value)
  if (!activeTasks().length && pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function ensurePolling() {
  if (!pollTimer && activeTasks().length) {
    pollTimer = setInterval(pollOnce, POLL_INTERVAL)
  }
}

onMounted(() => {
  tasks.value = loadTasks()
  ensurePolling()
})
onBeforeUnmount(() => pollTimer && clearInterval(pollTimer))
</script>

<template>
  <div class="app">
    <header>
      <h1>🎬 视频创作 Agent</h1>
      <p class="tagline">说个想法,AI 导演帮你写镜头,再生成视频</p>
    </header>

    <main>
      <section class="create">
        <PhraseInput />
        <IdeaInput :loading="polishing" @polish="onPolish" />
        <PromptCard
          v-if="card"
          :card="card"
          :busy="submitting"
          @generate="onGenerate"
          @repolish="onPolish(lastIdea)"
        />
      </section>

      <section v-if="tasks.length" class="gallery">
        <h2>我的作品</h2>
        <TaskCard
          v-for="t in tasks"
          :key="t.task_id"
          :task="t"
          @retry="onRetry"
          @remove="onRemove"
        />
      </section>
    </main>

    <transition name="fade">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </transition>
  </div>
</template>

<style scoped>
.app {
  min-height: 100%;
  max-width: 760px;
  margin: 0 auto;
  padding: 32px 16px 60px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}
header { text-align: center; }
h1 { font-size: 24px; margin-bottom: 6px; }
.tagline { color: var(--text-dim); font-size: 14px; }
main { display: flex; flex-direction: column; gap: 28px; }
.create { display: flex; flex-direction: column; gap: 16px; }
.gallery { display: flex; flex-direction: column; gap: 12px; }
h2 { font-size: 16px; color: var(--text-dim); font-weight: 500; }
.toast {
  position: fixed;
  bottom: 28px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--surface-2);
  border: 1px solid var(--border);
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 14px;
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
