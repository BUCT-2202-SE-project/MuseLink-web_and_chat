import { createRouter, createWebHistory } from 'vue-router';
import Home from '@/views/Home.vue';
import Timeline from '@/views/Timeline.vue';
import Knowledge from '@/views/Knowledge.vue';
import Login from '../views/Login.vue';
import Detail from '../views/Detail.vue';
import Register from '../views/Register.vue';
import user from '../views/user.vue';
import Chat from '../views/Chat.vue';



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


export default router;