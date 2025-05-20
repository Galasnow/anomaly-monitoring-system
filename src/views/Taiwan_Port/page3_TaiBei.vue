<template>
  <div class="container">
    <!-- 左上角的截止时间选择框 -->
    <div class="time-selector-box">
      <h2 class="title">台北港异常扩建动态监测</h2>
      <h3>开始日期</h3>
      <input type="date" v-model="selectedDate" @change="onDateChange" />
      <h3>截止日期</h3>
      <input type="date" v-model="secondDate" @change="onSecondDateChange" />
      <button @click="analyzeData">分析</button>
    </div>

    <!-- Cesium 3D地球容器 -->
    <div ref="cesiumContainer" :class="['cesium-container', { 'split-left': isSplit }]"></div>

    <!-- 右侧内容容器 -->
    <transition name="slide">
      <div v-if="isSplit" class="right-panel">
        <!-- 上部分：监测结果 -->
        <div class="image-container">
          <h2 class="title">台北港异常扩建动态监测结果</h2>
          <img :src="image1" alt="监测结果" class="responsive-image" />
        </div>
        <!-- 下部分：监测曲线 和 ECharts 图表 -->
        <div class="chart-container-box">
          <h2 class="title">台北港异常扩建动态监测曲线</h2>
          <div ref="chartContainer" class="chart-container"></div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { Viewer } from "cesium";
import * as Cesium from "cesium";
import * as echarts from "echarts";
import "cesium/Build/Cesium/Widgets/widgets.css";
import { cesium_token } from "../../../my_package.json";
import * as d3 from "d3";

var date_list = [];
var area_list = [];
let cesium_viewer = null;
// 解析 CSV 文件
function decode_CSV(csv_path) {
  return new Promise((resolve, reject) => {
    d3.csv(csv_path)
      .then((data) => {
        resolve(data);
      })
      .catch((error) => {
        reject(new Error(`读取 CSV 文件时出错: ${error.message}`));
      });
  });
}

export default {
  data() {
    return {
      isSplit: false,
      image1: "src/assets/Taibei_Port_Result.png", // 修改图片路径
      viewer: null,
      chartInstance: null,
    };
  },
  mounted() {
    this.initCesium();
    window.addEventListener("resize", this.handleResize);
  },
  beforeUnmount() {
    if (this.viewer && !this.viewer.isDestroyed()) {
      this.viewer.destroy();
    }
    if (this.chartInstance) {
      this.chartInstance.dispose();
    }
    window.removeEventListener("resize", this.handleResize);
  },
  methods: {
    initCesium() {
      // 初始化Cesium Viewer
      Cesium.Ion.defaultAccessToken = cesium_token;
      this.viewer = new Viewer(this.$refs.cesiumContainer, {
        animation: false,
        baseLayerPicker: false,
        fullscreenButton: false,
        geocoder: false,
        homeButton: false,
        infoBox: false,
        sceneModePicker: false,
        selectionIndicator: false,
        shouldAnimate: false,
        showRenderLoopErrors: false,
        timeline: false,
        navigationHelpButton: false,
        navigationInstructionsInitiallyVisible: false,
      });
      // 隐藏logo信息
      this.viewer._cesiumWidget._creditContainer.style.display = "none";
      // 设置初始视角
      this.viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(121.38277, 25.15883, 9000.0),
      });
    },

    initChart() {
      decode_CSV("src/assets/Taibei_Port_Area.csv")
        .then(csv_data => {
          // 提取日期、面积（保留4位小数）和abnormal值
          const date_list = csv_data.map(item => item.date);
          const area_list = csv_data.map(item => parseFloat(item.area).toFixed(4)); // 保留4位小数
          const abnormal_list = csv_data.map(item => parseInt(item.abnormal, 10) || 0);

          console.log("date_list:", date_list);
          console.log("area_list:", area_list);
          console.log("abnormal_list:", abnormal_list);

          const chartDom = this.$refs.chartContainer;
          if (!chartDom) {
            console.error("ECharts 容器未正确初始化！");
            return;
          }

          const myChart = echarts.init(chartDom);
          myChart.clear(); // 清除缓存，避免图表不刷新

          const option = {
            tooltip: {
              trigger: "axis",
              valueFormatter: function (value) {
                return value + " km²";
              },
            },
            xAxis: {
              type: "time",  // 将 xAxis 类型改为 "time"
              name: '日期',
              nameTextStyle: { fontSize: 18 },
              axisLabel: {
                fontSize: 18,
              },
            },
            yAxis: {
              type: "value",
              name: '面积 (km²)',
              nameTextStyle: { fontSize: 18 },
              min: Math.min(...area_list) * 0.95,
              max: Math.max(...area_list) * 1.05,
              axisLabel: {
                formatter: (value) => value.toFixed(1),
                fontSize: 18,
              },
            },
            series: [
              {
                name: "面积",
                type: "line",
                data: date_list.map((date, index) => [new Date(date).getTime(), area_list[index]]), // 将日期转换为时间戳
                color: '#FAFA33',
                smooth: true,
                showSymbol: true,  // 显示所有数据点
                symbol: 'circle',  // 圆圈符号
                symbolSize: (value, params) => (abnormal_list[params.dataIndex] === 1 ? 15 : 0),  // abnormal=1 显示大圆圈
                lineStyle: {
                  color: 'red',  // 自定义线条颜色为红色
                  width: 3,       // 自定义线条宽度
                },
                itemStyle: {
                  color: (params) => abnormal_list[params.dataIndex] === 1 ? '#FAFA33' : 'transparent', // abnormal=1 时填充黄色
                  borderColor: 'black',  // 圆圈的边框颜色
                  borderWidth: 1.5,        // 圆圈边框宽度
                },
              },
            ],
          };


          myChart.setOption(option);
        })
        .catch(error => console.error("CSV 解析错误: ", error));
    },

    analyzeData() {
      this.isSplit = !this.isSplit;
      this.$nextTick(() => {
        this.adjustLayout();
        if (this.isSplit && !this.chartInstance) {
          this.initChart();
        }
      });
    },

    toggleSplit() {
      this.isSplit = !this.isSplit;
      this.$nextTick(() => {
        this.adjustLayout();
        if (this.isSplit && !this.chartInstance) {
          this.initChart();
        }
      });
    },

    adjustLayout() {
      // 调整Cesium和图表尺寸
      if (this.viewer && !this.viewer.isDestroyed()) {
        this.viewer.resize();
      }
      if (this.chartInstance) {
        this.chartInstance.resize();
      }
    },

    handleResize() {
      this.adjustLayout();
    },
  },
};
</script>

