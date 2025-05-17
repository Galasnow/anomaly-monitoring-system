<template>
  <div>
    <button @click="startProcessing" :disabled="isProcessing">
      {{ isProcessing ? "处理中..." : "获取文件列表" }}
    </button>

    <!-- 显示文件列表 -->
    <ul v-if="Array.isArray(files) && files.length > 0">
      <li v-for="(file, index) in files" :key="index">{{ file }}</li>
    </ul>

    <!-- 显示状态信息 -->
    <p v-if="isProcessing">正在运行 main.py，请稍候...</p>
    <p v-else-if="Array.isArray(files) && files.length === 0">没有文件</p>
    <p v-else-if="errorMessage">{{ errorMessage }}</p>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      files: [], // 存储 .tif 文件列表
      isProcessing: false, // 是否正在运行 main.py
      errorMessage: "", // 错误信息
      pollingInterval: null, // 轮询定时器
    };
  },
  beforeUnmount() {
    this.stopPolling(); // 组件销毁时，停止轮询
  },
  methods: {
    // 1️⃣ 点击按钮，开始处理
    async startProcessing() {
      this.isProcessing = true;
      this.files = [];
      this.errorMessage = "";

      try {
        // 运行 main.py
        await axios.get("http://localhost:3017/api/run-main");

        // 启动轮询，等待 .tif 生成
        this.startPolling();
      } catch (error) {
        this.isProcessing = false;
        this.errorMessage = "启动 main.py 失败，请检查后端";
      }
    },

    startPolling() {
      this.pollingInterval = setInterval(async () => {
        try {
          const response = await axios.get("http://localhost:3017/api/files");

          if (response.data.files.length > 0) {
            this.files = response.data.files;
            this.stopPolling();
            this.isProcessing = false;
          }
        } catch (error) {
          console.error("获取文件列表失败:", error);
        }
      }, 10000); // 每 10 秒检查一次
    },

    // 3️⃣ 停止轮询
    stopPolling() {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval);
        this.pollingInterval = null;
      }
    },
  },
};
</script>

<style scoped>
button {
  padding: 10px 20px;
  font-size: 16px;
  color: white;
  cursor: pointer;
  background-color: #4caf50;
  border: none;
  border-radius: 5px;
}

button:disabled {
  cursor: not-allowed;
  background-color: gray;
}

ul {
  padding: 0;
  list-style-type: none;
}

li {
  padding: 5px 0;
}
</style>
