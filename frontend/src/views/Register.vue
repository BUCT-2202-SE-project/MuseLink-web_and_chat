<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1 class="auth-title">注册</h1>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            class="form-input"
          />
          <div v-if="errors.username" class="error-text">{{ errors.username }}</div>
        </div>

        <div class="form-group">
          <label for="email">邮箱</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            class="form-input"
          />
          <div v-if="errors.email" class="error-text">{{ errors.email }}</div>
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
          <div v-if="errors.password" class="error-text">{{ errors.password }}</div>
        </div>

        <div class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            required
            class="form-input"
          />
          <div v-if="errors.confirmPassword" class="error-text">{{ errors.confirmPassword }}</div>
        </div>

        <button type="submit" class="auth-button" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>

        <div class="auth-footer">
          <span>已有账号？</span>
          <router-link to="/login" class="auth-link">立即登录</router-link>
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
  name: 'RegisterPage',
  setup() {
    const router = useRouter()
    const username = ref('')
    const email = ref('')
    const password = ref('')
    const confirmPassword = ref('')
    const errors = ref({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })
    const error = ref('')
    const loading = ref(false)

    const validateForm = () => {
      let isValid = true
      errors.value = {
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
      }

      if (username.value.length < 4 || username.value.length > 50) {
        errors.value.username = '用户名长度应在4-5个字符之间'
        isValid = false
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(email.value)) {
        errors.value.email = '请输入有效的邮箱地址'
        isValid = false
      }

      if (password.value.length < 8) {
        errors.value.password = '密码长度至少为8个字符'
        isValid = false
      }

      if (password.value !== confirmPassword.value) {
        errors.value.confirmPassword = '两次输入的密码不一致'
        isValid = false
      }

      return isValid
    }

    const handleRegister = async () => {
      if (!validateForm()) return

      error.value = ''
      loading.value = true

      try {
        const response = await axios.post('/api/register', {
          username: username.value,
          email: email.value,
          password: password.value
        }, { withCredentials: true })

        if (response.data.success) {
          router.push('/login')
        } else {
          error.value = response.data.message || '注册失败'
        }
      } catch (err) {
        if (err.response) {
          error.value = err.response.data.message || '注册失败'
        } else {
          error.value = '网络错误，请稍后再试'
        }
      } finally {
        loading.value = false
      }
    }

    return {
      username,
      email,
      password,
      confirmPassword,
      errors,
      error,
      loading,
      handleRegister
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

.error-text {
  color: #d32f2f;
  font-size: 0.8rem;
  margin-top: 0.2rem;
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