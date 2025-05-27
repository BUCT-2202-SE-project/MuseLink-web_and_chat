<template>
  <div class="timeline-container">
    <iframe
      class="timeline-iframe"
      :src="iframeSrc"
      frameborder="0"
      allowfullscreen
    ></iframe>
  </div>
</template>

<script setup>
const iframeSrc =
  'https://cdn.knightlab.com/libs/timeline3/latest/embed/index.html?source=v2:2PACX-1vSQDZuqQcpYudyRjVZtGlJhVJ5nMv96C3O9ohSG1N31KR37iILESAfWkMOakfNG5w9nKt6ZtgIddxOK&font=Default&lang=en&initial_zoom=2';
</script>

<style scoped>
.timeline-container {
  width: 1790px;
  height: 100vh;
  display: flex;
  margin-left: -320px; /* 整体向左移动100像素 */
  overflow: hidden;
}

.timeline-iframe {
  width: 100%; /* 你可以改成更小的宽度看得更明显 */
  height: 100%;
  border: none;
}
</style>
