<template>
  <transition name="fade">
    <div class="advanced-search-overlay" v-if="visible" @click.self="closePanel">
      <div class="advanced-search-panel" ref="panel" :style="{ height: panelHeight + 'px' }">
        <div class="panel-header" @mousedown="startDrag">
          <h2>高级搜索</h2>
          <button class="close-btn" @click="closePanel">
            <svg viewBox="0 0 24 24" width="24" height="24">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>

        <div class="panel-body">
          <div class="filter-row">
            <div class="filter-group">
              <label>文物名称</label>
              <input type="text" v-model="filters.title" placeholder="输入文物名称">
            </div>

            <div class="filter-group">
              <label>博物馆</label>
              <select v-model="filters.museum">
                <option value="">选择博物馆</option>
                <option v-for="museum in museumOptions" :key="museum.value" :value="museum.value">
                  {{ museum.label }}
                </option>
              </select>
            </div>
          </div>

          <div class="filter-row">
            <div class="filter-group">
              <label>年代</label>
              <input type="text" v-model="filters.period" placeholder="例如：1800-1900">
            </div>

            <div class="filter-group">
              <label>艺术家</label>
              <input type="text" v-model="filters.artist" placeholder="输入艺术家名称">
            </div>
          </div>

          <div class="filter-group full-width">
            <label>描述关键词</label>
            <textarea v-model="filters.descripe" placeholder="输入描述关键词" rows="7"></textarea>
          </div>
        </div>

        <div class="panel-footer">
          <button class="reset-btn" @click="resetFilters">重置</button>
          <button class="search-btn" @click="executeSearch">开始搜索</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'AdvancedSearchPanel',
  props: {
    visible: Boolean
  },
  data() {
    return {
      filters: {
        title: '',
        museum: '',
        period: '',
        descripe: '',
        artist: ''
      },
      museumOptions: [
        { value: '大都会博物馆', label: '大都会博物馆' },
        { value: '宾夕法尼亚大学考古与人类学博物馆', label: '宾夕法尼亚大学' },
        { value: '克利夫兰博物馆', label: '克利夫兰博物馆' }
      ],
      isDragging: false,
      startY: 0,
      panelHeight: window.innerHeight * 0.66,
      minHeight: 300,
      maxHeight: window.innerHeight * 0.9
    };
  },
  methods: {
    closePanel() {
      this.$emit('close');
    },
    resetFilters() {
      this.filters = {
        title: '',
        museum: '',
        period: '',
        descripe: '',
        artist: ''
      };
    },
    executeSearch() {
      const activeTags = [];

      // 转换过滤条件为标签格式
      if (this.filters.title) {
        activeTags.push({ field: 'Title', value: this.filters.title });
      }
      if (this.filters.museum) {
        activeTags.push({ field: 'Museum', value: this.filters.museum });
      }
      if (this.filters.period) {
        activeTags.push({ field: 'Period', value: this.filters.period });
      }
      if (this.filters.artist) {
        activeTags.push({ field: 'Artist', value: this.filters.artist });
      }
      if (this.filters.descripe) {
        activeTags.push({ field: 'descripe', value: this.filters.descripe });
      }

      // 跳转回首页并传递标签参数
      this.$router.push({
        path: '/',
        query: {
          searchTags: JSON.stringify(activeTags)
        }
      });

      this.closePanel();
    },
    startDrag(e) {
      this.isDragging = true;
      this.startY = e.clientY;
      document.addEventListener('mousemove', this.onDrag);
      document.addEventListener('mouseup', this.stopDrag);
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';
    },
    onDrag(e) {
      if (!this.isDragging) return;
      const delta = this.startY - e.clientY;
      this.panelHeight = Math.min(
        this.maxHeight,
        Math.max(this.minHeight, this.panelHeight + delta)
      );
      this.startY = e.clientY;
    },
    stopDrag() {
      this.isDragging = false;
      document.removeEventListener('mousemove', this.onDrag);
      document.removeEventListener('mouseup', this.stopDrag);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    },
    handleResize() {
      this.maxHeight = window.innerHeight * 0.9;
      if (this.panelHeight > this.maxHeight) {
        this.panelHeight = this.maxHeight;
      }
    }
  },
  mounted() {
    window.addEventListener('resize', this.handleResize);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
    this.stopDrag();
  }
}
</script>

<style scoped>
/* 保持原有的样式不变 */
.advanced-search-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: flex-end;
}

.advanced-search-panel {
  background: #fff;
  width: 100%;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  overflow: hidden;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  border: 1px solid #e0e0e0;
}

.panel-header {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
  cursor: row-resize;
  background: #f8f8f8;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #222;
  font-weight: 500;
}

.close-btn {
  background: none;
  border: none;
  padding: 5px;
  cursor: pointer;
  color: #666;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #222;
}

.panel-body {
  padding: 20px;
  overflow-y: auto;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-row {
  display: flex;
  gap: 20px;
  width: 100%;
}

.filter-group {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.filter-group.full-width {
  flex: 0 0 100%;
}

.filter-group label {
  margin-bottom: 8px;
  font-weight: 500;
  color: #444;
  font-size: 0.95rem;
}

.filter-group input[type="text"],
.filter-group select,
.filter-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  background: #fff;
  color: #333;
  transition: border 0.2s;
}

.filter-group input[type="text"]:focus,
.filter-group select:focus,
.filter-group textarea:focus {
  border-color: #999;
  outline: none;
}

.filter-group textarea {
  min-height: 80px;
  resize: vertical;
}

.filter-group select {
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 16px;
}

.panel-footer {
  padding: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  border-top: 1px solid #f0f0f0;
  background: #f8f8f8;
}

.reset-btn, .search-btn {
  padding: 10px 24px;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.reset-btn {
  background: #fff;
  border-color: #ddd;
  color: #444;
}

.reset-btn:hover {
  background: #f0f0f0;
}

.search-btn {
  background: #222;
  color: white;
}

.search-btn:hover {
  background: #444;
}

@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
    gap: 20px;
  }

  .panel-body {
    padding: 15px;
  }

  .panel-header, .panel-footer {
    padding: 15px;
  }
}
</style>