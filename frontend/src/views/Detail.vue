<template>
  <div class="artifact-detail-container">
    <!-- 头部导航 -->
    <div class="header">
      <router-link to="/" class="back-button">
        <img src="@/components/icons/arrow-left.png" class="button-icon" alt="返回" /> 返回
      </router-link>
      <h1>{{ artifact.Title }}</h1>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
      <!-- 左半部分 - 图片展示 -->
      <div class="image-section">
        <div class="main-image-container" id="openseadragon-container"></div>
        <!-- 自定义控制按钮 -->
        <div class="custom-controls">
          <button @click="zoomIn" title="放大">
            <img src="@/components/icons/zoom-in.png" class="button-icon" alt="放大" />
          </button>
          <button @click="zoomOut" title="缩小">
            <img src="@/components/icons/zoom-out.png" class="button-icon" alt="缩小" />
          </button>
          <button @click="resetZoom" title="重置">
            <img src="@/components/icons/refresh.png" class="button-icon" alt="重置" />
          </button>
          <button @click="toggleFullscreen" :title="isFullscreen ? '退出全屏' : '全屏'">
            <img :src="isFullscreen ? require('@/components/icons/fullscreen-exit.png') : require('@/components/icons/fullscreen.png')"
                 class="button-icon" :alt="isFullscreen ? '退出全屏' : '全屏'" />
          </button>
        </div>
      </div>

      <!-- 右半部分 - 文物介绍 -->
      <div class="info-section">
        <div class="info-card">
          <div class="title-row">
            <h2>{{ artifact.Title }}</h2>
            <div class="action-buttons">
              <button @click="toggleLike" class="like-button" :title="isLiked ? '取消点赞' : '点赞'">
                <img :src="isLiked ? require('@/components/icons/heart-filled.png') : require('@/components/icons/heart-outline.png')"
                     class="action-icon" alt="点赞" />
                <span class="action-count">{{ likeCount }}</span>
              </button>
              <button @click="toggleCollect" class="collect-button" :title="isCollected ? '取消收藏' : '收藏'">
                <img :src="isCollected ? require('@/components/icons/star-filled.png') : require('@/components/icons/star-outline.png')"
                     class="action-icon" alt="收藏" />
                <span class="action-count">{{ collectCount }}</span>
              </button>
            </div>
          </div>

          <div class="info-item" v-if="artifact.Artist && artifact.Artist !== '未知'">
            <span class="label">作者:</span>
            <span class="value">{{ artifact.Artist }}</span>
          </div>

          <div class="info-item" v-if="artifact.Period && artifact.Period !== '未知'">
            <span class="label">时期:</span>
            <span class="value">{{ artifact.Period }}</span>
          </div>

          <div class="info-item" v-if="artifact.Museum && artifact.Museum !== '未知'">
            <span class="label">博物馆:</span>
            <span class="value">{{ artifact.Museum }}</span>
          </div>

          <div class="info-item" v-if="artifact.descripe">
            <span class="label">描述:</span>
            <div class="value description">{{ artifact.descripe }}</div>
          </div>

          <div class="info-item" v-if="artifact['Object ID']">
            <span class="label">文物ID:</span>
            <span class="value">{{ artifact['Object ID'] }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 相关文物推荐部分 -->
    <div class="related-section" v-if="relatedArtifacts.length > 0">
      <h2 class="related-title">相关推荐</h2>
      <div class="divider"></div>
      <div class="masonry-grid">
        <div class="masonry-item" v-for="item in relatedArtifacts" :key="item['Object ID']"
          @click="goToDetail(item['Object ID'])">
          <img :src="item.Image" :alt="item.Title" />
          <div class="item-info">
            <div class="item-name">{{ item.Title }}</div>
            <div class="item-period">{{ item.Period || '未知时期' }}</div>
            <div class="item-artist">{{ item.Artist || '未知作者' }}</div>
            <div class="item-museum">{{ item.Museum || '未知博物馆' }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 加载状态 -->
  <div v-if="loading" class="loading-overlay">
    <div class="loading-spinner"></div>
  </div>
</template>

<script>
import OpenSeadragon from 'openseadragon';
import axios from 'axios';
import api from '@/utils/api';

export default {
  name: 'ArtifactDetail',
  data() {
    return {
      artifact: {
        'Object ID': '',
        Title: '',
        Artist: '',
        Period: '',
        Museum: '',
        descripe: '',
        Image: ''
      },
      relatedArtifacts: [],
      loading: false,
      // 互动状态
      likeCount: 0,
      collectCount: 0,
      isLiked: false,
      isCollected: false,
      // OpenSeadragon 实例
      viewer: null,
      isFullscreen: false
    };
  },
  watch: {
    '$route.query.id': {
      immediate: true,
      handler(newId) {
        if (newId) {
          this.fetchArtifactData();
        }
      }
    },
    // 监听图片变化
    'artifact.Image': {
      handler(newImage) {
        if (newImage && newImage !== '未知') {
          this.initOpenSeadragon();
        }
      }
    }
  },
  created() {
    this.fetchArtifactData();
  },
  methods: {
    async fetchArtifactData() {
      this.loading = true;
      const artifactId = this.$route.query.id;

      try {
        // 使用axios替代fetch
        const response = await api.get(`/artifact/${artifactId}`);
        const data = response.data;

        if (data.success) {
          this.artifact = data.artifact || {};
          this.relatedArtifacts = data.related || [];

          // 设置互动状态
          if (data.interaction) {
            this.likeCount = data.interaction.likeCount || 0;
            this.collectCount = data.interaction.collectCount || 0;
            this.isLiked = data.interaction.isLiked || false;
            this.isCollected = data.interaction.isCollected || false;
          }

          // 设置默认图片
          if (!this.artifact.Image) {
            this.artifact.Image = 'https://via.placeholder.com/600x400?text=No+Image';
          }
        } else {
          throw new Error(data.error || '获取数据失败');
        }
      } catch (error) {
        console.error('Error:', error);
        this.$message.error(error.message || '获取文物详情失败');
      } finally {
        this.loading = false;
      }
    },

    initOpenSeadragon() {
      // 如果已有viewer实例，先销毁
      if (this.viewer) {
        this.viewer.destroy();
      }

      // 确保容器存在
      this.$nextTick(() => {
        if (!document.getElementById('openseadragon-container')) {
          console.error('OpenSeadragon container not found');
          return;
        }

        // 初始化OpenSeadragon
        this.viewer = OpenSeadragon({
          id: 'openseadragon-container',
          prefixUrl: 'https://cdnjs.cloudflare.com/ajax/libs/openseadragon/2.4.2/images/',
          tileSources: {
            type: 'image',
            url: this.artifact.Image
          },
          showNavigator: true,
          navigatorPosition: 'TOP_RIGHT',
          navigatorHeight: '100px',
          navigatorWidth: '150px',
          animationTime: 0.5,
          blendTime: 0.1,
          constrainDuringPan: true,
          maxZoomPixelRatio: 5,
          minZoomLevel: 0.5,
          visibilityRatio: 1.0,
          zoomPerScroll: 1.2,
          showNavigationControl: false, // 禁用原生控制按钮
          gestureSettingsMouse: {
            clickToZoom: true,
            dblClickToZoom: true,
            pinchToZoom: true,
            scrollToZoom: true,
            flickEnabled: true,
            flickMinSpeed: 120,
            flickMomentum: 0.25
          }
        });
      });
    },

    async toggleLike() {
      try {
        // 使用axios实例替代fetch
        const response = await api.post('/likes/toggle', {
          artifact_id: this.artifact['Object ID']
        });

        if (response.data.success) {
          this.isLiked = response.data.isLiked;
          this.likeCount = response.data.likeCount;
          this.$message.success(response.data.message);
        } else {
          throw new Error(response.data.message || '操作失败');
        }
      } catch (error) {
        console.error('点赞操作失败:', error);
        // 处理错误但不强制跳转登录，因为拦截器会处理401
        if (error.response && error.response.status !== 401) {
          this.$message.error(error.message || '点赞操作失败');
        }
      }
    },

    async toggleCollect() {
      try {
        // 使用axios实例替代fetch
        const response = await api.post('/collection/toggle', {
          artifact_id: this.artifact['Object ID']
        });

        if (response.data.success) {
          this.isCollected = response.data.isCollected;
          this.collectCount = response.data.collectCount;
          this.$message.success(response.data.message);
        } else {
          throw new Error(response.data.message || '操作失败');
        }
      } catch (error) {
        console.error('收藏操作失败:', error);
        // 处理错误但不强制跳转登录，因为拦截器会处理401
        if (error.response && error.response.status !== 401) {
          this.$message.error(error.message || '收藏操作失败');
        }
      }
    },

    zoomIn() {
      if (this.viewer) {
        this.viewer.viewport.zoomBy(1.5);
      }
    },

    zoomOut() {
      if (this.viewer) {
        this.viewer.viewport.zoomBy(0.5);
      }
    },

    resetZoom() {
      if (this.viewer) {
        this.viewer.viewport.goHome();
      }
    },

    toggleFullscreen() {
      if (!this.viewer) return;

      if (!this.isFullscreen) {
        this.viewer.setFullScreen(true);
        this.isFullscreen = true;
      } else {
        this.viewer.setFullScreen(false);
        this.isFullscreen = false;
      }
    },

    goToDetail(id) {
      this.$router.push({ path: '/detail', query: { id } });
    }
  },
  mounted() {
    document.addEventListener('fullscreenchange', () => {
      this.isFullscreen = document.fullscreenElement !== null;
    });
  },
  beforeDestroy() {
    if (this.viewer) {
      this.viewer.destroy();
    }
    document.removeEventListener('fullscreenchange', () => {
      this.isFullscreen = document.fullscreenElement !== null;
    });
  }
};
</script>

<style scoped>
.title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.like-button, .collect-button {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: all 0.2s;
}

.like-button:hover, .collect-button:hover {
  background-color: #f0f0f0;
}

.action-icon {
  width: 24px;
  height: 24px;
}

.action-count {
  margin-left: 5px;
  font-size: 14px;
  color: #666;
}

.artifact-detail-container {
  width: 1200px;
  margin-left: -200px;
  margin: 0 auto;
  padding: 40px;
  font-family: 'Helvetica Neue', Arial, sans-serif;
  color: #333;
  background-color: #fff;
}

.header {
  display: flex;
  align-items: center;
  margin-top: 100px;
  margin-left: -200px;
  margin-bottom: 0px;
  padding-bottom: 15px;
  width: 1400px;
  border-bottom: 1px solid #d3d3d3;
}

.back-button {
  display: inline-flex;
  align-items: center;
  margin-right: 20px;
  margin-left: 0px;
  color: #333;
  text-decoration: none;
  font-size: 16px;
  font-weight: bold;
}

.back-button .button-icon {
  margin-right: 5px;
  width: 16px;
  height: 16px;
}

.back-button:hover {
  color: #666;
}

.header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: bold;
  font-family: 'Lora', serif;
}

.main-content {
  display: flex;
  gap: 40px;
  margin-bottom: 60px;
  margin-top: 50px;
  flex-direction: row;
  margin-left: -200px;
}

.image-section {
  flex: 1;
  width: 200px;
  position: relative;
}

.main-image-container {
  position: relative;
  width: 100%;
  height: 559px;
  background-color: #f5f5f5;
}

/* OpenSeadragon 容器样式 */
#openseadragon-container {
  width: 100%;
  height: 100%;
}

