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
        <el-form>
          <el-form-item label="彩色画面">
            <div class="upload-wrapper">
              <single-upload v-model="Image1" />
            </div>
          </el-form-item>
        </el-form>

        <el-form>
          <el-form-item label="红外画面">
            <div class="upload-wrapper">
              <single-upload v-model="Image2" />
            </div>
          </el-form-item>
        </el-form>

        <!-- 执行融合按钮 -->
        <el-button
          type="primary"
          :disabled="isProcessing"
          @click="handleFusionProcess"
        >
          {{ isProcessing ? "正在融合中..." : "执行融合" }}
        </el-button>

        <!-- 保存结果按钮 -->
        <el-button
          v-if="resultImageUrl"
          type="success"
          @click="saveFusionResult"
          class="save-button"
        >
          保存结果
        </el-button>

        <div v-if="resultImageUrl" class="result-wrapper">
          <img :src="resultImageUrl" alt="融合结果" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import SingleUpload from "@/components/Upload/SingleUpload.vue";
import { FusionRequest, FusionType } from "@/api/lzjt/menu1/fusion/model";
import FusionAPI from "@/api/lzjt/menu1/fusion";

// 保存上传的图像
const Image1 = ref({ name: "", url: "" });
const Image2 = ref({ name: "", url: "" });
const resultImageUrl = ref(""); // 保存处理后的图片URL
const isProcessing = ref(false); // 控制处理状态

// 保存融合结果到本地
const saveFusionResult = async () => {
  if (!resultImageUrl.value) {
    ElMessage.error("未找到可保存的结果，请重新尝试!");
    return;
  }

  try {
    // 使用 fetch 获取文件数据
    const response = await fetch(resultImageUrl.value);
    if (!response.ok) {
      throw new Error("无法下载文件");
    }

    // 将响应数据转为 Blob
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);

    // 创建 <a> 元素用于下载
    const link = document.createElement("a");
    link.href = url;
    link.download = "融合结果.jpg"; // 下载文件的默认名称
    document.body.appendChild(link);
    link.click();

    // 清理临时 URL 和 DOM
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    ElMessage.success("结果已保存！");
  } catch (error) {
    console.error(error);
    ElMessage.error("保存结果失败，请重试！");
  }
};

// 处理融合过程
const handleFusionProcess = async () => {
  if (isProcessing.value) return;

  if (!Image1.value.url || !Image2.value.url) {
    ElMessage.error("请上传两张影像后再执行融合操作!");
    return;
  }

  const requestData: FusionRequest = {
    Image1_name: Image1.value.name,
    Image2_name: Image2.value.name,
    type: FusionType.Fusion_IR_IMG,
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
    type: Array as () => string[],
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
  font-size: 24px;
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #ff4d4f;
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
  background-color: rgba(0, 0, 0, 0.5); /* 半透明背景 */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.fusion-popup {
  background: #ffffff; /* 弹窗背景为纯白 */
  padding: 20px;
  border-radius: 12px; /* 圆角更柔和 */
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* 更明显的阴影 */
  width: 400px;
  max-width: 90%; /* 自适应小屏幕 */
  max-height: 90%;
  text-align: center;
  animation: fadeIn 0.3s ease-in-out; /* 添加淡入效果 */
  overflow-x: hidden;
  overflow-y: auto;
}

.fusion-popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  margin-bottom: 20px; /* 标题与内容间距 */
  font-weight: bold;
  color: #333;
}

.fusion-popup-body {
  font-size: 16px;
  display: flex;
  flex-direction: column;
  gap: 1px; /* 子元素间的间距 */
  align-items: center;
}

.upload-wrapper {
  width: 200px; /* 可根据需要调整大小 */
  height: 200px;
  margin: 0 auto; /* 居中 */
  background-color: #f9f9f9; /* 浅灰色背景 */
  border: 1px dashed #ccc; /* 虚线边框 */
  border-radius: 8px;
  text-align: center;
}

.el-button {
  width: 100%;
  max-width: 200px; /* 限制按钮宽度 */
  margin-top: 10px;
}

.result-wrapper {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f5f5; /* 浅背景突出结果区 */
  border: 1px solid #ddd; /* 边框颜色柔和 */
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.result-wrapper img {
  max-width: 100%;
  max-height: 300px;
  margin-top: 10px;
  border-radius: 8px;
  border: 1px solid #ccc; /* 图片边框 */
}

.save-button {
  margin-top: 10px;
  width: 150px;
}
.save-button {
  margin-top: 10px;
  width: 100%;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
