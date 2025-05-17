<template>
  <div class="dashboard">
    <!-- 顶部标题栏 -->
    <header class="header">
      <span class="logo">LOGO-系统名称</span>
      <span>{{ currentDate }}</span>
    </header>

    <!-- 左侧地图和相关信息 -->
    <div class="left-panel">
      <div class="map-container">
        <!-- 地图容器，可以使用 Vue-Cesium、Leaflet 或者其他地图库 -->
        <div id="map"></div>
      </div>
      <div class="info-panel">
        <el-row>
          <el-col :span="24">
            <el-card class="chart-card">
              <!-- 折线图容器 -->
              <div id="line-chart"></div>
            </el-card>
          </el-col>
          <el-col :span="24">
            <el-card class="chart-card">
              <!-- 饼图容器 -->
              <div id="pie-chart"></div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 中间的地图大容器 -->
    <div class="center-panel">
      <!-- 主地图容器 -->
      <div id="main-map"></div>
    </div>

    <!-- 右侧统计信息 -->
    <div class="left-panel">
      <div class="map-container">
        <!-- 地图容器，可以使用 Vue-Cesium、Leaflet 或者其他地图库 -->
        <!-- 柱状图 -->
        <div id="bar-chart"></div>
      </div>
      <div class="info-panel">
        <el-card class="chart-card">
          <!-- 饼图容器 -->
          <div class="circular-progress-container">
            <div class="circular-progress">
              <div class="progress-text">
                <span>6.66%</span>
                <p>今日流量</p>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref } from "vue";
import * as echarts from "echarts";

// 更新系统时间
function updateCurrentDate() {
  const now = new Date();
  currentDate.value = now.toLocaleString(); // 根据需要更改格式
}

// 防抖函数
function debounce(fn: Function, delay: number) {
  let timeout: ReturnType<typeof setTimeout>; // 显式定义timeout类型
  return function (this: any, ...args: any[]) {
    // 显式定义this和参数类型
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      fn.apply(this, args); // 保持this和传入的参数
    }, delay);
  };
}

// 节流函数
function throttle(fn: Function, limit: number) {
  let lastCall = 0;
  return function (this: any, ...args: any[]) {
    // 显式定义this和参数类型
    const now = new Date().getTime();
    if (now - lastCall >= limit) {
      lastCall = now;
      fn.apply(this, args);
    }
  };
}

// 使用防抖/节流动态调整Echarts
function resizeHandler(
  type: "debounce" | "throttle" = "throttle",
  delayOrLimit: number = 100
) {
  if (type === "debounce") {
    return debounce(function () {
      lineChart?.resize(); // 使用可选链操作符 ?. 确保 chart 对象不为 null 才执行方法
      pieChart?.resize();
      barChart?.resize();
    }, delayOrLimit);
  } else if (type === "throttle") {
    return throttle(function () {
      lineChart?.resize();
      pieChart?.resize();
      barChart?.resize();
    }, delayOrLimit);
  }

  // 增加一个默认返回的函数，防止返回 undefined
  return function () {
    lineChart?.resize();
    pieChart?.resize();
    barChart?.resize();
  };
}

const currentDate = ref(new Date().toLocaleString());
let resizeFn: () => void;
// 初始化 ECharts 图表
let lineChart: echarts.ECharts | null = null;
let pieChart: echarts.ECharts | null = null;
let barChart: echarts.ECharts | null = null;

onMounted(() => {
  updateCurrentDate();
  const intervalId = setInterval(updateCurrentDate, 1000); // 每秒更新
  onUnmounted(() => clearInterval(intervalId)); // 组件销毁时清除定时器

  const lineChartDom = document.getElementById("line-chart");
  const pieChartDom = document.getElementById("pie-chart");
  const barChartDom = document.getElementById("bar-chart");

  // 折线图配置
  const lineOption = {
    title: {
      text: "折线图",
    },
    xAxis: {
      type: "category",
      data: ["1", "2", "3", "4", "5", "6", "7"],
    },
    yAxis: {
      type: "value",
    },
    series: [
      {
        data: [820, 932, 901, 934, 1290, 1330, 1320],
        type: "line",
      },
    ],
  };

  // 饼图配置
  const pieOption = {
    title: {
      text: "饼图",
      left: "center",
    },
    series: [
      {
        name: "访问来源",
        type: "pie",
        radius: "50%",
        data: [
          { value: 1048, name: "直接访问" },
          { value: 735, name: "邮件营销" },
          { value: 580, name: "联盟广告" },
          { value: 484, name: "视频广告" },
          { value: 300, name: "搜索引擎" },
        ],
      },
    ],
  };

  // 柱状图配置
  const barOption = {
    title: {
      text: "柱状图",
    },
    xAxis: {
      type: "category",
      data: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
    },
    yAxis: {
      type: "value",
    },
    series: [
      {
        data: [120, 200, 150, 80, 70, 110, 130],
        type: "bar",
      },
    ],
  };

  if (lineChartDom) {
    lineChart = echarts.init(lineChartDom, null, {
      width: 190, // 设置宽度
      height: 190, // 设置高度
    });
    lineChart.setOption(lineOption);
  } else {
    console.error("line-chart DOM 元素未找到");
  }

  if (pieChartDom) {
    pieChart = echarts.init(pieChartDom);
    pieChart.setOption(pieOption);
  } else {
    console.error("pie-chart DOM 元素未找到");
  }

  if (barChartDom) {
    barChart = echarts.init(barChartDom, null, {
      width: 190, // 设置宽度
      height: 190, // 设置高度
    });
    barChart.setOption(barOption);
  } else {
    console.error("bar-chart DOM 元素未找到");
  }

  // 使用 resize 事件监听器
  resizeFn = resizeHandler("throttle", 100);
  window.addEventListener("resize", resizeFn); // 选择防抖
  // 或者
  // window.addEventListener('resize', resizeHandler('throttle', 100)); // 选择节流
});

// 组件销毁时清理事件监听
onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeFn);
});
</script>

<style scoped>
.dashboard {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  grid-template-rows: auto 1fr;
  height: calc(100vh - 84px);
  gap: 10px;
}

.header {
  grid-column: 1 / 4;
  display: flex;
  justify-content: space-between;
  align-items: center; /* 垂直居中 */
  padding: 10px;
  background-color: #123456;
  color: white;
}

.logo {
  flex: 1; /* 让 logo 占据剩余空间 */
  text-align: center; /* 居中对齐 */
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.map-container {
  height: 100%;
  background-color: #333;
}

.info-panel {
  gap: 10px;
}

.center-panel {
  background-color: #333;
  height: 100%;
}

#main-map {
  width: 100%;
  height: 100%;
}

.right-panel {
  display: flex;
  gap: 10px;
}

.stat-card {
  width: 100%;
  padding: 10px;
}

.circular-progress {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: conic-gradient(#4caf50 66.6%, #ccc 66.6%);
  margin: 0 auto;
  position: relative;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: white;
}

#bar-chart,
#line-chart,
#pie-chart {
  height: 190px; /* 增加图表高度 */
  width: 100%;
}
</style>
