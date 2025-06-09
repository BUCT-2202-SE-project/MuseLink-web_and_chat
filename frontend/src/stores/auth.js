import { defineStore } from 'pinia';
import { ref } from 'vue';
import axios from 'axios';
import router from '@/router';

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null);
  const isAuthenticated = ref(false);
  const authChecked = ref(false);

  // 初始化检查认证状态
  const init = async () => {
    try {
      await fetchUser();
      console.log('认证状态初始化成功，用户已登录');
    } catch (error) {
      console.log('认证状态初始化：未登录或会话已过期');
    }
  };

  const setUser = (userData) => {
    user.value = userData;
    isAuthenticated.value = true;
    console.log('用户状态已更新:', userData?.username);
  };

  const clearUser = () => {
    user.value = null;
    isAuthenticated.value = false;
    console.log('用户状态已清除');
  };

  const checkAuth = async () => {
    if (authChecked.value) return isAuthenticated.value;
    
    try {
      await fetchUser();
      authChecked.value = true;
      return true;
    } catch (error) {
      authChecked.value = true;
      return false;
    }
  };

  const fetchUser = async () => {
    try {
      console.log('正在获取当前用户信息...');
      const response = await axios.get('/api/user', {
        withCredentials: true
      });
      
      if (response.data.success && response.data.user) {
        setUser(response.data.user);
        return response.data.user;
      } else {
        console.log('API返回成功但无用户数据');
        clearUser();
        throw new Error('未找到用户数据');
      }
    } catch (error) {
      console.error('获取用户信息失败:', error);
      clearUser();
      throw error;
    }
  };

  const login = async (credentials) => {
    try {
      const response = await axios.post('/api/login', credentials, {
        withCredentials: true
      });
      
      if (response.data.success) {
        // 登录成功后立即获取用户信息
        await fetchUser();
        return true;
      } else {
        return false;
      }
    } catch (error) {
      console.error('登录失败:', error);
      return false;
    }
  };

  const logout = async () => {
    try {
      await axios.post('/api/logout', {}, {
        withCredentials: true
      });
      clearUser();
      router.push('/login');
    } catch (error) {
      console.error('登出失败:', error);
    }
  };

  return {
    user,
    isAuthenticated,
    authChecked,
    init,
    setUser,
    clearUser,
    fetchUser,
    login,
    logout,
    checkAuth
  };
}, {
  persist: {
    paths: ['user', 'isAuthenticated']
  }
});