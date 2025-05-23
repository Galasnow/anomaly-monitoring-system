<!-- SK10海上油气平台异常出现与消失动态监测 -->
<template>
  <div class="container">
    <div class="top-panel">
      <!-- 左上角的截止时间选择框 -->
      <div class="time-selector-box">
        <h2 class="title">SK10海上油气平台异常出现与消失动态监测</h2>
        <h3>开始日期</h3>
        <input type="date" v-model="firstDate" @change="onDateChange" />
        <h3>截止日期</h3>
        <input type="date" v-model="secondDate" @change="onSecondDateChange" />
        <button @click="analyzeData">分析</button>
      </div>

      <!-- 选择影像文件的独立窗体 -->
      <div class="image-selector-box" v-if="isImageSelectorVisible">
        <h2 class="title">SK10海上油气平台提取结果</h2>
        <Calendar
          ref="calendarRef"
          transparent
          borderless
          :min-date="new Date(2017, 0, 1)"
          :max-date="new Date()"
          :attributes="attributes"
          @dayclick="onDayClickHandler"
        >
          <DatePicker v-model="calendarDate" />
        </Calendar>
        <div v-if="selectedDate" class="selected-date">
          <!-- 当前选中日期：{{ formattedDate }} -->
        </div>
      </div>
    </div>

    <div id="loading" v-show="isLoading">
      <p>正在执行，请稍候...</p>
    </div>

    <!-- Cesium 3D地球容器 -->
    <div
      ref="cesiumContainer"
      :class="['cesium-container', { 'split-left': isSplit }]"
    ></div>

    <!-- 右侧内容容器 -->
    <div v-if="isChartModalVisible" class="modal">
      <div class="modal-content">
        <h2 class="title">SK10海上油气平台数量监测曲线</h2>
        <div ref="chartContainer" style="width: 600px; height: 400px"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from "vue";
import { cesium_token } from "../../../my_package.json";
import { Viewer } from "cesium";
import * as Cesium from "cesium";
import * as echarts from "echarts";
import "cesium/Build/Cesium/Widgets/widgets.css";
import axios from "axios";
import * as d3 from "d3";
import * as GeoTIFF from "geotiff";
import { Calendar, DatePicker } from "v-calendar";
import "v-calendar/style.css";

// 响应式数据
const isSplit = ref(false);
const viewer = ref(null);
const chartInstance = ref(null);
const tifFiles_sk10 = ref([]);
const tifFiles_sk10_gaofen = ref([]);
const selectedTiff = ref(null);
const isImageSelectorVisible = ref(false);
const mark_dates_sentinel_1 = ref([]);
const mark_dates_gaofen = ref([]);
const cesiumContainer = ref(null);
const chartContainer = ref(null);
const firstDate = ref("");
const secondDate = ref("");
const calendarDate = ref(null);
const selectedDate = defineModel();
const image1 = ref("");
const calendarRef = ref(null);
const isLoading = ref(false);
const isChartModalVisible = ref(false);

// 计算属性
const attributes = computed(() => {
  return [
    {
      key: "tif-dates",
      highlight: {
        fillMode: "light",
        color: "blue",
      },
      dates: mark_dates_sentinel_1.value,
    },
    {
      key: "tif-dates_gaofen",
      highlight: {
        fillMode: "light",
        color: "red",
      },
      dates: mark_dates_gaofen.value,
    },
  ];
});

const formattedDate = computed(() => {
  console.log(selectedDate);
  return selectedDate.value ? selectedDate.value.toLocaleDateString() : "";
});

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

// 初始化Cesium
async function initCesium() {
  Cesium.Ion.defaultAccessToken = cesium_token;
  viewer.value = new Viewer(cesiumContainer.value, {
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
  viewer.value._cesiumWidget._creditContainer.style.display = "none";

  // 设置初始视角
  viewer.value.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(113.45, 4.78, 200000),
  });
}

// 获取TIFF文件列表
async function fetchTiffFiles_Gaofen() {
  try {
    const response = await axios.get(
      "http://localhost:3017/api/files_sk10_Gaofen"
    );
    console.log("返回的数据:", response.data);

    tifFiles_sk10_gaofen.value = response.data.files.map((file) => ({
      fullName: file,
      shortName: file.substring(4, 12),
    }));

    mark_dates_gaofen.value = [];
    const files = tifFiles_sk10_gaofen.value;
    for (let i = 0; i < tifFiles_sk10_gaofen.value.length; i++) {
      const file = files[i].fullName;
      const year = file.substring(4, 8);
      const month = file.substring(8, 10);
      const day = file.substring(10, 12);
      console.log(year);
      mark_dates_gaofen.value.push(new Date(year, month - 1, day));
    }
  } catch (error) {
    console.error("获取文件列表时出错:", error);
  }
}

