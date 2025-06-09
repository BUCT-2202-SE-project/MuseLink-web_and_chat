import { createRouter, createWebHistory } from 'vue-router';
import Home from '@/views/Home.vue';
import Timeline from '@/views/Timeline.vue';
import Knowledge from '@/views/Knowledge.vue';
import Login from '../views/Login.vue';
import Detail from '../views/Detail.vue';
import Register from '../views/Register.vue';
import user from '../views/user.vue';
import Chat from '../views/Chat.vue';
import { useAuthStore } from '@/stores/auth';

const routes = [
  { path: '/', component: Home },
  { path: '/timeline', component: Timeline },
  { path: '/knowledge', component: Knowledge },
  { path: '/login', component: Login },
  { path: '/detail', component: Detail },
  { path: '/register', component: Register },
  { path: '/user', component: user },
  { path: '/chat', component: Chat },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

// 添加路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  
  // 如果路由需要认证
  if (requiresAuth) {
    // 检查认证状态
    const isAuthenticated = await authStore.checkAuth();
    
    if (!isAuthenticated) {
      // 未认证，重定向到登录页
      next({ 
        path: '/login', 
        query: { redirect: to.fullPath } 
      });
    } else {
      // 已认证，允许访问
      next();
    }
  } else {
    // 不需要认证的路由，直接放行
    next();
  }
});

export default router;