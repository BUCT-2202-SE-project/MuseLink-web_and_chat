<template>
  <el-backtop :right="100" :bottom="100" />
  <div class="gallery-wrapper">
    <!-- 搜索框部分 -->
    <div class="search-container">
      <div class="search-box">
        <div class="search-field-selector">
          <select v-model="selectedField">
            <option value="all">ALL</option>
            <option v-for="field in searchableFields" :key="field.name" :value="field.name">
              {{ field.label }}
            </option>
          </select>
        </div>
        <input
          type="text"
          v-model="searchQuery"
          :placeholder="getPlaceholder()"
          @keyup.enter="addSearchTagFromInput"
        />
        <button @click="addSearchTagFromInput">
          <img src="@/components/icons/search.png" alt="搜索" class="search-icon" />
        </button>
      </div>



      <!-- 搜索标签展示区 -->
      <div class="search-tags" v-if="activeTags.length > 0">
        <div class="tag" v-for="(tag, index) in activeTags" :key="index">
          <span class="tag-field">{{ getFieldLabel(tag.field) }}:</span>
          <span class="tag-value">{{ tag.value }}</span>
          <span class="tag-remove" @click="removeTag(index)">×</span>
        </div>
      </div>
      <!-- 排序部分 -->
      <div class="sort-container">
        <span>Sort by:</span>
        <select v-model="sortOrder" @change="fetchArtifacts">
          <option value="asc">Title A-Z</option>
          <option value="desc">Title Z-A</option>
        </select>
      </div>
      <!-- 显示当前展示的数据数量 -->
      <div class="display-count">
        当前展示: {{ displayedCount }} / {{ totalCount }} 件文物
      </div>
    </div>

    <!-- 文物展示区 -->
    <div
      class="gallery-container"
      v-infinite-scroll="loadMore"
      :infinite-scroll-disabled="busy"
      infinite-scroll-distance="100"
    >
      <div
        v-for="artifact in displayedArtifacts"
        :key="artifact['Object ID']"
        class="gallery-item"
        @click="goToDetail(artifact['Object ID'])"
      >
        <div class="item-image">
          <img :src="artifact.Image" :alt="artifact.Title" loading="lazy" />
        </div>
        <div class="item-info">
          <h3>{{ artifact.Title }}</h3>
          <p>{{ formatField(artifact.Artist, '艺术家') }}</p>
          <p>{{ formatField(artifact.Period, '年代') }}</p>
          <p>{{ formatField(artifact.Museum, '博物馆') }}</p>
        </div>
      </div>
    </div>

    <!-- 加载状态提示 -->
    <div v-if="loading" class="loading-more">
      加载中...
    </div>
    <div v-if="noMoreData" class="no-more-data">
      没有更多数据了
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue';
import axios from 'axios';
import { useRouter, useRoute } from 'vue-router';