async function checkFolderExists() {
  try {
    const response = await axios.get(
      "http://localhost:3017/api/check-folder_sk10_sentinel-1"
    );
    console.log("response", response);
    // 根据返回的数据格式进行判定
    if (response.data.files) {
      return true; // 如果文件夹中有 .tif 文件
    } else if (response.data.error || response.data.message) {
      return false; // 如果发生错误或没有找到文件
    }
  } catch (error) {
    console.error("检查文件夹是否存在时出错:", error);
    return false; // 出现错误时认为文件夹不存在
  }
}

async function analyzeData() {
  try {
    // 1. 先检查文件夹是否存在
    const folderExists = await checkFolderExists();

    if (folderExists) {
      // 2. 如果文件夹存在，直接加载 .tif 文件并展示
      await fetchTiffFiles();
      loadpoint(viewer.value);
      // await loadSelectedTiff();
      isChartModalVisible.value = true; // 显示ECharts弹窗
      initChart(); // 初始化ECharts图表
      isImageSelectorVisible.value = true; // 点击分析按钮后展示“港口提取结果”窗体  // 成功提示
      console.log("文件夹存在，已加载 .tif 文件");
    } else {
      // 3. 如果文件夹不存在，调用后端的 main.py 进行处理
      console.log("文件夹不存在，正在调用 Python 脚本进行处理...");
      const result = await runMainPythonScript();
      console.log("执行完成，已加载 .tif 文件"); // 返回 Python 脚本的执行结果
    }
  } catch (error) {
    console.error("分析按钮点击时出错:", error, "message:", error.message);
  }
}

async function runMainPythonScript() {
  try {
    // 开始执行时显示加载框
    isLoading.value = true; // 显示加载框

    // 点击“分析”按钮时，先执行 main.py 生成 .tif 文件
    const response = await axios.get(
      "http://localhost:3017/api/run-main_offshore_platform"
    );
    console.log("返回消息:", response.data.message); // 确认是否成功执行

    // 检查返回值
    if (response.data.message === "main.py 执行已启动") {
      // 等待文件夹生成并检查是否有 finish.txt 文件
      const isFinished = await checkFolderAndLoadFiles();

      if (isFinished) {
        console.log("Python 脚本执行完成");
        // 执行完成后，继续后续的操作，如加载文件
        loadpoint(viewer.value);
        await fetchTiffFiles();
        // await loadSelectedTiff();  // 根据你的需要加载文件
        isChartModalVisible.value = true; // 显示ECharts弹窗
        initChart(); // 初始化ECharts图表
        isImageSelectorVisible.value = true; // 点击分析按钮后展示“港口提取结果”窗体  // 成功提示
      } else {
        console.error("执行失败：没有找到 finish.txt 文件");
      }
    } else {
      console.error("执行失败:", response.data.message);
    }
  } catch (error) {
    console.error("分析执行失败:", error);
  } finally {
    // 执行完毕后隐藏加载框
    isLoading.value = false; // 隐藏加载框
  }
}

function checkFolderAndLoadFiles() {
  return new Promise((resolve, reject) => {
    const startTime = Date.now(); // 获取开始时间
    const timeLimit = 60 * 60 * 1000; // 60分钟的时间限制 (单位：毫秒)

    const intervalId = setInterval(async () => {
      try {
        // 检查是否超时
        if (Date.now() - startTime > timeLimit) {
          clearInterval(intervalId); // 停止定时器
          console.log("时间已到，未找到 finish.txt 文件");
          resolve(false); // 返回失败标志
          return;
        }

        // 尝试获取文件夹中的文件
        const response = await axios.get(
          "http://localhost:3017/api/sk10_platform_finish_txt"
        );

        // 查找是否存在 finish.txt 文件
        const finishFile = response.data.files.find(
          (file) => file === "finish.txt"
        );

        // 如果 finish.txt 文件存在，表示 main.py 执行完成
        if (finishFile) {
          clearInterval(intervalId); // 停止定时器
          console.log("main.py 执行完成，文件夹中存在 finish.txt");
          resolve(true); // 返回执行完成的标志
        }
      } catch (error) {
        console.error("获取文件列表时出错:", error);
      }
    }, 30 * 1000); // 每30秒检查一次
  });
}

// 获取TIFF文件列表
async function fetchTiffFiles() {
  try {
    const response = await axios.get(
      "http://localhost:3017/api/files_sk10_sentinel-1"
    );
    console.log("返回的数据:", response.data);

    tifFiles_sk10.value = response.data.files.map((file) => ({
      fullName: file,
      shortName: file.substring(17, 25),
    }));

    mark_dates_sentinel_1.value = [];
    const files = tifFiles_sk10.value;
    for (let i = 0; i < tifFiles_sk10.value.length; i++) {
      const file = files[i].fullName;
      const year = file.substring(17, 21);
      const month = file.substring(21, 23);
      const day = file.substring(23, 25);
      mark_dates_sentinel_1.value.push(new Date(year, month - 1, day));
    }
  } catch (error) {
    console.error("获取文件列表时出错:", error);
  }
}