/* 自定义控制按钮样式 */
.custom-controls {
  position: absolute;
  bottom: 20px;
  right: 20px;
  display: flex;
  gap: 10px;
  z-index: 10;
}

.custom-controls button {
  width: 40px;
  height: 40px;
  border: none;
  background: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #333;
  font-size: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
  padding: 0;
}

.custom-controls button:hover {
  background: #f0f0f0;
  transform: scale(1.1);
}

.button-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.info-section {
  flex: 1;
  max-width: 500px;
  margin-right: -100px;
  height: 500px;
}

.info-card {
  padding: 0;
}

.info-card h2 {
  margin-top: 0;
  margin-bottom: 25px;
  font-size: 24px;
  font-weight: 300;
  font-family: 'Lora', serif;
}

.info-item {
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ddd;
  display: flex;
}

.info-item .label {
  font-size: 15px;
  font-weight: 500;
  color: #666;
  min-width: 80px;
}

.info-item .value {
  color: #333;
  flex: 1;
}

.description {
  white-space: pre-line;
  line-height: 1.6;
}

.related-section {
  margin-top: 60px;
  margin-left: -200px;
  width: 1450px;
  background-color: #fff;
}

.related-title {
  margin-bottom: 10px;
  font-size: 29px;
  font-weight: 750;
  margin-bottom: 10px;
  padding: 10px;
  font-family: 'Lora', serif;
  border-bottom: 1px solid #d3d3d3;
}

.divider {
  height: 0px;
  background-color: #000;
  margin: 20px 0 40px;
}

.masonry-grid {
  columns: 4;
  column-gap: 20px;
}

.masonry-item {
  break-inside: avoid;
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.3s;
  background: #fff;
  border-bottom: 2px solid #fff;
  border-radius: 4px;
  overflow: hidden;
}

.masonry-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.masonry-item img {
  width: 100%;
  height: auto;
  display: block;
  background-color: #f5f5f5;
}

.item-info {
  padding: 15px;
}

.item-name {
  font-weight: 500;
  margin-bottom: 5px;
  font-size: 16px;
  font-style: italic;
}

.item-artist {
  font-size: 14px;
  margin-bottom: 3px;
}

.item-period,
.item-museum {
  font-size: 14px;
  margin-bottom: 3px;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@media (max-width: 1200px) {
  .main-content {
    flex-direction: column;
  }

  .masonry-grid {
    columns: 2;
  }
}

@media (max-width: 600px) {
  .masonry-grid {
    columns: 1;
  }

  .main-image-container {
    height: 400px;
  }

  .custom-controls {
    top: 10px;
    right: 10px;
  }
}
</style>