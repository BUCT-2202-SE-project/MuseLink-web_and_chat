<template>
  <div class="knowledge-container">
    <div class="nav-placeholder"></div>

    <div class="content-wrapper">
      <div class="left-sidebar">
        <div class="museum-selector">
          <label>museum</label>
          <select v-model="selectedMuseum" @change="loadData">
            <option value="">-- 请选择 --</option>
            <option v-for="museum in museums" :key="museum.name" :value="museum.name">
              {{ museum.name }}
            </option>
          </select>
        </div>

        <div class="display-options">
          <div class="option-section">
            <div class="section-title">node</div>
            <div class="option-tags">
              <span
                v-for="type in nodeTypes"
                :key="type.value"
                class="tag"
                :class="{ 'active': selectedDisplay === type.value }"
                :style="{ backgroundColor: type.color }"
                @click="selectDisplay(type.value)"
              >
                {{ type.label }}
              </span>
              <span
                class="tag all-tag"
                :class="{ 'active': selectedDisplay === 'all' }"
                @click="selectDisplay('all')"
                style="background-color: #666;"
              >
                全部展示
              </span>
            </div>
          </div>

          <div class="option-section">
            <div class="section-title">relationship</div>
            <div class="option-tags">
              <span
                v-for="rel in relTypes"
                :key="rel.value"
                class="tag"
                :class="{ 'active': selectedDisplay === rel.value }"
                :style="{ backgroundColor: rel.color }"
                @click="selectDisplay(rel.value)"
              >
                {{ rel.label }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="graph-area">
        <div v-if="!selectedMuseum" class="empty-tip">请先选择博物馆</div>
        <div v-else-if="graphData.nodes.length === 0" class="empty-tip">没有找到数据</div>
        <div v-else ref="graphContainer" class="graph"></div>

        <!-- Control buttons -->
        <div class="graph-controls">
          <button class="control-btn download-btn" @click="downloadImage" title="下载图片">
            <i class="icon-download"></i>
          </button>
          <button class="control-btn toggle-btn" @click="toggleSidebar" :title="sidebarVisible ? '隐藏边栏' : '显示边栏'">
            <i :class="sidebarVisible ? 'icon-hide' : 'icon-show'"></i>
          </button>
        </div>
      </div>

      <div class="right-sidebar" v-show="sidebarVisible">
        <div class="sidebar-header">
          <h4 class="detail-label">details</h4>
          <button class="close-btn" @click="toggleSidebar">&times;</button>
        </div>

        <!-- Table displaying the selected node's key-value pairs -->
        <el-table :data="tableData" stripe style="width: 100%">
          <el-table-column prop="key" label="Key" width="180" />
          <el-table-column prop="value" label="Value" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script>
import * as d3 from 'd3';
import { saveSvgAsPng } from 'save-svg-as-png';
import { ElTable } from 'element-plus';

export default {
  name: 'KnowledgeGraph',
  data() {
    return {
      museums: [],
      selectedMuseum: '',
      nodeTypes: [
        { value: 'Artifact', label: '文物', color: '#e7c66b' },
        { value: 'Artist', label: '作者', color: '#76b7b2' },
        { value: 'Period', label: '时期', color: '#e15759' }
      ],
      relTypes: [
        { value: '包含', label: '包含', color: '#d3d3d3' },
        { value: '作者', label: '作者', color: '#ffc0cb' },
        { value: '年代', label: '年代', color: '#8da0cb' }
      ],
      selectedDisplay: 'Artifact',
      graphData: { nodes: [], links: [] },
      selectedNode: null,
      simulation: null,
      svg: null,
      linkGroup: null,
      nodeGroup: null,
      zoomBehavior: null,
      gZoom: null,
      sidebarVisible: true,
      tableData: []
    };
  },
  mounted() {
    this.fetchMuseums();
    window.addEventListener('resize', this.renderGraph);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.renderGraph);
    if (this.simulation) {
      this.simulation.stop();
    }
  },
  methods: {
    async fetchMuseums() {
      try {
        const response = await fetch('http://172.20.10.3:3200/api/museums');
        this.museums = await response.json();
      } catch (error) {
        console.error('获取博物馆失败:', error);
      }
    },
    async loadData() {
      if (!this.selectedMuseum) return;
      try {
        const response = await fetch(
          `http://172.20.10.3:3200/api/graph?museum_name=${encodeURIComponent(this.selectedMuseum)}&display_type=${this.selectedDisplay}`
        );
        this.graphData = await response.json();
        this.selectedNode = null;
        this.tableData = [];
        this.renderGraph();
      } catch (error) {
        console.error('获取数据失败:', error);
      }
    },
    selectDisplay(type) {
      this.selectedDisplay = type;
      this.loadData();
    },
    getTypeName(type) {
      const names = {
        'Artifact': '文物',
        'Artist': '作者',
        'Period': '时期',
        'Museum': '博物馆'
      };
      return names[type] || type;
    },
    getNodeColor(type) {
      const colors = {
        'Artifact': '#e7c66b',
        'Artist': '#76b7b2',
        'Period': '#e15759',
        'Museum': '#4e79a7'
      };
      return colors[type] || '#59a14f';
    },
    renderGraph() {
      if (!this.$refs.graphContainer) return;

      d3.select(this.$refs.graphContainer).selectAll('*').remove();

      const container = this.$refs.graphContainer;
      const width = container.clientWidth;
      const height = container.clientHeight;

      this.svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .style('cursor', 'grab');

      this.gZoom = this.svg.append('g');

      const markerColors = {
        '包含': '#d3d3d3',
        '作者': '#ffc0cb',
        '年代': '#8da0cb'
      };

      this.svg.append('defs').selectAll('marker')
        .data(this.relTypes)
        .enter().append('marker')
        .attr('id', d => `arrow-${d.value}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 50)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', d => markerColors[d.value]);

      this.linkGroup = this.gZoom.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(this.graphData.links)
        .enter().append('line')
        .attr('stroke', d => markerColors[d.type] || '#999')
        .attr('stroke-width', 2)
        .attr('marker-end', d => `url(#arrow-${d.type})`);

      this.nodeGroup = this.gZoom.append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(this.graphData.nodes)
        .enter().append('g')
        .style('cursor', 'pointer')
        .on('click', (event, d) => {
          event.stopPropagation();
          this.selectedNode = d;
          this.updateTableData(d);
          this.highlightSelectedNode(d.id);
          this.sidebarVisible = true;
        })
        .call(d3.drag()
          .on('start', (event, d) => {
            if (!event.active) this.simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) this.simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
        );


      this.nodeGroup.append('circle')
        .attr('r', 50)
        .attr('fill', d => this.getNodeColor(d.type))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);

      this.nodeGroup.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', 5)
        .attr('fill', '#fff')
        .text(d => d.name.length > 6 ? d.name.substring(0, 6) + '...' : d.name);


      this.simulation = d3.forceSimulation(this.graphData.nodes)
        .force('link', d3.forceLink(this.graphData.links).id(d => d.id).distance(200))
        .force('charge', d3.forceManyBody().strength(-500))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(60))
        .on('tick', () => {
          this.linkGroup
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

          this.nodeGroup
            .attr('transform', d => `translate(${d.x},${d.y})`);
        });

      this.zoomBehavior = d3.zoom()
        .scaleExtent([0.3, 3])
        .on('zoom', event => {
          this.gZoom.attr('transform', event.transform);
        });

      this.svg.call(this.zoomBehavior);

      this.svg.on('click', () => {
        this.selectedNode = null;
        this.clearHighlight();
      });
    },
    updateTableData(node) {
      const nodeDetails = [];
      for (const [key, value] of Object.entries(node.properties)) {
        nodeDetails.push({ key, value });
      }
      this.tableData = nodeDetails;
    },
    highlightSelectedNode(selectedId) {
      this.nodeGroup.selectAll('circle').attr('opacity', d => (d.id === selectedId ? 1 : 0.3));
      this.nodeGroup.selectAll('text').attr('opacity', d => (d.id === selectedId ? 1 : 0.3));
      this.linkGroup.attr('opacity', d => (d.source.id === selectedId || d.target.id === selectedId ? 1 : 0.1));
    },
    clearHighlight() {
      this.nodeGroup.selectAll('circle').attr('opacity', 1);
      this.nodeGroup.selectAll('text').attr('opacity', 1);
      this.linkGroup.attr('opacity', 1);
    },
    downloadImage() {
      if (!this.svg) return;
      const svgElement = this.svg.node();
      saveSvgAsPng(svgElement, 'knowledge-graph.png', {
        scale: 2,
        backgroundColor: '#ffffff'
      });
    },
    toggleSidebar() {
      this.sidebarVisible = !this.sidebarVisible;
    }
  },
  watch: {
    selectedMuseum(newVal) {
      this.loadData();
    },
    selectedDisplay(newVal) {
      this.loadData();
    }
  }
};
</script>

<style scoped>

.knowledge-container {
  padding-top: 100px;
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: 'Microsoft YaHei', sans-serif;
  margin-left: -230px;
  color: #333;
}

.nav-placeholder {
  height: 18px;
}

.content-wrapper {
  display: flex;
  flex: 1;
  width: 1600px;
  overflow: hidden;
  background-color: #fff;
}

.left-sidebar {
  background-color: #fff;
  border-right: 1px solid #dcdcdc;
  padding: 15px;
  box-sizing: border-box;
  overflow-y: auto;
  width: 300px;
  margin-left: -5px;
}

.museum-selector label {
  font-weight: bold;
}

.museum-selector select {
  width: 100%;
  margin-top: 6px;
  padding: 6px;
  border-radius: 4px;
  border: 1px solid #ddd;
  font-size: 14px;
}

.display-options {
  margin-top: 20px;
}

.option-section {
  margin-bottom: 20px;
}

.section-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.option-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}


