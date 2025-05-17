<!-- 读取csv界面 -->
<template>
  <div class="container">
    <div class="top-panel">
      <!-- 左上角的截止时间选择框 -->
      <div class="time-selector-box">
        <h2 class="title">高雄港异常扩建动态监测</h2>
        <h3>开始日期</h3>
        <input type="date" v-model="selectedDate" @change="onDateChange" />
        <h3>截止日期</h3>
        <input type="date" v-model="secondDate" @change="onSecondDateChange" />
        <button @click="analyzeData">分析</button>
      </div>

      <!-- 选择影像文件的独立窗体 -->
      <div class="image-selector-box" v-if="isImageSelectorVisible">
        <h2 class="title">港口提取结果</h2>
        <select v-model="selectedTiff" @change="loadSelectedTiff">
          <option
            v-for="file in tifFiles"
            :key="file.fullName"
            :value="file.fullName"
          >
            {{ file.shortName }}
          </option>
        </select>
      </div>
    </div>

    <!-- Cesium 3D地球容器 -->
    <div
      ref="cesiumContainer"
      :class="['cesium-container', { 'split-left': isSplit }]"
    ></div>

    <!-- 右侧内容容器 -->
    <transition name="slide">
      <div v-if="isSplit" class="right-panel">
        <div class="image-container">
          <h2 class="title">高雄港异常扩建动态监测结果</h2>
          <img :src="image1" alt="监测结果" class="responsive-image" />
        </div>
        <div class="chart-container-box">
          <h2 class="title">高雄港异常扩建动态监测曲线</h2>
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
import axios from "axios"; // 导入 axios
import * as d3 from "d3";
import * as GeoTIFF from "geotiff";
import proj4 from "proj4"; // 导入 proj4 用于坐标转换

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
      image1: "src/assets/Gaoxiong_Port_Result.png", // 修改图片路径
      viewer: null,
      chartInstance: null,
      tifFiles: [], // 存储 .tif 文件名
      selectedTiff: null, // 选择的 .tif 文件
      isImageSelectorVisible: false, // 控制“港口提取结果”窗体的显示与隐藏
    };
  },
  mounted() {
    this.initCesium();
    this.fetchTiffFiles(); // 加载.tif文件名列表
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
    async initCesium() {
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
        destination: Cesium.Cartesian3.fromDegrees(120.305, 22.534, 6800.0),
      });
    },

    async fetchTiffFiles() {
      try {
        const response = await axios.get("http://localhost:3017/api/files");
        console.log("返回的数据:", response.data); // 确认返回的数据格式

        // 保存完整文件名和前8位文件名的映射
        this.tifFiles = response.data.files.map((file) => ({
          fullName: file, // 完整的文件名
          shortName: file.substring(0, 8), // 文件名的前8位
        }));
      } catch (error) {
        console.error("获取文件列表时出错:", error);
      }
    },

    // 根据选择的文件名加载 TIFF 文件
    async loadSelectedTiff() {
      if (this.selectedTiff) {
        const tiffUrl = `public/${this.selectedTiff}`; // 根据选择的完整文件名拼接 URL
        await this.loadTiffImage(tiffUrl);
      }
    },

    async loadTiffImage(tiffUrl) {
      try {
        const response = await fetch(tiffUrl);
        const arrayBuffer = await response.arrayBuffer();
        const tiff = await GeoTIFF.fromArrayBuffer(arrayBuffer);

        const image = await tiff.getImage();
        const width = image.getWidth();
        const height = image.getHeight();
        const rasters = await image.readRasters();

        console.log("Image width:", width, "height:", height);
        console.log("Rasters data:", rasters);

        const bbox = image.getBoundingBox();
        console.log("Bounding box (UTM):", bbox);

        if (!bbox || bbox.length !== 4) {
          throw new Error("Invalid bounding box retrieved from TIFF image.");
        }

        const utmProjection = "EPSG:32650";
        const wgs84Projection = "EPSG:4326";

        const lowerLeft = proj4(utmProjection, wgs84Projection, [
          bbox[0],
          bbox[1],
        ]);
        const upperRight = proj4(utmProjection, wgs84Projection, [
          bbox[2],
          bbox[3],
        ]);

        const minLon = lowerLeft[0];
        const minLat = lowerLeft[1];
        const maxLon = upperRight[0];
        const maxLat = upperRight[1];

        console.log("Converted Bounding box (WGS84):", [
          minLon,
          minLat,
          maxLon,
          maxLat,
        ]);

        // 确保影像是三波段的
        if (rasters.length < 3) {
          throw new Error("This TIFF image doesn't have 3 bands.");
        }

        const redBand = rasters[0]; // 第一个波段（红色）
        const greenBand = rasters[1]; // 第二个波段（绿色）
        const blueBand = rasters[2]; // 第三个波段（蓝色）

        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        canvas.width = width;
        canvas.height = height;

        const imageData = ctx.createImageData(width, height);
        for (let i = 0; i < redBand.length; i++) {
          // R、G、B 分别对应每个波段的数据
          imageData.data[i * 4] = redBand[i]; // Red channel
          imageData.data[i * 4 + 1] = greenBand[i]; // Green channel
          imageData.data[i * 4 + 2] = blueBand[i]; // Blue channel
          imageData.data[i * 4 + 3] = 255; // Alpha channel (不透明)
        }

        ctx.putImageData(imageData, 0, 0);

        canvas.toBlob(async (blob) => {
          const blobUrl = URL.createObjectURL(blob);
          const imageryProvider = new Cesium.SingleTileImageryProvider({
            url: blobUrl,
            rectangle: Cesium.Rectangle.fromDegrees(
              minLon,
              minLat,
              maxLon,
              maxLat
            ),
            tileWidth: width,
            tileHeight: height,
          });

          this.viewer.imageryLayers.addImageryProvider(imageryProvider);
        });
      } catch (error) {
        console.error("Error loading TIFF image:", error);
      }
    },

    initChart() {
      decode_CSV("src/assets/Gaoxiong_Port_Area.csv")
        .then((csv_data) => {
          // 提取日期、面积（保留4位小数）和abnormal值
          const date_list = csv_data.map((item) => item.date);
          const area_list = csv_data.map((item) =>
            parseFloat(item.area).toFixed(4)
          ); // 保留4位小数
          const abnormal_list = csv_data.map(
            (item) => parseInt(item.abnormal, 10) || 0
          );

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
              type: "time", // 将 xAxis 类型改为 "time"
              name: "日期",
              nameTextStyle: { fontSize: 18 },
              axisLabel: {
                fontSize: 18,
              },
            },
            yAxis: {
              type: "value",
              name: "面积 (km²)",
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
                data: date_list.map((date, index) => [
                  new Date(date).getTime(),
                  area_list[index],
                ]), // 将日期转换为时间戳
                color: "#FAFA33",
                smooth: true,
                showSymbol: true, // 显示所有数据点
                symbol: "circle", // 圆圈符号
                symbolSize: (value, params) =>
                  abnormal_list[params.dataIndex] === 1 ? 15 : 0, // abnormal=1 显示大圆圈
                lineStyle: {
                  color: "red", // 自定义线条颜色为红色
                  width: 3, // 自定义线条宽度
                },
                itemStyle: {
                  color: (params) =>
                    abnormal_list[params.dataIndex] === 1
                      ? "#FAFA33"
                      : "transparent", // abnormal=1 时填充黄色
                  borderColor: "black", // 圆圈的边框颜色
                  borderWidth: 1.5, // 圆圈边框宽度
                },
              },
            ],
          };

          myChart.setOption(option);
        })
        .catch((error) => console.error("CSV 解析错误: ", error));
    },

    analyzeData() {
      this.isSplit = !this.isSplit; // 切换右侧面板的显示与隐藏

      this.isImageSelectorVisible = true; // 点击分析按钮后展示“港口提取结果”窗体

      this.$nextTick(() => {
        this.adjustLayout(); // 调整布局

        if (this.isSplit && !this.chartInstance) {
          this.initChart(); // 初始化图表
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
        // 点击分析按钮时加载.tif影像
        if (this.isSplit) {
          this.loadTiffImage();
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

/* 港口提取结果选择面板 */
.image-selector-box {
  position: absolute;
  top: 10px;
  left: 300px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 280px;
  height: auto;
  padding: 15px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 0 10px rgb(0 0 0 / 10%);

  /* 根据内容自动调整高度 */
}

/* 调整 select 元素的样式 */
select {
  width: 100%;
  height: auto;

  /* 根据内容自动调整高度 */
  max-height: 200px;

  /* 限制最大高度，避免过长 */
  overflow-y: auto;

  /* 如果选项太多，可以滚动 */
}

/* 确保每个 option 不会压缩 */
option {
  white-space: nowrap;

  /* 防止文件名被压缩到一行 */
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
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 55%;
  height: 100%;
  padding: 8px;
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
  height: 91%;
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
  transition: all 0.5s ease;
}

.slide-enter,
.slide-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