// 日期点击处理
async function onDayClickHandler(day) {
  selectedDate.value = day.date;
  const year_str = day.year;
  const month_str = ("0" + day.month).slice(-2);
  const day_str = ("0" + day.day).slice(-2);
  const date_str = `${year_str}${month_str}${day_str}`;
  console.log("date_str:", date_str);

  const selected = tifFiles_sk10_gaofen.value.filter(
    (element) => element.shortName == date_str
  )[0];
  if (selected) {
    const tiffUrl = `/sk10_platform/gaofen/${selected.fullName}`;
    console.log(tiffUrl);
    await loadTiffImage(tiffUrl);
  } else {
    const selected = tifFiles_sk10.value.filter(
      (element) => element.shortName == date_str
    )[0];
    if (selected) {
      const tiffUrl = `/sk10_platform/output/predict/${selected.fullName}`;
      console.log(tiffUrl);
      await loadTiffImage(tiffUrl);
    }
  }
}

// 加载点数据
async function loadpoint(viewer) {
  try {
    const geo_json = "/sk10_platform/sk10_platform_point.json";
    const dataSource = await Cesium.GeoJsonDataSource.load(geo_json, {
      markerSymbol: "circle",
      markerSize: 30,
      stroke: Cesium.Color.HOTPINK,
      fill: Cesium.Color.PINK.withAlpha(1),
      strokeWidth: 3,
      clampToGround: true,
    });

    dataSource.entities.values.forEach((value) => {
      value.billboard = undefined;
      if (value._properties._Frequency._value == 230) {
        value.point = {
          pixelSize: 6,
          color: Cesium.Color.GREEN,
          show: true,
        };
      } else {
        value.point = {
          pixelSize: 5,
          color: Cesium.Color.RED,
          show: true,
        };
      }
    });

    console.log(dataSource);
    viewer.dataSources.add(dataSource);
    viewer.flyTo(dataSource, {
      duration: 1.5,
      orientation: {
        heading: Cesium.Math.toRadians(0),
        pitch: Cesium.Math.toRadians(0),
        roll: 0.0,
      },
    });
  } catch (error) {
    console.error("加载 GeoJSON 失败:", error);
    alert("加载 GeoJSON 失败，请检查数据格式");
  }
}

// 加载TIFF图像
async function loadTiffImage(tiffUrl) {
  try {
    const response = await fetch(tiffUrl);
    console.log(tiffUrl);
    const arrayBuffer = await response.arrayBuffer();
    const tiff = await GeoTIFF.fromArrayBuffer(arrayBuffer);

    const image = await tiff.getImage();
    const width = image.getWidth();
    const height = image.getHeight();
    const rasters = await image.readRasters();

    console.log("Image width:", width, "height:", height);
    console.log("Rasters data:", rasters);

    const bbox = image.getBoundingBox();
    console.log("Bounding box:", bbox);

    if (!bbox || bbox.length !== 4) {
      throw new Error("Invalid bounding box retrieved from TIFF image.");
    }

    const [minLon, minLat, maxLon, maxLat] = bbox;

    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    canvas.width = width;
    canvas.height = height;

    const imageData = ctx.createImageData(width, height);

    const redBand = ref([]);
    const greenBand = ref([]);
    const blueBand = ref([]);
    if (rasters.length == 1) {
      redBand.value = rasters[0];
      greenBand.value = rasters[0];
      blueBand.value = rasters[0];
    } else if (rasters.length == 3) {
      redBand.value = rasters[0];
      greenBand.value = rasters[1];
      blueBand.value = rasters[2];
    }
    for (let i = 0; i < redBand.value.length; i++) {
      imageData.data[i * 4] = redBand.value[i];
      imageData.data[i * 4 + 1] = greenBand.value[i];
      imageData.data[i * 4 + 2] = blueBand.value[i];
      imageData.data[i * 4 + 3] = 255;
    }

    ctx.putImageData(imageData, 0, 0);

    canvas.toBlob(async (blob) => {
      const blobUrl = URL.createObjectURL(blob);
      const imageryProvider = new Cesium.SingleTileImageryProvider({
        url: blobUrl,
        rectangle: Cesium.Rectangle.fromDegrees(minLon, minLat, maxLon, maxLat),
        tileWidth: width,
        tileHeight: height,
      });

      viewer.value.imageryLayers.addImageryProvider(imageryProvider);
    });
  } catch (error) {
    console.error("Error loading TIFF image:", error);
  }
}

