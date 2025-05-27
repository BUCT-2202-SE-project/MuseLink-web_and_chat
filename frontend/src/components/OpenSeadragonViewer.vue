<template>
  <div class="openseadragon-container" ref="viewerContainer">
    <div class="osd-toolbar" v-if="showControls">
      <button @click="zoomIn" title="放大">
        <img src="@/components/icons/zoom-in.png" class="button-icon" alt="放大" />
      </button>
      <button @click="zoomOut" title="缩小">
        <img src="@/components/icons/zoom-out.png" class="button-icon" alt="缩小" />
      </button>
      <button @click="home" title="重置">
        <img src="@/components/icons/refresh.png" class="button-icon" alt="重置" />
      </button>
      <button @click="toggleFullscreen" :title="isFullscreen ? '退出全屏' : '全屏'">
        <img :src="isFullscreen ? require('@/components/icons/fullscreen-exit.png') : require('@/components/icons/fullscreen.png')"
             class="button-icon" :alt="isFullscreen ? '退出全屏' : '全屏'" />
      </button>
    </div>
  </div>
</template>

<script>
import OpenSeadragon from 'openseadragon'
import { onMounted, ref, watch, onBeforeUnmount } from 'vue'

export default {
  name: 'OpenSeadragonViewer',
  props: {
    imageUrl: {
      type: String,
      required: true
    },
    showControls: {
      type: Boolean,
      default: true
    },
    tileSources: {
      type: Object,
      default: null
    }
  },
  setup(props, { emit }) {
    const viewer = ref(null)
    const viewerContainer = ref(null)
    const isFullscreen = ref(false)
    const corsProxy = 'https://cors-anywhere.herokuapp.com/'
const imageUrl = props.imageUrl.includes('metmuseum.org') 
  ? `${corsProxy}${props.imageUrl}`
  : props.imageUrl
    const initViewer = () => {
      if (viewer.value) {
        viewer.value.destroy()
      }

      const options = {
        element: viewerContainer.value,
        prefixUrl: 'https://cdn.jsdelivr.net/npm/openseadragon@3.1/build/openseadragon/images/',
        tileSources: props.tileSources || `https://cors-anywhere.herokuapp.com/${props.imageUrl}`,
        showNavigator: true,
        navigatorPosition: 'TOP_RIGHT',
        navigatorHeight: '120px',
        navigatorWidth: '180px',
        gestureSettingsMouse: {
          scrollToZoom: true,
          clickToZoom: true,
          dblClickToZoom: true,
          pinchToZoom: true
        },
        zoomInButton: 'zoom-in',
        zoomOutButton: 'zoom-out',
        homeButton: 'home',
        fullPageButton: 'fullscreen',
        timeout: 120000,
        animationTime: 0.5,
        maxZoomPixelRatio: 3,
        visibilityRatio: 1,
        constrainDuringPan: true
      }

      viewer.value = OpenSeadragon(options)

      viewer.value.addHandler('open', () => {
        emit('loaded')
      })

      viewer.value.addHandler('zoom', (data) => {
        emit('zoom', data.zoom)
      })

      viewer.value.addHandler('pan', (data) => {
        emit('pan', data.center)
      })
    }

    const zoomIn = () => {
      if (viewer.value) {
        viewer.value.viewport.zoomBy(1.5)
      }
    }

    const zoomOut = () => {
      if (viewer.value) {
        viewer.value.viewport.zoomBy(0.6667)
      }
    }

    const home = () => {
      if (viewer.value) {
        viewer.value.viewport.goHome()
      }
    }

    const toggleFullscreen = () => {
      if (viewer.value) {
        if (isFullscreen.value) {
          viewer.value.setFullScreen(false)
        } else {
          viewer.value.setFullScreen(true)
        }
        isFullscreen.value = !isFullscreen.value
      }
    }

    onMounted(() => {
      initViewer()
    })

    watch(() => props.imageUrl, () => {
      initViewer()
    })

    watch(() => props.tileSources, () => {
      initViewer()
    })

    onBeforeUnmount(() => {
      if (viewer.value) {
        viewer.value.destroy()
      }
    })

    return {
      viewer,
      viewerContainer,
      isFullscreen,
      zoomIn,
      zoomOut,
      home,
      toggleFullscreen
    }
  }
}
</script>

<style scoped>
.openseadragon-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.osd-toolbar {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  gap: 10px;
  background: rgba(255, 255, 255, 0.8);
  padding: 8px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.osd-toolbar button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: all 0.2s;
}

.osd-toolbar button:hover {
  background-color: #f0f0f0;
}

.button-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
}
</style>