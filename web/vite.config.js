import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// custom domain: video.yuchuntest.com
export default defineConfig({
  base: '/',
  plugins: [vue()],
})