// 初始化图表
function initChart() {
  decode_CSV("/sk10_platform/output/platform_number.csv")
    .then((csv_data) => {
      const date_list = csv_data.map((item) => item.date);
      const number_list = csv_data.map((item) => parseInt(item.number));
      const abnormal_list = csv_data.map(
        (item) => parseInt(item.anomaly, 10) || 0
      );

      const myChart = echarts.init(chartContainer.value);
      myChart.clear();

      const option = {
        tooltip: {
          trigger: "axis",
          valueFormatter: function (value) {
            return value;
          },
        },
        xAxis: {
          type: "time",
          name: "日期",
          nameTextStyle: { fontSize: 18 },
          axisLabel: {
            fontSize: 18,
          },
        },
        yAxis: {
          type: "value",
          name: "数量",
          nameTextStyle: { fontSize: 18 },
          min: Math.min(...number_list),
          max: Math.max(...number_list),
          interval: 1,
          axisLabel: {
            formatter: (value) => value,
            fontSize: 18,
          },
        },
        series: [
          {
            name: "数量",
            type: "line",
            data: date_list.map((date, index) => [
              new Date(date).getTime(),
              number_list[index],
            ]),
            color: "#FAFA33",
            smooth: true,
            showSymbol: true,
            symbol: "circle",
            symbolSize: (value, params) =>
              abnormal_list[params.dataIndex] === 1 ? 15 : 0,
            lineStyle: {
              color: "red",
              width: 3,
            },
            itemStyle: {
              color: (params) =>
                abnormal_list[params.dataIndex] === 1
                  ? "#FAFA33"
                  : "transparent",
              borderColor: "black",
              borderWidth: 1.5,
            },
          },
        ],
      };

      myChart.setOption(option);
      myChart.on("click", function (params) {
        // 直接从点击的数据点获取日期
        const clickedDate = new Date(params.value[0]);
        calendarDate.value = clickedDate;
        selectedDate.value = clickedDate;
        // 跳转到选中日期的月份页面
        if (calendarRef.value) {
          calendarRef.value.move(clickedDate);
        }
        // 格式化为 YYYYMMDD
        const year = clickedDate.getFullYear();
        const month = String(clickedDate.getMonth() + 1).padStart(2, "0");
        const day = String(clickedDate.getDate()).padStart(2, "0");
        const date_str = `${year}${month}${day}`;

        console.log("Clicked date:", date_str);

        // 查找对应的TIFF文件并加载
        const selected = tifFiles_sk10_gaofen.value.filter(
          (element) => element.shortName == date_str
        )[0];
        if (selected) {
          const tiffUrl = `/sk10_platform/gaofen/${selected.fullName}`;
          console.log(tiffUrl);
          loadTiffImage(tiffUrl);
        } else {
          const selected = tifFiles_sk10.value.filter(
            (element) => element.shortName == date_str
          )[0];
          if (selected) {
            const tiffUrl = `/sk10_platform/output/predict/${selected.fullName}`;
            console.log(tiffUrl);
            loadTiffImage(tiffUrl);
          }
        }
      });
    })
    .catch((error) => console.error("CSV 解析错误: ", error));
}

// 调整布局
function adjustLayout() {
  if (viewer.value && !viewer.value.isDestroyed()) {
    viewer.value.resize();
  }
  if (chartInstance.value) {
    chartInstance.value.resize();
  }
}

// 处理窗口大小变化
function handleResize() {
  adjustLayout();
}

// 生命周期钩子
onMounted(() => {
  initCesium();
  fetchTiffFiles_Gaofen();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  if (viewer.value && !viewer.value.isDestroyed()) {
    viewer.value.destroy();
  }
  if (chartInstance.value) {
    chartInstance.value.dispose();
  }
  window.removeEventListener("resize", handleResize);
});

// 日期变化处理函数
function onDateChange() {
  // 实现日期变化逻辑
}

function onSecondDateChange() {
  // 实现日期变化逻辑
}
</script>

/* 页面主容器 */
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
  width: auto;
  height: 300px;
  padding: 15px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 0 10px rgb(0 0 0 / 10%);

  /* 根据内容自动调整高度 */
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

/* Echart弹框的位置 */
.modal {
  position: fixed;
  top: 405px;
  left: 310px;
  display: flex;
  width: 500px;
  height: 450px;
  background-color: rgb(0 0 0 / 50%);
}

.modal-content {
  padding: 20px;
  background: white;
  border-radius: 10px;
}

#loading {
  position: fixed;
  top: 50%;
  left: 50%;
  z-index: 9999;

  /* 将元素居中 */
  padding: 20px;
  font-size: 20px;

  /* 半透明背景 */
  color: white;
  background-color: rgb(0 0 0 / 70%);
  border-radius: 5px;
  transform: translate(-50%, -50%);

  /* 确保 loading 层位于其他内容之上 */
}
</style>