export default {
  name: 'Home',
  setup() {
    const allArtifacts = ref([]);
    const displayedArtifacts = ref([]);
    const router = useRouter();
    const route = useRoute();
    const searchQuery = ref('');
    const activeTags = ref([]);
    const selectedField = ref('all');
    const currentPage = ref(1);
    const itemsPerPage = 20; // 初始加载20条
    const busy = ref(false);
    const loading = ref(false);
    const noMoreData = ref(false);
    const sortOrder = ref('asc'); // 排序字段

    // 可搜索字段配置
    const searchableFields = [
      { name: 'Title', label: '名称', param: 'title' },
      { name: 'Artist', label: '艺术家', param: 'artist' },
      { name: 'Period', label: '年代', param: 'period' },
      { name: 'Museum', label: '博物馆', param: 'museum' },
      { name: 'descripe', label: '描述', param: 'descripe' }
    ];

    // 计算属性
    const displayedCount = computed(() => displayedArtifacts.value.length);
    const totalCount = computed(() => allArtifacts.value.length);

    // 从URL参数初始化搜索标签
    const initSearchTagsFromQuery = () => {
      if (route.query.searchTags) {
        try {
          const tags = JSON.parse(route.query.searchTags);
          activeTags.value = tags;
        } catch (e) {
          console.error('解析搜索标签失败:', e);
        }
      }
    };

    // 获取文物数据
    const fetchArtifacts = async () => {
      try {
        loading.value = true;
        noMoreData.value = false;

        // 构造查询参数（合并相同字段的条件）
        const params = {};

        // 按字段分组
        const fieldGroups = {};
        activeTags.value.forEach(tag => {
          if (tag.field === 'all') {
            params['q'] = tag.value;
          } else {
            const field = searchableFields.find(f => f.name === tag.field);
            if (field) {
              fieldGroups[field.param] = fieldGroups[field.param] || [];
              fieldGroups[field.param].push(tag.value);
            }
          }
        });

        // 将同字段多个值用逗号连接
        Object.entries(fieldGroups).forEach(([param, values]) => {
          params[param] = values.join(',');
        });

        // 传递排序参数
        params['sort'] = sortOrder.value;

        const response = await axios.get('http://172.20.10.3:3200/api/artifacts', { params });
        allArtifacts.value = response.data.filter(artifact =>
          artifact.Image &&
          (artifact.Image.startsWith('http://') || artifact.Image.startsWith('https://'))
        );

        // 重置分页
        currentPage.value = 1;
        displayedArtifacts.value = allArtifacts.value.slice(0, itemsPerPage);

        // 检查是否还有更多数据
        noMoreData.value = displayedArtifacts.value.length >= allArtifacts.value.length;
      } catch (error) {
        console.error('获取数据失败:', error);
      } finally {
        loading.value = false;
        busy.value = false;
      }
    };

    // 加载更多数据
    const loadMore = () => {
      if (busy.value || noMoreData.value) return;

      busy.value = true;
      loading.value = true;

      setTimeout(() => {
        currentPage.value += 1;
        const nextItems = allArtifacts.value.slice(
          displayedArtifacts.value.length,
          displayedArtifacts.value.length + itemsPerPage
        );

        displayedArtifacts.value = [...displayedArtifacts.value, ...nextItems];

        // 检查是否还有更多数据
        noMoreData.value = displayedArtifacts.value.length >= allArtifacts.value.length;

        busy.value = false;
        loading.value = false;
      }, 1000); // 模拟延迟
    };

    // 添加搜索标签
    const addSearchTagFromInput = () => {
      if (!searchQuery.value.trim()) return;

      const newTag = {
        field: selectedField.value,
        value: searchQuery.value.trim()
      };

      // 避免重复标签
      if (!activeTags.value.some(tag => tag.field === newTag.field && tag.value === newTag.value)) {
        activeTags.value.push(newTag);
        updateUrlWithTags();
      }

      searchQuery.value = '';
    };

    // 移除标签
    const removeTag = (index) => {
      activeTags.value.splice(index, 1);
      updateUrlWithTags();
    };

    // 更新URL中的标签参数
    const updateUrlWithTags = () => {
      router.replace({
        query: {
          searchTags: activeTags.value.length > 0 ? JSON.stringify(activeTags.value) : undefined
        }
      });
    };

    // 辅助方法
    const getFieldLabel = (fieldName) => {
      const field = searchableFields.find(f => f.name === fieldName);
      return field ? field.label : '所有字段';
    };

    const getPlaceholder = () => {
      return selectedField.value === 'all'
        ? 'Search the Collection'
        : `按${getFieldLabel(selectedField.value)}搜索`;
    };

    const formatField = (value, label) => {
      const emptyValues = ['未知', 'unknown', '无', '暂无'];
      return (!value || emptyValues.includes(value.toString().trim().toLowerCase()))
        ? `未知${label}` : value;
    };

    const goToDetail = (id) => {
      router.push({ path: '/detail', query: { id } });
    };

    // 初始化和监听
    onMounted(() => {
      initSearchTagsFromQuery();
      fetchArtifacts();
    });

    watch(activeTags, () => {
      fetchArtifacts();
    }, { deep: true });

    watch(() => route.query, () => {
      initSearchTagsFromQuery();
    });

    return {
      allArtifacts,
      displayedArtifacts,
      searchQuery,
      activeTags,
      selectedField,
      searchableFields,
      displayedCount,
      totalCount,
      loading,
      noMoreData,
      sortOrder, // 排序字段
      addSearchTagFromInput,
      removeTag,
      getFieldLabel,
      getPlaceholder,
      formatField,
      goToDetail,
      loadMore,
      fetchArtifacts,
    };
  }
};
</script>

<style scoped>

.sort-container {
  width: 200px;
  height: 40px;
  display: flex;
  align-items: center;
  background-color: black;
  color: white;
  padding: 10px 20px;
  margin-top: 0px;
  margin-bottom: -40px;
  margin-left: 980px;
  border-radius: 0px;
}

