<template>
  <div class="user-container">
    <div class="user-sidebar">
      <div class="user-avatar">
        <img :src="user.avatar || '/images/default-avatar.png'" alt="用户头像" @click="triggerFileInput">
        <input
          type="file"
          ref="fileInput"
          @change="handleAvatarUpload"
          accept="image/*"
          style="display: none"
        >
        <div class="avatar-name">{{ user.username }}</div>
        <div class="avatar-upload" @click="triggerFileInput">更换头像</div>
      </div>
      <div class="sidebar-menu">
        <div
          class="menu-item"
          v-for="(item, index) in menuItems"
          :key="index"
          :class="{ active: activeMenu === item.id }"
          @click="activeMenu = item.id"
        >
          <i :class="item.icon"></i>
          {{ item.label }}
        </div>
      </div>
    </div>

    <div class="user-content">
      <!-- 基本信息 -->
      <div v-if="activeMenu === 'basic'" class="content-section">
        <h2>基本信息</h2>
        <div class="form-layout">
          <div class="form-group">
            <label>用户名</label>
            <input type="text" v-model="user.username" :disabled="!editing">
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input type="email" v-model="user.email" :disabled="!editing">
          </div>
          <div class="form-group">
            <label>注册时间</label>
            <div class="info-text">{{ formatDate(user.register_time) }}</div>
          </div>
          <div class="form-group">
            <label>账号状态</label>
            <div class="info-text">{{ user.permission_status === '正常' ? '正常' : '受限' }}</div>
          </div>
          <div class="action-buttons" v-if="editing">
            <button class="btn-save" @click="saveUserInfo">保存修改</button>
            <button class="btn-cancel" @click="cancelEdit">取消</button>
          </div>
          <button v-else class="btn-edit" @click="startEdit">编辑信息</button>
        </div>
      </div>

      <!-- 点赞列表 -->
      <div v-if="activeMenu === 'likes'" class="content-section">
        <h2>我的点赞</h2>
        <div v-if="likesLoading" class="loading">加载中...</div>
        <div v-else-if="likes.length === 0" class="empty-message">暂无点赞记录</div>
        <div v-else class="waterfall-container">
          <div class="waterfall-item" v-for="item in likes" :key="item['Object ID']">
            <img :src="item.Image" :alt="item.Title" @click="goToArtifact(item['Object ID'])">
            <div class="item-info">
              <h3 @click="goToArtifact(item['Object ID'])">{{ item.Title }}</h3>
              <p>{{ item.Artist || '未知艺术家' }}</p>
              <p>{{ item.Period || '未知时期' }}</p>
            </div>
            <button class="btn-unlike" @click="toggleLike(item['Object ID'])">取消点赞</button>
          </div>
        </div>
      </div>

      <!-- 收藏列表 -->
      <div v-if="activeMenu === 'collections'" class="content-section">
        <h2>我的收藏</h2>
        <div v-if="collectionsLoading" class="loading">加载中...</div>
        <div v-else-if="collections.length === 0" class="empty-message">暂无收藏记录</div>
        <div v-else class="waterfall-container">
          <div class="waterfall-item" v-for="item in collections" :key="item['Object ID']">
            <img :src="item.Image" :alt="item.Title" @click="goToArtifact(item['Object ID'])">
            <div class="item-info">
              <h3 @click="goToArtifact(item['Object ID'])">{{ item.Title }}</h3>
              <p>{{ item.Artist || '未知艺术家' }}</p>
              <p>{{ item.Period || '未知时期' }}</p>
              <p class="collect-time">收藏时间: {{ formatDate(item.collect_time) }}</p>
            </div>
            <button class="btn-uncollect" @click="toggleCollect(item['Object ID'])">取消收藏</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import api from '@/utils/api';

