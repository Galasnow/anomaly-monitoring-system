<template>
  <div class="container">
    <!-- 文件上传部分 -->
    <div class="upload-section">
      <h2>文件上传</h2>
      <p class="upload-instructions">
        服务器中已含有21年的原始数据，可以直接点击SAVEE评价获得当年的结果。<br />
        如想更新获得其他年份或地区的评价结果，请更新数据：<br />
        <strong
          >01.tif（中国敏感）、02.tif（印度敏感）、03.tif（中国地灾）、04.tif（印度地灾）、05.tif（突发事件）</strong
        ><br />
        命名必须按上述格式（括号内内容仅为提示，不包含在命名中）。
      </p>
      <input type="file" multiple @change="handleFiles" class="file-input" />
      <button
        @click="uploadFiles"
        class="upload-button"
        :disabled="isUploading"
      >
        上传文件
      </button>
      <div v-if="uploadSuccess" class="success-message">
        <h3>文件上传成功！</h3>
        <ul class="file-list">
          <li
            v-for="(file, index) in uploadedFileNames"
            :key="index"
            class="file-item"
          >
            {{ file }}
          </li>
        </ul>
      </div>
    </div>

    <hr class="divider" />

    <!-- SAVEE 评价部分 -->
    <div class="savee-section">
      <h2>SAVEE 评价</h2>
      <div class="savee-control">
        <button
          @click="startSAVEEAssessment"
          class="savee-button"
          :disabled="isAssessing"
        >
          开始SAVEE评价
        </button>
        <span v-if="isAssessing" class="loading-message">
          评价进行中，请耐心等待
        </span>
      </div>

      <!-- 显示评价结果 -->
      <div v-if="thumbnailSrc" class="result">
        <button @click="saveResultFile" class="save-button">
          保存结果文件到本地
        </button>
        <h3>评价结果TIFF文件已经成功生成，以下为其略缩图展示。</h3>
        <img :src="thumbnailSrc" alt="SAVEE Result" class="result-image" />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      selectedFiles: [],
      uploadSuccess: false,
      uploadedFileNames: [],
      thumbnailSrc: null,
      isUploading: false,
      isAssessing: false,
      tiffBlob: null, // 保存 SAVEE 评价结果文件的二进制数据
      thumbnailBlob: null, // 保存略缩图的二进制数据
    };
  },
  methods: {
    handleFiles(event) {
      this.selectedFiles = Array.from(event.target.files);
    },
    async uploadFiles() {
      if (this.selectedFiles.length === 0) {
        alert("请选择要上传的文件！");
        return;
      }

      this.isUploading = true;

      const formData = new FormData();
      this.selectedFiles.forEach((file) => {
        formData.append("files", file, file.name);
      });

      try {
        // http://47.108.151.251:8989
        const response = await fetch(
          "http://127.0.0.1:8989/api/v1/SAVEE_files",
          {
            method: "POST",
            body: formData,
          }
        );

        if (!response.ok) {
          throw new Error("网络响应不是ok");
        }

        const data = await response.json();
        if (data.code === "00000") {
          this.uploadSuccess = true;
          this.uploadedFileNames = data.data.map((file) => file.name);
        } else {
          alert("文件上传失败：" + data.msg);
        }
      } catch (error) {
        console.error("上传文件时出错:", error);
        alert("上传文件时出错: " + error.message);
      } finally {
        this.isUploading = false;
      }
    },
    async startSAVEEAssessment() {
      try {
        this.isAssessing = true;

        // 获取 SAVEE 评价结果和缩略图数据
        const response = await fetch("http://127.0.0.1:8989/api/v1/SAVEE", {
          method: "POST",
        });

        if (!response.ok) {
          throw new Error("请求失败");
        }

        const data = await response.json();

        // 确认 TIFF 文件和缩略图数据是否有效
        if (!data.tiff_data || !data.thumbnail_data) {
          throw new Error("返回的数据不完整");
        }

        // 保存 TIFF 文件的二进制数据
        this.tiffBlob = new Blob([new Uint8Array(data.tiff_data)], {
          type: "application/octet-stream",
        });

        // 检查 TIFF 数据的大小
        if (this.tiffBlob.size === 0) {
          throw new Error("返回的 TIFF 文件为空！");
        }

        // 保存缩略图的二进制数据
        this.thumbnailBlob = new Blob([new Uint8Array(data.thumbnail_data)], {
          type: "image/jpeg",
        });
        this.thumbnailSrc = URL.createObjectURL(this.thumbnailBlob);

        alert("SAVEE 评价完成！请点击保存按钮保存文件到本地。");
      } catch (error) {
        console.error("请求失败:", error);
        alert("请求失败: " + error.message);
      } finally {
        this.isAssessing = false;
      }
    },

    // 新增保存文件到本地的方法
    saveResultFile() {
      if (this.tiffBlob) {
        // 创建一个临时的 <a> 标签
        const link = document.createElement("a");
        link.href = URL.createObjectURL(this.tiffBlob);
        link.download = "SAVEE_Result.tif"; // 文件名

        // 触发点击事件，下载文件
        link.click();

        // 释放 URL 对象
        URL.revokeObjectURL(link.href);
      } else {
        alert("没有可保存的文件！");
      }
    },
  },
};
</script>

<style scoped>
.container {
  max-width: 800px;
  margin: 0 auto;
  font-family: Arial, sans-serif;
  color: #333;
}

h2 {
  color: #0056b3;
  text-align: center;
}

.upload-section,
.savee-section {
  margin-bottom: 20px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.upload-instructions {
  background-color: #e9f5ff;
  border-left: 4px solid #007bff;
  padding: 10px 15px;
  margin-bottom: 15px;
  font-size: 14px;
  color: #0056b3;
  line-height: 1.6;
}

.file-input {
  display: block;
  margin: 10px 0;
}

.upload-button,
.savee-button,
.save-button {
  display: block;
  background-color: #007bff;
  color: #fff;
  padding: 10px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  text-align: center;
  font-size: 16px;
  margin: 10px auto;
}

.save-button {
  background-color: #ff8c00;
}

.save-button:hover {
  background-color: #e67e00;
}

.upload-button[disabled],
.savee-button[disabled],
.save-button[disabled] {
  background-color: #cccccc;
  cursor: not-allowed;
}

.upload-button:hover:not([disabled]),
.savee-button:hover:not([disabled]) {
  background-color: #0056b3;
}

.loading-message {
  margin-left: 10px;
  font-size: 14px;
  color: #ff6f00;
}

.success-message {
  margin-top: 10px;
  color: #28a745;
  font-weight: bold;
}

.file-list {
  list-style-type: none;
  padding: 0;
}

.file-item {
  margin: 5px 0;
}

.divider {
  margin: 30px 0;
  border: 0;
  height: 1px;
  background: #ddd;
}

.result {
  text-align: center;
  margin-top: 20px;
}

.result-image {
  max-width: 100%;
  border: 1px solid #ddd;
  border-radius: 8px;
}
</style>