.sort-container select {
  background-color: black;
  color: white;
  border: 2px solid black;
  font-size: 16px;
  margin-left: 10px;
  padding: 5px;
  border-radius: 0;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3e%3cpath d='M7 10l5 5 5-5z'/%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 5px center;
  background-size: 16px;
  padding-right: 25px;
}


.sort-container select:focus {
  outline: none;
}


.sort-container select option {
  background-color: white;
  color: black;
  padding: 8px;
  border: 1px solid black;
}


.sort-container select option-list {
  border: 1px solid black;
  border-radius: 0 !important;
}

.sort-container select:hover {
  opacity: 0.9;
}
.sort-container span {
  font-size: 16px;
}


.el-backtop {
  background-color: #fff;
  border: 2px solid #000;
  border-radius: 50%;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 50px;
  height: 50px;
  color: #000;
  font-size: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.3s ease;
}


.el-backtop:hover {
  background-color: #000;
  color: #fff;
  transform: scale(1.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.gallery-wrapper {
  padding: 0;
  width: 1200px;
  margin: 0 auto;
  margin-top: 10px;
}

.gallery-container {
  margin-left:-50px;
  column-count: 4;
  column-gap: 20px;
}

.gallery-item {
  display: inline-block;
  width: 100%;
  margin-bottom: 20px;
  break-inside: avoid;
  overflow: hidden;
  border-radius: 0;
  background: none;
  box-shadow: none;
  transition: transform 0.3s ease;
}

.gallery-item:hover {
  transform: translateY(-3px);
}

.item-image {
  width: 100%;
  overflow: hidden;
}

.item-image img {
  width: 100%;
  display: block;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.gallery-item:hover .item-image img {
  transform: scale(1.05);
}

.item-info {
  padding: 6px 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.item-info h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.3s ease;
}

.gallery-item:hover .item-info h3 {
  color: #007bff;
}

.item-info p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.search-container {
  padding: 20px;
  width: 1200px;
  margin: 0 auto;
  margin-top: 120px;
  position: relative;
}

.search-box {
  display: flex;
  margin-bottom: 20px;
  margin-left:-70px;
  height: 60px;
  width:1250px;
  align-items: center;
  border-bottom: 3px solid black;
}

.search-field-selector {
  width: 120px;
  margin-right: 20px;
  margin-left: 20px;
}

.search-field-selector select {
  width: 100%;
  height: 100%;
  padding: 10px 10px 10px 10px;
  font-style: italic;
  border: none;
  outline: none;
  background-color: transparent;
  font-size: 20px;
  cursor: pointer;
}

.search-box input {
  flex: 1;
  padding: 20px 10px 15px 10px;
  font-size: 40px;
  border: none;
  outline: none;
  background: transparent;
  font-weight: bold;
  font-style: italic;
}

.search-box button {
  background-color: black;
  color: white;
  border: none;
  padding: 12px 18px;
  font-size: 18px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  margin-left: 10px;
}

.search-box button:hover {
  background-color: #333;
}

.search-box input::placeholder {
  font-size: 50px;
  color: #D3D3D3;
  font-style: italic;
}

.search-icon {
  font-size: 20px;
  width: 39px;
  height: 39px;
}

.search-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
  margin-left:-70px;
}

.tag {
  display: flex;
  align-items: center;
  background-color: #ffc0cb;
  padding: 8px 12px;
  border-radius: 20px;
  font-size: 14px;
  color: #333;
}

.tag-field {
  font-weight: bold;
  margin-right: 5px;
}

.tag-remove {
  margin-left: 8px;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}

.tag-remove:hover {
  color: #ff4757;
}

.display-count {
  margin: 10px 0 20px -70px;
  font-size: 14px;
  color: #666;
}

.loading-more, .no-more-data {
  text-align: center;
  padding: 20px;
  color: #666;
  font-size: 14px;
}


@media (max-width: 1200px) {
  .gallery-container {
    column-count: 3;
  }
}

@media (max-width: 800px) {
  .gallery-container {
    column-count: 2;
  }

  .search-box {
    flex-direction: column;
    height: auto;
  }

  .search-field-selector {
    width: 100%;
  }

  .search-field-selector select {
    width: 100%;
    padding: 12px;
    border-right: none;
    border-bottom: 1px solid #eee;
    font-family: 'Verdana', sans-serif;
  }

  .search-box input {
    padding: 12px;
  }

  .search-box button {
    padding: 12px;
  }
}

@media (max-width: 500px) {
  .gallery-container {
    column-count: 1;
  }
}
</style>
