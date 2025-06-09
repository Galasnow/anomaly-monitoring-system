<!-- 南华礁船舶异常聚集监测 -->
<template>
  <div class="container">
    <div class="top-panel">
      <!-- 左上角的截止时间选择框 -->
      <div class="time-selector-box">
        <h2 class="title">南华礁船舶异常聚集监测</h2>
        <h3>开始日期</h3>
        <input type="date" v-model="firstDate" @change="onDateChange" />
        <h3>截止日期</h3>
        <input type="date" v-model="secondDate" @change="onSecondDateChange" />
        <button @click="analyzeData">分析</button>
      </div>

      <!-- 选择影像文件的独立窗体 -->
      <div class="image-selector-box" v-if="isImageSelectorVisible">
        <h2 class="title">南华礁提取结果</h2>
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
        <h2 class="title">南华礁船舶异常聚集监测曲线</h2>
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
import * as GeoTIFF from "geotiff";
import { Calendar, DatePicker } from "v-calendar";
import "v-calendar/style.css";
import "../../styles/sub_area_page.scss";
import {
  decode_CSV,
  checkFolderExists,
  checkFinishStatus,
  reprojectGeoTiff,
} from "../utils/utils.js";

// 响应式数据
const isSplit = ref(false);
const viewer = ref(null);
const chartInstance = ref(null);
const tif_files = ref([]);
const selectedTiff = ref(null);
const isImageSelectorVisible = ref(false);
const mark_dates = ref([]);
const cesiumContainer = ref(null);
const chartContainer = ref(null);
const firstDate = ref("2016-01-01");
const secondDate = ref("2025-01-01");
const calendarDate = ref(null);
const selectedDate = defineModel();
const image1 = ref("");
const calendarRef = ref(null);
const isLoading = ref(false);
const isChartModalVisible = ref(false);

const tiffRootPath = "/Ship_Gather/02_Nanhuajiao/result";
const csvPath = "/Ship_Gather/02_Nanhuajiao/02_nanhuajiao_Number.csv";

// 计算属性
const attributes = computed(() => {
  return [
    {
      key: "tif-dates",
      highlight: {
        fillMode: "light",
        color: "blue",
      },
      dates: mark_dates.value,
    },
  ];
});

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
    destination: Cesium.Cartesian3.fromDegrees(114.1841, 8.7135, 100000),
  });
}

async function analyzeData() {
  try {
    // 1. 先检查文件夹是否存在
    const outTifFileUrl = "http://localhost:3017/api/files_nanhuajiao";
    const folderExists = await checkFolderExists(outTifFileUrl);

    if (folderExists) {
      // 2. 如果文件夹存在，直接加载 .tif 文件并展示
      await fetchTiffFiles();
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
      "http://localhost:3017/api/run-main_nanhuajiao"
    );
    console.log("返回消息:", response.data.message); // 确认是否成功执行

    // 检查返回值
    if (response.data.message === "main.py 执行已启动") {
      // 等待文件夹生成并检查是否有 finish.txt 文件
      const finishResponseUrl =
        "http://localhost:3017/api/nanhuajiao_finish_txt";
      const isFinished = await checkFinishStatus(finishResponseUrl);

      if (isFinished) {
        console.log("Python 脚本执行完成");
        // 执行完成后，继续后续的操作，如加载文件
        loadpoint(viewer.value);
        await fetchTiffFiles();
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

// 获取TIFF文件列表
async function fetchTiffFiles() {
  try {
    const response = await axios.get(
      "http://localhost:3017/api/files_nanhuajiao"
    );
    console.log("返回的数据:", response.data);

    tif_files.value = response.data.files.map((file) => ({
      fullName: file,
      shortName: file.substring(0, 8),
    }));

    mark_dates.value = [];
    const files = tif_files.value;
    // console.log(files)
    for (let i = 0; i < tif_files.value.length; i++) {
      const file = files[i].fullName;
      const year = file.substring(0, 4);
      const month = file.substring(4, 6);
      const day = file.substring(6, 8);
      mark_dates.value.push(new Date(year, month - 1, day));
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

  const selectedTiff = tif_files.value.filter(
    (element) => element.shortName == date_str
  )[0];
  if (selectedTiff) {
    const tiffUrl = `${tiffRootPath}/${selectedTiff.fullName}`;
    console.log(tiffUrl);
    await loadTiffImage(tiffUrl);
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

    const [minLon, minLat, maxLon, maxLat] = await reprojectGeoTiff(image);

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
  decode_CSV(csvPath)
    .then((csv_data) => {
      const date_list = csv_data.map((item) => item.date);
      const number_list = csv_data.map((item) => parseInt(item.number));
      const abnormal_list = csv_data.map(
        (item) => parseInt(item.abnormal, 10) || 0
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
          interval: 2,
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
        const selectedTiff = tif_files.value.filter(
          (element) => element.shortName == date_str
        )[0];
        if (selectedTiff) {
          const tiffUrl = `${tiffRootPath}/${selectedTiff.fullName}`;
          console.log(tiffUrl);
          loadTiffImage(tiffUrl);
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