<style scoped>
/* 确保全屏布局 */
html,
body,
#app {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

/* 页面主容器 */
.container {
  display: flex;
  width: 100%;
  height: 91vh;
}

/* 左上角控制面板 */
.time-selector-box {
  position: absolute;
  top: 10px;
  left: 10px;
  background-color: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  /* 垂直排列 */
  gap: 5px;
  /* 两个日期选择框之间的间隔 */
  width: 280px;
  /* 设置面板的宽度 */
  height: 280px;
  /* 设置面板的高度 */
}

.time-selector-box h3 {
  font-size: 16px;
  margin-bottom: 8px;
}

.time-selector-box input[type="date"] {
  padding: 5px;
  margin-right: 10px;
}

.time-selector-box button {
  padding: 5px 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.time-selector-box button:hover {
  background-color: #0056b3;
}

/* Cesium容器样式 */
.cesium-container {
  /* position: absolute;
  top: 0;
  left: 0; */
  width: 100%;
  height: 100%;
  /* transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1); */
}

.cesium-container.split-left {
  width: 45%;
}

/* 右侧面板 */
.right-panel {
  width: 55%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  box-sizing: border-box;
}


/* 上部分：监测结果 */
.image-container {
  height: calc(50% - 5px);
  background-color: white;
  border: 1px solid white;
  border-radius: 4px;
  padding: 16px;
  box-sizing: border-box;
  overflow: hidden;
}

/* 下部分：监测曲线 */
.chart-container-box {
  height: calc(50% - 5px);
  background-color: white;
  border: 1px solid white;
  border-radius: 4px;
  padding: 16px;
  box-sizing: border-box;
}

/* ECharts 图表样式 */
.chart-container {
  width: 100%;
  height: 100%;
}

/* .image-container {
  height: 50%;
  padding: 15px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-container {
  flex: 1;
  padding: 15px;
  /* min-height: 300px;
} */

.responsive-image {
  width: auto;
  height: 91%;
  margin-top: 5px;
  display: block;
  margin-left: auto;
  margin-right: auto;
}

/* 标题样式 */
.title {
  margin: 0;
  font-size: 20px;
  font-weight: bold;
  color: #002060;
  text-align: left;
  padding-bottom: 8px;
  border-bottom: 2px solid #000000;
}

/* 过渡动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.5s ease;
}

.slide-enter,
.slide-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
