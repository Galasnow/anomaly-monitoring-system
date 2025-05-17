<template>
  <div class="icon-grid">
    <div v-for="(icon, index) in icons" :key="index" class="icon-item">
      <div class="icon-container">
        <img :src="icon.src" :alt="icon.name" class="icon-image" />
      </div>
      <span class="icon-name">{{ icon.name }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

// 创建一个响应式数组来存储图标信息
const icons = ref<{ src: string; name: string }[]>([]);

// 加载图标的函数
const loadIcons = () => {
  // 使用 import.meta.glob 动态导入所有 SVG 图标
  const iconFiles = import.meta.glob("@/assets/icons2/*.svg");

  // 将导入的图标信息添加到 icons 数组中
  for (const path in iconFiles) {
    // 提取文件名作为名称
    const name = path.split("/").pop()?.replace(".svg", "") || "未命名";
    icons.value.push({ src: path, name });
  }
};

// 调用加载图标的函数
loadIcons();
</script>

<style scoped>
.icon-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr); /* 4 列布局 */
  gap: 16px; /* 网格间距 */
}

.icon-item {
  display: flex; /* 使用 Flexbox */
  flex-direction: column; /* 垂直排列 */
  align-items: center; /* 水平居中 */
  text-align: center; /* 中心对齐 */
}

.icon-container {
  display: flex; /* 使用 Flexbox 使图标上下左右居中 */
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
  height: 100px; /* 图标容器高度 */
  width: 100px; /* 图标容器宽度 */
}

.icon-image {
  max-width: 100%; /* 图标自适应宽度 */
  max-height: 100%; /* 图标自适应高度 */
}

.icon-name {
  margin-top: 8px; /* 名称与图标之间的间距 */
  font-size: 14px; /* 设置名称字体大小 */
}
</style>
