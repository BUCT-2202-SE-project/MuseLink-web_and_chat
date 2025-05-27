<template>
  <header class="museum-header">
    <!-- 顶部信息栏 -->
    <div class="top-bar">
      <div class="museum-name">MuseLink-THE MUSEUM OF ART</div>
      <div class="utility-links">
        <template v-if="!user">
          <router-link to="/login" class="utility-link">Join/Log in</router-link>
        </template>

        <div v-else class="user-dropdown">
          <button class="user-dropdown-toggle" @click.stop="toggleDropdown">
            {{ user.username }}
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2"/>
            </svg>
          </button>
          <transition name="fade">
            <div v-show="showDropdown" class="user-dropdown-menu">
              <router-link to="/user" class="dropdown-item" @click="showDropdown = false">
                <svg class="dropdown-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 12C14.7614 12 17 9.76142 17 7C17 4.23858 14.7614 2 12 2C9.23858 2 7 4.23858 7 7C7 9.76142 9.23858 12 12 12Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M20.5901 22C20.5901 18.13 16.7402 15 12.0002 15C7.26015 15 3.41016 18.13 3.41016 22" stroke="currentColor" stroke-width="2"/>
                </svg>
                <span>个人中心</span>
              </router-link>
              <button @click="handleLogout" class="dropdown-item">
                <svg class="dropdown-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M15 4H18C19.1046 4 20 4.89543 20 6V18C20 19.1046 19.1046 20 18 20H15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <path d="M9 16L4 12L9 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M4 12H15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <span>登出</span>
              </button>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <!-- 主导航栏 -->
    <nav class="main-nav">
      <router-link to="/" class="logo-link">
        <img src="@/assets/logo2.png" alt="阡陌 Logo" class="logo-image">
        <span class="logo-text">阡陌-文物数字博物馆</span>
      </router-link>

      <nav class="category-nav">
        <router-link to="/timeline">时间轴</router-link>
        <a href="#" @click.prevent="navigateToChat">知识问答</a>
        <router-link to="/knowledge">知识图谱</router-link>
        <a href="#" class="advanced-search-link" @click.prevent="openAdvancedSearch">
          高级搜索
        </a>
      </nav>
    </nav>

    <!-- 高级搜索面板 -->
    <AdvancedSearchPanel
      :visible="showAdvancedSearch"
      @close="closeAdvancedSearch"
      @search="handleAdvancedSearch"
    />
  </header>
</template>

<script>
import { ref, onMounted, watch,onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import AdvancedSearchPanel from './AdvancedSearchPanel.vue'

export default {
  name: 'MuseumNavBar',
  components: {
    AdvancedSearchPanel
  },
  setup() {
    const router = useRouter()
    const user = ref(null)
    const showDropdown = ref(false)
    const showAdvancedSearch = ref(false)
    
    // 获取当前用户
    const fetchCurrentUser = async () => {
      try {
        const response = await axios.get('/api/user', { withCredentials: true })
        if (response.data.success) {
          user.value = response.data.user
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
      }
    }

    // 登出
    const handleLogout = async () => {
      try {
        await axios.post('/api/logout', {}, { withCredentials: true })
        user.value = null
        showDropdown.value = false
        router.push('/login')
      } catch (error) {
        console.error('登出失败:', error)
        alert('登出失败，请重试')
      }
    }

    // 导航到聊天页面前检查登录状态
    const navigateToChat = () => {
      if (user.value) {
        // 已登录，直接导航到聊天页面
        router.push('/chat')
      } else {
        // 未登录，提示用户并跳转到登录页面
        alert('请先登录后再使用知识问答功能')
        router.push('/login')
      }
    }

    // 切换下拉菜单
    const toggleDropdown = () => {
      showDropdown.value = !showDropdown.value
    }

    // 高级搜索
    const openAdvancedSearch = () => {
      showAdvancedSearch.value = true
    }

    const closeAdvancedSearch = () => {
      showAdvancedSearch.value = false
    }

    const handleAdvancedSearch = (searchParams) => {
      console.log('高级搜索参数:', searchParams)
      closeAdvancedSearch()
      // 这里可以处理搜索逻辑
    }

    // 点击外部关闭下拉菜单
    const handleClickOutside = (event) => {
      if (!event.target.closest('.user-dropdown')) {
        showDropdown.value = false
      }
    }

    onMounted(() => {
      fetchCurrentUser()
      document.addEventListener('click', handleClickOutside)
    })

    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside)
    })
    return {
      user,
      showDropdown,
      showAdvancedSearch,
      toggleDropdown,
      handleLogout,
      openAdvancedSearch,
      closeAdvancedSearch,
      handleAdvancedSearch,
      navigateToChat
    }
  }
}
</script>

