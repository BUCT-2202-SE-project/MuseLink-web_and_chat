import { defineStore } from 'pinia';
import { ref } from 'vue';
import axios from 'axios';
import router from '@/router';

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null);
  const isAuthenticated = ref(false);

  const setUser = (userData) => {
    user.value = userData;
    isAuthenticated.value = true;
  };

  const clearUser = () => {
    user.value = null;
    isAuthenticated.value = false;
  };

  const fetchUser = async () => {
    try {
      const response = await axios.get('/api/current_user', {
        withCredentials: true
      });
      setUser(response.data);
    } catch (error) {
      clearUser();
      throw error;
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
      console.error('Logout failed:', error);
    }
  };

  return {
    user,
    isAuthenticated,
    setUser,
    clearUser,
    fetchUser,
    logout
  };
});