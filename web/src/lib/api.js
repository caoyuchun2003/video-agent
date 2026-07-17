// 调用 CFC 网关的 API 封装
// 生产:VITE_API_URL = CFC 触发器基地址(不带路径)
// 本地:默认直连本地 server,需要 VITE_DEV_GATEWAY_TOKEN
const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8001').replace(/\/$/, '')
const DEV_TOKEN = import.meta.env.VITE_DEV_GATEWAY_TOKEN || ''

async function request(method, path, { body, query } = {}) {
  const url = new URL(API_BASE + path)
  for (const [k, v] of Object.entries(query || {})) url.searchParams.set(k, v)
  const headers = { 'Content-Type': 'application/json' }
  if (DEV_TOKEN) headers['X-Gateway-Token'] = DEV_TOKEN

  const resp = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await resp.json().catch(() => ({}))
  if (!resp.ok) {
    throw new Error(data.detail || data.error || `HTTP ${resp.status}`)
  }
  return data
}

/** 优化提示词 → {title, polished_prompt, style} */
export const polishPrompt = (idea) => request('POST', '/prompt/polish', { body: { idea } })

/** 提交生成任务 → {task_id} */
export const createVideo = (prompt) => request('POST', '/video/create', { body: { prompt } })

/** 查询任务 → {status, video_url?, error?} */
export const getVideoStatus = (taskId) =>
  request('GET', '/video/status', { query: { task_id: taskId } })
