import axios from 'axios';
import router from '@/router';

// 创建API实例
const api = axios.create({
  baseURL: '/api',
  withCredentials: true
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 处理401错误
    if (error.response && error.response.status === 401) {
      console.log('未授权，重定向到登录页面');
      router.push('/login');
    }
    return Promise.reject(error);
  }
);

export default api;