export default {
  name: 'UserCenter',
  data() {
    return {
      activeMenu: 'basic',
      editing: false,
      user: {
        user_id: '',
        username: '',
        email: '',
        avatar: '',
        register_time: '',
        permission_status: '正常'
      },
      originalUserInfo: {},
      likes: [],
      likesLoading: false,
      collections: [],
      collectionsLoading: false,
      menuItems: [
        { id: 'basic', label: '基本信息', icon: 'icon-user' },
        { id: 'likes', label: '我的点赞', icon: 'icon-like' },
        { id: 'collections', label: '我的收藏', icon: 'icon-star' }
      ]
    }
  },
  created() {
    this.fetchUserInfo();
  },
  watch: {
    activeMenu(newVal) {
      if (newVal === 'likes' && this.likes.length === 0) {
        this.fetchLikes();
      } else if (newVal === 'collections' && this.collections.length === 0) {
        this.fetchCollections();
      }
    }
  },
  methods: {
    async fetchUserInfo() {
      try {
        const response = await api.get('/user');
        if (response.data.success) {
          this.user = response.data.user;
          // 如果用户有头像，构建头像URL
          if (this.user.user_id) {
            this.user.avatar = this.getUserAvatarUrl(this.user.user_id);
          }
          // 保存原始信息用于取消编辑时恢复
          this.originalUserInfo = { ...this.user };
        }
      } catch (error) {
        console.error('获取用户信息失败:', error);
      }
    },
    getUserAvatarUrl(userId) {
      return `http://172.20.10.3:3200/avatar/${userId}.png`;
    },
    async fetchLikes() {
      this.likesLoading = true;
      try {
        const response = await api.get('/user/likes');
        if (response.data.success) {
          this.likes = response.data.data;
        }
      } catch (error) {
        console.error('获取点赞列表失败:', error);
      } finally {
        this.likesLoading = false;
      }
    },
    async fetchCollections() {
      this.collectionsLoading = true;
      try {
        const response = await api.get('/user/collections');
        if (response.data.success) {
          this.collections = response.data.data;
        }
      } catch (error) {
        console.error('获取收藏列表失败:', error);
      } finally {
        this.collectionsLoading = false;
      }
    },
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString();
    },
    startEdit() {
      this.editing = true;
    },
    cancelEdit() {
      this.user = { ...this.originalUserInfo };
      this.editing = false;
    },
    async saveUserInfo() {
      if (!this.user.username || !this.user.email) {
        alert('用户名和邮箱不能为空');
        return;
      }

      try {
        const response = await api.post('/user/update', {
          username: this.user.username,
          email: this.user.email
        });

        if (response.data.success) {
          alert('用户信息更新成功');
          this.originalUserInfo = { ...this.user };
          this.editing = false;
        } else {
          alert(response.data.message || '更新失败');
        }
      } catch (error) {
        console.error('更新用户信息失败:', error);
        alert('更新失败，请稍后再试');
      }
    },
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    async handleAvatarUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await api.post('/user/avatar', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        if (response.data.success) {
          this.user.avatar = response.data.avatarUrl;
          window.location.reload();
          
        } else {
          alert(response.data.message || '头像上传失败');
        }
      } catch (error) {
        console.error('上传头像失败:', error);
        alert('上传头像失败，请稍后再试');
      } finally {
        // 清空文件输入，以便可以重复选择同一文件
        event.target.value = '';
      }
    },
    goToArtifact(artifact_id) {
      this.$router.push(`/detail/?id=${artifact_id}`);
    },
    async toggleLike(artifact_id) {
      try {
        const response = await api.post('/likes/toggle', {
          artifact_id: artifact_id
        });

        if (response.data.success) {
          // 更新本地点赞列表
          this.likes = this.likes.filter(item => item['Object ID'] !== artifact_id);
        }
      } catch (error) {
        console.error('取消点赞失败:', error);
        alert('操作失败，请稍后再试');
      }
    },
    async toggleCollect(artifact_id) {
      try {
        const response = await api.post('/collection/toggle', {
          artifact_id: artifact_id
        });

        if (response.data.success) {
          // 更新本地收藏列表
          this.collections = this.collections.filter(item => item['Object ID'] !== artifact_id);
        }
      } catch (error) {
        console.error('取消收藏失败:', error);
        alert('操作失败，请稍后再试');
      }
    }
  }
}
</script>

<style scoped>
.user-container {
  display: flex;
  max-width: 1200px;
  margin: 20px auto;
  min-height: calc(100vh - 100px);
  background: #fff;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  overflow: hidden;
  margin-top:120px;
}

.user-sidebar {
  width: 250px;
  background: #f8f8f8;
  border-right: 1px solid #eee;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
}