.tag {
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 20px;
  color: white;
  font-size: 14px;
  user-select: none;
  transition: all 0.3s ease;
}


.tag:hover {
  background-color: #3a5f8a;
  transform: scale(1.1);
}


.tag.active {
  background-color: #4e79a7;
  font-weight: 700;
}

.all-tag {
  font-weight: 600;
}

.graph-area {
  flex: 1;
  background-color: #fff;
  position: relative;
  min-width: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  margin-left:0px;
}

.graph {
  margin-top:0px;
  width: 1500px;
  background-color: #f0f0f0;
  height: 100%;
}

.empty-tip {
  color: #aaa;
  font-size: 18px;
}

.right-sidebar {
  width: 400px;
  background-color: #fff;
  border-left: 1px solid #dcdcdc;
  padding: 15px;
  box-sizing: border-box;
  overflow-y: auto;
  transition: all 0.3s ease;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
  padding: 0 5px;
}

.close-btn:hover {
  color: #333;
}

.node-details {
  margin-top: 10px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-row {
  margin-bottom: 10px;
  display: flex;
}

.detail-label {
  width: 90px;
  margin-right: 10px;
  font-weight: 700;
  color: #555;
}

.detail-value {
  flex: 1;
  word-break: break-word;
}

a {
  color: #1890ff;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

.graph-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 10;
}

.control-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background-color: #d3d3d3;
  color: white;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.control-btn:hover {
  background-color: #3a5f8a;
  transform: scale(1.1);
}

.download-btn {
  background-color: #d3d3d3;
}

.toggle-btn {
  background-color: #d3d3d3;
}

.icon-download:before {
  content: "↓";
}

.icon-hide:before {
  content: "◄";
}

.icon-show:before {
  content: "►";
}

.el-table {
  margin-top: 20px;
}
</style>
