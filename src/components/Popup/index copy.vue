<template>
  <div v-if="visible" class="popup-container">
    <div class="popup">
      <div class="popup-header">
        <span>{{ location }}</span>
        <button class="close-btn" @click="closePopup">×</button>
      </div>
      <div class="video-section">
        <div
          v-for="(videourl, index) in videoUrls"
          :key="index"
          class="video-container"
        >
          <div class="video-info">
            <span>{{ deviceNames[index] }}</span>
            <span>{{ timestamps[index] }}</span>
          </div>
          <video
            v-if="videourl.endsWith('.mp4') || videourl.endsWith('.avi')"
            :src="videourl"
            loop
            autoplay
            muted
            class="video"
          ></video>
          <img v-else :src="videourl" alt="Video/Img" class="image" />
        </div>
      </div>
      <button class="fusion-btn" @click="openFusionPopup">去实时融合</button>
    </div>
  </div>

  <!-- 实时融合弹窗 -->
  <div v-if="fusionPopupVisible" class="fusion-popup-container">
    <div class="fusion-popup">
      <div class="fusion-popup-header">
        <span>实时融合</span>
        <button class="close-btn" @click="closeFusionPopup">×</button>
      </div>
      <div class="fusion-popup-body">
        <p>实时融合内容展示区域...</p>
        <el-form>
          <el-form-item label="MSS">
            <!-- 外部容器控制上传组件的大小 -->
            <div class="upload-wrapper">
              <single-upload v-model="Image1" />
            </div>
          </el-form-item>
        </el-form>

        <el-form>
          <el-form-item label="SAR">
            <!-- 外部容器控制上传组件的大小 -->
            <div class="upload-wrapper">
              <single-upload v-model="Image2" />
            </div>
          </el-form-item>
        </el-form>

        <!-- 提交按钮 -->
        <el-button
          type="primary"
          :disabled="isProcessing"
          @click="handleFusionProcess"
        >
          {{ isProcessing ? "正在融合中..." : "执行融合" }}
        </el-button>

        <!-- 处理后的图片显示框 -->
        <div v-if="resultImageUrl" class="result-wrapper">
          <img :src="resultImageUrl" alt="融合结果" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import SingleUpload from "@/components/Upload/SingleUpload.vue";
import { FusionRequest } from "@/api/lzjt/menu1/fusion/model";
import FusionAPI from "@/api/lzjt/menu1/fusion";
// 将 Image1 和 Image2 保存服务端返回的对象
const Image1 = ref({ name: "", url: "" });
const Image2 = ref({ name: "", url: "" });
const resultImageUrl = ref(""); // 保存处理后图片的URL
const isProcessing = ref(false); // 控制处理状态
// 点击处理按钮时触发的函数
const handleFusionProcess = async () => {
  // 防止重复点击
  if (isProcessing.value) return;

  if (!Image1.value.url || !Image2.value.url) {
    ElMessage.error("请上传两张影像后再执行融合操作!");
    return;
  }

  const requestData = {
    Image1_name: Image1.value.name,
    Image2_name: Image2.value.name,
  };

  try {
    // 显示加载状态
    isProcessing.value = true;

    // 发送请求到后端
    const response = await FusionAPI.startFusion(requestData);
    // 请求成功，返回处理后的图片URL
    resultImageUrl.value = response.url;
    ElMessage.success("融合完成!");
  } catch (error) {
    ElMessage.error("融合失败，请重试!");
    console.error(error);
  } finally {
    // 取消加载状态
    isProcessing.value = false;
  }
};

// 定义 props
const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
  videoUrls: {
    type: Array,
    required: true,
    default: () => [
      "https://example.com/video1.mp4",
      "https://example.com/video2.mp4",
      "https://example.com/video3.mp4",
    ],
  },
  deviceNames: {
    type: Array,
    required: true,
    default: () => ["设备1", "设备2", "设备3"],
  },
  timestamps: {
    type: Array,
    required: true,
    default: () => ["未知时间", "未知时间", "未知时间"],
  },
  location: {
    type: String,
    required: true,
    default: "未知地点",
  },
});

// 定义 emits
const emit = defineEmits(["close"]);

// 关闭弹出框的函数
const closePopup = () => {
  emit("close");
};

// 实时融合弹窗可见性状态
const fusionPopupVisible = ref(false);

// 打开实时融合弹窗
const openFusionPopup = () => {
  fusionPopupVisible.value = true;
};

// 关闭实时融合弹窗
const closeFusionPopup = () => {
  fusionPopupVisible.value = false;
};
</script>

<style lang="scss" scoped>
/** 关闭tag标签  */
.popup {
  height: calc(100vh - 50px);
}

/** 开启tag标签  */
.hasTagsView {
  .popup {
    height: calc(100vh - 84px);
  }
}

.popup-container {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1000;
  overflow-x: hidden;
  overflow-y: auto; /* 添加滚动条 */
}

.popup {
  background: rgba(255, 255, 255, 0.9);
  color: black;
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
  width: 300px;
  overflow-x: hidden;
  overflow-y: auto;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 20px;
  margin-bottom: 12px;
}

.close-btn {
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
  gap: 15px; /* 添加设备之间的间隙 */
}

.video-container {
  text-align: center;
}

.video-info {
  display: flex;
  justify-content: space-between; /* 设备和时间同一行 */
  font-size: 14px;
  margin-bottom: 5px; /* 与视频/图片之间的间隙 */
}

.video {
  width: 100%;
  border-radius: 8px;
}

.image {
  width: 100%;
  border-radius: 8px;
}

.fusion-btn {
  display: block;
  margin: 20px auto 0;
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}

.fusion-btn:hover {
  background-color: #0056b3;
}

.fusion-popup-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.fusion-popup {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  width: 400px;
  text-align: center;
}

.fusion-popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  margin-bottom: 15px;
}

.fusion-popup-body {
  font-size: 16px;
}
</style>
