// localStorage 任务持久化
const KEY = 'video-agent-tasks'

export function loadTasks() {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function saveTasks(tasks) {
  try {
    localStorage.setItem(KEY, JSON.stringify(tasks.slice(0, 50)))
  } catch { /* 存储满,忽略 */ }
}
