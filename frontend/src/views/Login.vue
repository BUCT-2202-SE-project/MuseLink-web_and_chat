<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1 class="auth-title">登录</h1>

      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label for="username_or_email">用户名或邮箱</label>
          <input
            id="username_or_email"
            v-model="username_or_email"
            type="text"
            required
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            class="form-input"
          />
        </div>

        <button type="submit" class="auth-button" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <div class="auth-footer">
          <span>还没有账号？</span>
          <router-link to="/register" class="auth-link">立即注册</router-link>
        </div>
      </form>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'LoginPage',
  setup() {
    const router = useRouter()
    const username_or_email = ref('')
    const password = ref('')
    const error = ref('')
    const loading = ref(false)

    const handleLogin = async () => {
      error.value = ''
      loading.value = true

      try {
        const response = await axios.post('/api/login', {
          username_or_email: username_or_email.value,
          password: password.value
        }, { withCredentials: true })

        if (response.data.success) {
          window.location.href = '/'
        } else {
          error.value = response.data.message || '登录失败'
        }
      } catch (err) {
        if (err.response) {
          error.value = err.response.data.message || '登录失败'
        } else {
          error.value = '网络错误，请稍后再试'
        }
      } finally {
        loading.value = false
      }
    }

    return {
      username_or_email,
      password,
      error,
      loading,
      handleLogin
    }
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  width:600px;
  padding: 2rem;
  margin-left:300px;
}

.auth-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 2.5rem;
  width: 100%;
  max-width: 400px;
}

.auth-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: #333;
  text-align: center;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  font-size: 0.9rem;
  color: #555;
}

.form-input {
  padding: 0.8rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-input:focus {
  border-color: #666;
  outline: none;
}

.auth-button {
  padding: 0.8rem;
  background-color: #000;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.auth-button:hover:not(:disabled) {
  background-color: #333;
}

.auth-button:disabled {
  background-color: #999;
  cursor: not-allowed;
}

.auth-footer {
  text-align: center;
  font-size: 0.9rem;
  color: #666;
  margin-top: 1rem;
}

.auth-link {
  color: #000;
  text-decoration: none;
  font-weight: 500;
}

.auth-link:hover {
  text-decoration: underline;
}

.error-message {
  margin-top: 1.5rem;
  padding: 0.8rem;
  background-color: #ffeeee;
  color: #d32f2f;
  border-radius: 4px;
  font-size: 0.9rem;
  text-align: center;
}
</style>