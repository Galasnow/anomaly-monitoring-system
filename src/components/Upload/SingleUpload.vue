<template>
  <!-- 上传组件 -->
  <el-upload
    v-model="fileInfo"
    class="single-uploader"
    :show-file-list="false"
    list-type="picture-card"
    :before-upload="handleBeforeUpload"
    :http-request="uploadFile"
    drag
    @drop="handleDrop"
  >
    <div class="upload-content">
      <div v-if="fileInfo.url">
        <img
          :src="fileInfo.url"
          class="single-uploader__image"
          alt="fileInfo.name"
        />
      </div>
      <div v-else>
        <!-- 使用自定义的 svg 图标 -->
        <svg-icon
          v-if="!fileInfo.url"
          class="single-uploader__icon"
          icon-class="upload"
        />
        <div class="divider"></div>
        <div class="upload-text">将文件拖到此处，或点击上传</div>
      </div>
    </div>
  </el-upload>
</template>

<script setup lang="ts">
import { UploadRawFile } from "element-plus";
import FileAPI from "@/api/file";

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ name: "", url: "" }),
  },
});

const emit = defineEmits(["update:modelValue"]);
const fileInfo = useVModel(props, "modelValue", emit);

/**
 * 自定义图片上传
 *
 * @param options
 */
async function uploadFile(options: any) {
  try {
    const file = options.file as File; // 直接从 options 中获取文件
    const data = await FileAPI.upload(file); // 调用 FileAPI.upload 直接上传文件
    fileInfo.value = { name: data.name, url: data.url }; // 上传成功后, 设置 imgUrl
  } catch (error) {
    console.error("上传失败", error);
  }
}

/**
 * 限制用户上传文件的格式和大小
 */
function handleBeforeUpload(file: UploadRawFile) {
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning("警告:上传的图片大于2M,可能会导致处理速度变慢!");
    return true;
  }
  return true;
}

/**
 * 处理拖拽文件上传的事件
 */
function handleDrop(event: DragEvent) {
  const files = event.dataTransfer?.files as FileList;
  if (files && files.length > 0) {
    const file = files[0]; // 获取拖拽的第一个文件

    // 手动为 File 添加 uid 属性，以符合 UploadRawFile 的要求
    const uploadFile0: UploadRawFile = {
      ...file,
      uid: Date.now(), // 生成唯一的 number 类型 uid
    };

    // 进行文件类型和大小的验证
    if (!handleBeforeUpload(uploadFile0)) {
      return;
    }

    // 调用上传文件的函数
    uploadFile({ file: uploadFile0 });
  }
}
</script>

<style scoped lang="scss">
/* 覆盖默认的 el-upload 样式，使其适应外部容器 */
.single-uploader {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border: 1px var(--el-border-color) solid;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  width: 100%; /* 使 el-upload 占满父容器的宽度 */
  height: 100%; /* 使 el-upload 占满父容器的高度 */
}

::v-deep(.el-upload--picture-card) {
  width: 100% !important;
  height: 100% !important;
}

::v-deep(.el-upload-dragger) {
  height: 100%;
  width: 100%;
}

.upload-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.single-uploader__image {
  display: block;
  max-width: 100%;
  max-height: 100%; /* 图片自适应容器 */
}

.single-uploader__icon {
  font-size: 28px;
  color: #8c939d;
  text-align: center;
  margin-bottom: 8px;
}

.divider {
  width: 100%;
  border-top: 1px dashed var(--el-border-color);
  margin: 8px 0;
}

.upload-text {
  font-size: 14px;
  color: #8c939d;
  text-align: center;
}
</style>
