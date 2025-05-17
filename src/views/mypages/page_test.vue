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
    <div
      ref="cesiumContainer"
      :class="['cesium-container', { 'split-left': isSplit }]"
    ></div>

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
      image1: "src/assets/test_image.png", // 修改图片路径
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
      // 初始化 Cesium 地图
      Cesium.Ion.defaultAccessToken = cesium_token;
      cesium_viewer = new Cesium.Viewer(this.$refs.cesiumContainer, {
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

      cesium_viewer.scene.frameState.creditDisplay.container.style.display =
        "none";
      cesium_viewer.imageryLayers.addImageryProvider(
        new Cesium.WebMapServiceImageryProvider({
          url: "http://127.0.0.1:13140/geoserver/satellitevisibility/",
          layers: "satellitevisibility:ZB-DEM",
          parameters: {
            service: "WMS",
            version: "1.1.1",
            request: "GetMap",
            format: "image/png",
            transparent: false,
            srs: "EPSG:4326",
          },
        })
      );
      cesium_viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(121.38277, 25.15883, 9000.0),
      });
    },

    initChart() {
      decode_CSV("src/assets/test_area.csv")
        .then((csv_data) => {
          // 成功读取文件，打印数据
          console.log("CSV 文件内容:", csv_data);
          date_list = csv_data.map((item) => item.date);
          area_list = csv_data.map((item) => item.area).map(Number);
          console.log(date_list);
          console.log(area_list);
          // 获取DOM元素
          const chartDom = this.$refs.chartContainer;
          // 初始化ECharts实例
          const myChart = echarts.init(chartDom);

          // 配置折线图选项
          const option = {
            // title: {
            //   text: "港口面积变化图",
            // },
            tooltip: {
              trigger: "axis",
              valueFormatter: function (value) {
                return value + " 平方千米";
              },
            },
            xAxis: {
              type: "category",
              name: "日期",
              // data: ["周一", "周二", "周三", "周四", "周五", "周六", "周日", "周一"],
              data: date_list,
            },
            yAxis: {
              type: "value",
              name: "平方千米",
              min: function (value) {
                return 0.95 * Math.min(...area_list);
              },
              max: function (value) {
                return 1.05 * Math.max(...area_list);
              },
              axisLabel: {
                formatter: (value, index) => {
                  // 保留3位小数
                  return value.toFixed(3);
                },
              },
            },
            series: [
              {
                name: "面积",
                type: "line",
                //data: [1,2,3,4,5,6,7,8],
                data: area_list,
                color: "red",
                smooth: true, // 平滑曲线
                showSymbol: true, //是否默认展示圆点
                symbol: "emptyCircle", //设定为空心点
                symbolSize: 10, //设定实心点的大小
              },
            ],
          };

          // 使用配置项绘制图表
          myChart.setOption(option);
        })
        .catch((error) => {
          // 处理错误
          console.error(error.message);
        });
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
  padding: 0;
  margin: 0;
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
  z-index: 1000;
  display: flex;
  flex-direction: column;

  /* 垂直排列 */
  gap: 5px;

  /* 两个日期选择框之间的间隔 */
  width: 280px;

  /* 设置面板的宽度 */
  height: 280px;
  padding: 15px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 0 10px rgb(0 0 0 / 10%);

  /* 设置面板的高度 */
}

.time-selector-box h3 {
  margin-bottom: 8px;
  font-size: 16px;
}

.time-selector-box input[type="date"] {
  padding: 5px;
  margin-right: 10px;
}

.time-selector-box button {
  padding: 5px 10px;
  color: white;
  cursor: pointer;
  background-color: #007bff;
  border: none;
  border-radius: 4px;
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
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  width: 55%;
  height: 100%;
  background: #f0f2f5;
}

/* 上部分：监测结果 */
.image-container {
  box-sizing: border-box;
  height: calc(50% - 5px);
  padding: 16px;
  overflow: hidden;
  background-color: white;
  border: 1px solid white;
  border-radius: 4px;
}

/* 下部分：监测曲线 */
.chart-container-box {
  box-sizing: border-box;
  height: calc(50% - 5px);
  padding: 16px;
  background-color: white;
  border: 1px solid white;
  border-radius: 4px;
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
  display: block;
  width: auto;
  height: 124%;
  margin-top: 5px;
  margin-right: auto;
  margin-left: auto;
}

/* 标题样式 */
.title {
  padding-bottom: 8px;
  margin: 0;
  font-size: 20px;
  font-weight: bold;
  color: #002060;
  text-align: left;
  border-bottom: 2px solid #000;
}

/* 过渡动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.1s ease;
}

.slide-enter,
.slide-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
