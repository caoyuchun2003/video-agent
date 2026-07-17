<script setup>
const props = defineProps({
  task: { type: Object, required: true },
  // {task_id, title, prompt, status, video_url?, error?, created_at}
})
const emit = defineEmits(['retry', 'remove'])

const STATUS_TEXT = {
  queued: '⏳ 排队中',
  running: '🎞 生成中',
  succeeded: '✅ 已完成',
  failed: '❌ 失败',
}

function fmtTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <div class="task-card" :class="task.status">
    <div class="head">
      <span class="title">{{ task.title || '未命名作品' }}</span>
      <span class="status">{{ STATUS_TEXT[task.status] || task.status }}</span>
    </div>
    <p class="prompt" :title="task.prompt">{{ task.prompt }}</p>

    <div v-if="task.status === 'queued' || task.status === 'running'" class="progress">
      <div class="bar"><span /></div>
      <span class="note">视频生成一般需要 1~5 分钟,可以先去忙别的,页面会自动刷新状态</span>
    </div>

    <template v-if="task.status === 'succeeded' && task.video_url">
      <video :src="task.video_url" controls preload="metadata" />
      <div class="actions">
        <a class="download" :href="task.video_url" target="_blank" rel="noopener" download>⬇️ 下载视频</a>
        <span class="note">⚠️ 链接有时效,请及时下载保存</span>
      </div>
    </template>

    <div v-if="task.status === 'failed'" class="fail">
      <p class="error">{{ task.error || '生成失败' }}</p>
      <button class="ghost" @click="emit('retry', task)">🔄 重试</button>
    </div>

    <div class="foot">
      <span class="time">{{ fmtTime(task.created_at) }}</span>
      <button class="remove" title="删除记录" @click="emit('remove', task.task_id)">🗑</button>
    </div>
  </div>
</template>

<style scoped>
.task-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.task-card.succeeded { border-color: rgba(52, 211, 153, 0.4); }
.task-card.failed { border-color: rgba(248, 113, 113, 0.4); }
.head { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
.title { font-weight: 600; }
.status { font-size: 13px; color: var(--text-dim); white-space: nowrap; }
.prompt {
  font-size: 13px;
  color: var(--text-dim);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.progress { display: flex; flex-direction: column; gap: 6px; }
.bar {
  height: 4px;
  border-radius: 2px;
  background: var(--surface-2);
  overflow: hidden;
}
.bar span {
  display: block;
  height: 100%;
  width: 40%;
  border-radius: 2px;
  background: var(--primary);
  animation: slide 1.6s ease-in-out infinite;
}
@keyframes slide {
  0% { margin-left: -40%; }
  100% { margin-left: 100%; }
}
.note { font-size: 12px; color: var(--text-dim); }
video { width: 100%; border-radius: 10px; background: #000; }
.actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.download {
  color: var(--success);
  text-decoration: none;
  font-size: 14px;
  border: 1px solid rgba(52, 211, 153, 0.4);
  padding: 5px 14px;
  border-radius: 8px;
}
.fail { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.error { font-size: 13px; color: var(--danger); word-break: break-all; }
.ghost {
  background: none;
  border: 1px solid var(--border);
  color: var(--text-dim);
  padding: 5px 14px;
  border-radius: 8px;
  white-space: nowrap;
}
.foot { display: flex; justify-content: space-between; align-items: center; }
.time { font-size: 12px; color: var(--text-dim); }
.remove { background: none; border: none; color: var(--text-dim); font-size: 14px; }
.remove:hover { color: var(--danger); }
</style>
