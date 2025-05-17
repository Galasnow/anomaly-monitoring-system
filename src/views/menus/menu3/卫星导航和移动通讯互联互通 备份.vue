<template>
  <div class="app-container">
    <el-form>
      <el-form-item label="DEM影像">
        <!-- 外部容器控制上传组件的大小 -->
        <div class="upload-wrapper">
          <single-upload v-model="Image1" />
        </div>
      </el-form-item>
    </el-form>

    <!-- 提交按钮 -->
    <el-button
      type="primary"
      :disabled="isProcessing"
      @click="handleFusionProcess"
    >
      {{ isProcessing ? "正在进行卫星可见性评价中..." : "开始评价" }}
    </el-button>

    <!-- 处理后的图片显示框 -->
    <div v-if="resultImageUrl" class="result-wrapper">
      <img :src="resultImageUrl" alt="卫星可见性评价结果" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import SingleUpload from "@/components/Upload/SingleUpload.vue";
import { FusionRequest, FusionType } from "@/api/lzjt/menu1/fusion/model";
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

  if (!Image1.value.url) {
    ElMessage.error("请上传影像后再执行操作!");
    return;
  }

  const requestData: FusionRequest = {
    Image1_name: Image1.value.name,
    Image2_name: Image2.value.name,
    type: FusionType.Satellite_Visibility,
  };

  try {
    // 显示加载状态
    isProcessing.value = true;

    // 发送请求到后端
    const response = await FusionAPI.startFusion(requestData);
    // 请求成功，返回处理后的图片URL
    resultImageUrl.value = response.url;
    ElMessage.success("评价完成!");
  } catch (error) {
    ElMessage.error("评价失败，请重试!");
    console.error(error);
  } finally {
    // 取消加载状态
    isProcessing.value = false;
  }
};
</script>

<style scoped lang="scss">
.upload-wrapper {
  width: 200px; /* 可根据需要调整大小 */
  height: 200px;
}
.result-wrapper {
  margin-top: 20px;
  border: 1px solid #dcdcdc;
  padding: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.result-wrapper img {
  max-width: 100%;
  max-height: 400px;
  margin-top: 10px;
}
</style>
