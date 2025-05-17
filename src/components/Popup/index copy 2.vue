<template>
  <div v-if="visible" class="popup-container">
    <div class="popup">
      <button class="close-btn" @click="closePopup">×</button>
      <div class="video-section">
        <div
          v-for="(url, index) in videoUrls"
          :key="index"
          class="video-container"
        >
          <video
            v-if="url.endsWith('.mp4')"
            :src="url"
            controls
            class="video"
          ></video>
          <img v-else :src="url" alt="Video/Img" class="image" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 定义 props
const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
  videoUrls: {
    type: Array,
    required: true,
    default: () => ["", "", ""],
  },
});

// 定义 emits
const emit = defineEmits(["close"]);

// 关闭弹出框的函数
const closePopup = () => {
  emit("close");
};
</script>

<style scoped>
.popup-container {
  position: absolute;
  top: 0; /* 固定在页面左侧的顶部位置 */
  left: 0; /* 固定在页面左侧的左边距 */
  z-index: 1000;
  /* height: 100%; */
}

.popup {
  background: rgba(255, 255, 255, 0.9);
  color: black;
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
  width: 300px;
  /* height: 100%; */
}

.close-btn {
  position: absolute;
  top: 5px;
  right: 5px;
  background: none;
  border: none;
  font-size: 20px;
  color: black;
  cursor: pointer;
}

.close-btn:hover {
  color: red;
}

.video-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

.video-container {
  text-align: center;
}

.video {
  width: 100%;
  border-radius: 8px;
}

.image {
  width: 100%;
  border-radius: 8px;
}
</style>