.user-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 15px 15px;
  border-bottom: 1px solid #eee;
  margin-bottom: 15px;
}

.user-avatar img {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #fff;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.user-avatar img:hover {
  opacity: 0.8;
}

.avatar-name {
  font-weight: bold;
  font-size: 16px;
  color: #333;
  text-align: center;
  margin-bottom: 5px;
}

.avatar-upload {
  font-size: 12px;
  color: #666;
  cursor: pointer;
  text-decoration: underline;
}

.avatar-upload:hover {
  color: #000;
}

.sidebar-menu {
  display: flex;
  flex-direction: column;
  padding: 0 15px;
}

.menu-item {
  padding: 12px 15px;
  cursor: pointer;
  transition: all 0.3s;
  color: #666;
  display: flex;
  align-items: center;
  border-left: 3px solid transparent;
  font-size: 14px;
  margin-bottom: 5px;
  border-radius: 4px;
}

.menu-item i {
  margin-right: 10px;
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.menu-item:hover {
  background: #f0f0f0;
  color: #333;
}

.menu-item.active {
  background: #f0f0f0;
  color: #000;
  font-weight: bold;
  border-left-color: #000;
}

.user-content {
  flex-grow: 1;
  padding: 30px;
  overflow: auto;
  width:1000px;

}

.content-section {
  max-width: 900px;
  margin: 0 auto;
}

.content-section h2 {
  margin-bottom: 25px;
  font-weight: 500;
  color: #333;
  font-size: 24px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.form-layout {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #666;
  font-size: 14px;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border 0.3s;
}

.form-group input:focus {
  border-color: #000;
  outline: none;
}

.form-group input:disabled {
  background: #f9f9f9;
  cursor: not-allowed;
}

.info-text {
  padding: 10px 0;
  color: #333;
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  grid-column: 1 / -1;
}

.btn-save, .btn-edit, .btn-cancel {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-save {

  margin-left:720px;
  background: #000;
  color: #fff;
}

.btn-save:hover {
  background: #333;
}

.btn-edit {
  width:100px;
  margin-left:800px;
  background: #f0f0f0;
  color: #333;
}

.btn-edit:hover {
  background: #e0e0e0;
}

.btn-cancel {
  background: #fff;
  color: #666;
  border: 1px solid #ddd;
}

.btn-cancel:hover {
  background: #f9f9f9;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-message {
  text-align: center;
  padding: 40px;
  color: #999;
}

.waterfall-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.waterfall-item {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.waterfall-item:hover {
  transform: translateY(-5px);
}

.waterfall-item img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  cursor: pointer;
}

.item-info {
  padding: 15px;
  flex-grow: 1;
}

.item-info h3 {
  margin: 0 0 10px;
  font-size: 16px;
  cursor: pointer;
  color: #333;
}

.item-info h3:hover {
  color: #000;
  text-decoration: underline;
}

.item-info p {
  margin: 5px 0;
  font-size: 13px;
  color: #666;
}

.collect-time {
  font-size: 12px !important;
  color: #999 !important;
  margin-top: 10px !important;
}

.btn-unlike, .btn-uncollect {
  width: 100%;
  padding: 8px;
  border: none;
  background: #f8f8f8;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-unlike:hover {
  background: #ffecec;
  color: #ff4d4f;
}

.btn-uncollect:hover {
  background: #fff8e6;
  color: #faad14;
}

@media (max-width: 768px) {
  .user-container {
    flex-direction: column;
  }

  .user-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #eee;
  }

  .user-avatar {
    flex-direction: row;
    justify-content: flex-start;
    align-items: center;
    padding-bottom: 20px;
  }

  .user-avatar img {
    margin-right: 15px;
    margin-bottom: 0;
  }

  .sidebar-menu {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 10px;
  }

  .menu-item {
    white-space: nowrap;
    border-left: none;
    border-bottom: 3px solid transparent;
    padding: 10px 15px;
  }

  .menu-item.active {
    border-left-color: transparent;
    border-bottom-color: #000;
  }

  .user-content {
    padding: 20px 15px;
  }

  .waterfall-container {
    grid-template-columns: 1fr;
  }
}
</style>