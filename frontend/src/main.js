import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import axios from 'axios'

// 全局配置axios
axios.defaults.withCredentials = true // 确保所有请求都携带认证凭据

// 添加请求拦截器用于调试
axios.interceptors.request.use(config => {
  console.log('发送请求:', config.url)
  return config
})

// 添加响应拦截器用于调试
axios.interceptors.response.use(
  response => {
    console.log('接收响应:', response.config.url, response.status)
    return response
  },
  error => {
    console.error('请求错误:', error.config?.url, error.response?.status)
    return Promise.reject(error)
  }
)

const app=createApp(App);
const pinia = createPinia()

pinia.use(piniaPluginPersistedstate) 
app.use(pinia)
app.use(router);
app.use(ElementPlus);
app.mount('#app');
