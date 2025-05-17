<template>
  <!-- 上传组件 -->
  <el-upload
    v-model="fileInfo"
    class="single-uploader"
    :show-file-list="false"
    list-type="picture-card"
    :before-upload="handleBeforeUpload"
    :http-request="uploadFile"
  >
    <img
      v-if="fileInfo.url"
      :src="fileInfo.url"
      class="single-uploader__image"
    />
    <el-icon v-else class="single-uploader__icon"><i-ep-plus /></el-icon>
  </el-upload>
</template>

<script setup lang="ts">
import { UploadRawFile, UploadRequestOptions } from "element-plus";
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
async function uploadFile(options: UploadRequestOptions): Promise<any> {
  const data = await FileAPI.upload(options.file);
  fileInfo.value = { name: data.name, url: data.url };
}

/**
 * 限制用户上传文件的格式和大小
 */
function handleBeforeUpload(file: UploadRawFile) {
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning("上传的图片大于2M!");
    return true;
  }
  return true;
}
</script>

<style scoped lang="scss">
.single-uploader {
  overflow: hidden;
  cursor: pointer;
  border: 1px var(--el-border-color) solid;
  border-radius: 6px;

  &:hover {
    border-color: var(--el-color-primary);
  }

  &__image {
    display: block;
    width: 178px;
    height: 178px;
  }

  &___icon {
    width: 178px;
    height: 178px;
    font-size: 28px;
    color: #8c939d;
    text-align: center;
  }
}
</style>