<style scoped>
/* 基础样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.museum-header {
  font-family: 'Helvetica Neue', Arial, sans-serif;
  width: 100%;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
  background: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

/* 顶部信息栏样式 */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 2rem;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  font-size: 0.85rem;
}

.museum-name {
  font-weight: bold;
  letter-spacing: 0.05em;
  color: #333;
}

.utility-links {
  display: flex;
  align-items: center;
}

.utility-link {
  color: #666;
  text-decoration: none;
  margin-left: 1.5rem;
  transition: color 0.3s;
  font-size: 0.85rem;
}

.utility-link:hover {
  color: #000;
}

/* 主导航栏样式 */
.main-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
}

.logo-link {
  text-decoration: none;
  font-size: 1.8rem; /* 从1.5rem增加到1.8rem */
  font-weight: bold;
  color: #333;
  flex-shrink: 0;
  margin-right: 2.5rem; /* 从2rem增加到2.5rem，给更大的logo留出更多空间 */
  display: flex;
  align-items: center;
  padding: 0.5rem 0; /* 添加垂直内边距 */
}

.logo-image {
  height: 40px; /* 从32px增加到40px */
  margin-right: 12px; /* 从10px增加到12px */
  vertical-align: middle;
}

.logo-text {
  letter-spacing: 1px;
}

/* 分类导航样式 */
.category-nav {
  display: flex;
  margin-left: 2rem;
}

.category-nav a {
  color: #333;
  text-decoration: none;
  margin-left: 1.5rem;
  font-weight: 500;
  padding: 0.5rem 0;
  position: relative;
  font-size: 1rem;
  transition: color 0.3s;
}

.category-nav a:after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: #333;
  transition: width 0.3s;
}

.category-nav a:hover:after,
.category-nav a.router-link-exact-active:after {
  width: 100%;
}

.advanced-search-link {
  cursor: pointer;
}

/* 用户下拉菜单样式 */
.user-dropdown {
  position: relative;
  display: inline-block;
  margin-left: 1.5rem;
}

.user-dropdown-toggle {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0;
  font: inherit;
  transition: color 0.3s;
}

.user-dropdown-toggle:hover {
  color: #000;
}

.user-dropdown-menu {
  position: absolute;
  right: 0;
  top: 100%;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  min-width: 160px;
  z-index: 100;
  margin-top: 8px;
  overflow: hidden;
}

.dropdown-item {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  color: #333;
  text-decoration: none;
  text-align: left;
  width: 100%;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  gap: 8px;
  transition: background-color 0.2s;
}

.dropdown-item:hover {
  background-color: #f5f5f5;
}

.dropdown-icon {
  flex-shrink: 0;
  color: #666;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .main-nav {
    flex-wrap: wrap;
    padding-bottom: 0;
  }

  .logo-link {
    order: 1;
    margin-bottom: 1rem;
  }

  .category-nav {
    order: 2;
    margin-left: auto;
    margin-bottom: 1rem;
  }
}

@media (max-width: 768px) {
  .top-bar {
    flex-direction: column;
    padding: 0.5rem;
  }

  .museum-name {
    margin-bottom: 0.5rem;
  }

  .utility-links {
    margin-top: 0.5rem;
  }

  .utility-link {
    margin: 0 0.5rem;
  }
}

@media (max-width: 480px) {
  .category-nav {
    width: 100%;
    justify-content: space-around;
    margin: 0.5rem 0;
  }

  .category-nav a {
    margin: 0;
    font-size: 0.9rem;
  }
}
</style>