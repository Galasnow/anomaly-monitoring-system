<!-- 大彰化风力发电场异常新建动态监测 -->
<template>
  <div class="container">
    <div class="top-panel">
      <!-- 左上角的截止时间选择框 -->
      <div class="time-selector-box">
        <h2 class="title">大彰化风力发电场异常新建动态监测</h2>
        <h3>开始日期</h3>
        <input v-model="firstDate" type="date" @change="onDateChange" />
        <h3>截止日期</h3>
        <input v-model="secondDate" type="date" @change="onSecondDateChange" />
        <button @click="analyzeData">分析</button>
      </div>

      <!-- 选择影像文件的独立窗体 -->
      <div v-if="isImageSelectorVisible" class="image-selector-box">
        <h2 class="title">大彰化风力发电场涡轮机提取结果</h2>
        <Calendar
          ref="calendarRef"
          transparent
          borderless
          :min-date="new Date(2021, 3, 1)"
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

    <div v-show="isLoading" id="loading">
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
        <h2 class="title">大彰化风力发电场涡轮机数量监测曲线</h2>
        <div ref="chartContainer" style="width: 600px; height: 400px"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { cesium_token } from "../../../my_package.json";
import { Viewer } from "cesium";
import * as Cesium from "cesium";
import * as echarts from "echarts";
import "cesium/Build/Cesium/Widgets/widgets.css";
import axios from "axios";
import { Calendar, DatePicker } from "v-calendar";
import { backendUrlPrefix } from "../utils/global_variable.js";
import "v-calendar/style.css";
import "../../styles/sub_area_page.scss";
import {
  decode_CSV,
  checkFolderExists,
  checkFinishStatus,
  loadSelectTiff,
  fetchTiffFiles,
} from "../utils/utils.js";

// 响应式数据
const isSplit = ref(false);
const viewer = ref(null);
const chartInstance = ref(null);
const tifFiles = ref([]);
const isImageSelectorVisible = ref(false);
const markDatesGreaterZhangHua = ref([]);
const cesiumContainer = ref(null);
const chartContainer = ref(null);
const firstDate = ref("2021-04-01");
const secondDate = ref("2025-07-04");
const calendarDate = ref(null);
const selectedDate = defineModel({ type: Date });
const calendarRef = ref(null);
const isLoading = ref(false);
const isChartModalVisible = ref(false);

const tiffRootPath = "/Wind_Farm/output/predict/";
const csvPath = "/Wind_Farm/output/turbine_number.csv";
const tiffApiUrl = `${backendUrlPrefix}/files_GreaterZhangHua`;
const mainScriptUrl = `${backendUrlPrefix}/run_main_wind_farm`;
const finishResponseUrl = `${backendUrlPrefix}/files_txt_GreaterZhangHua`;

// 计算属性
const attributes = computed(() => {
  return [
    {
      key: "tif-dates",
      highlight: {
        fillMode: "light",
        color: "blue",
      },
      dates: markDatesGreaterZhangHua.value,
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
    destination: Cesium.Cartesian3.fromDegrees(119.795, 24.1795, 55000),
  });
}

async function analyzeData() {
  try {
    // 1. 先检查文件夹是否存在
    const folderExists = await checkFolderExists(tiffApiUrl);

    if (folderExists) {
      // 2. 如果文件夹存在，直接加载 .tif 文件并展示
      const { files, markDates } = await fetchTiffFiles(tiffApiUrl, 17);
      console.log("markDates:", markDates);
      tifFiles.value = files;
      markDatesGreaterZhangHua.value = markDates;
      console.log("files:", files);
      console.log("markDatesGreaterZhangHua:", markDatesGreaterZhangHua.value);
      // loadpoint(viewer.value);
      isChartModalVisible.value = true; // 显示ECharts弹窗
      initChart(); // 初始化ECharts图表
      isImageSelectorVisible.value = true; // 点击分析按钮后展示“提取结果”窗体  // 成功提示
      console.log("文件夹存在，已加载 .tif 文件");
    } else {
      // 3. 如果文件夹不存在，调用后端的 main.py 进行处理
      console.log("文件夹不存在，正在调用 Python 脚本进行处理...");
      await runMainPythonScript();
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
    const response = await axios.get(mainScriptUrl);
    console.log("返回消息:", response.data.message); // 确认是否成功执行

    // 检查返回值
    if (response.data.message === "main.py 执行已启动") {
      // 等待文件夹生成并检查是否有 finish.txt 文件
      const isFinished = await checkFinishStatus(finishResponseUrl);

      if (isFinished) {
        console.log("Python 脚本执行完成");
        // 执行完成后，继续后续的操作，如加载文件
        // loadpoint(viewer.value);
        const { files, markDates } = await fetchTiffFiles(tiffApiUrl, 17);
        tifFiles.value = files;
        markDatesGreaterZhangHua.value = markDates;

        isChartModalVisible.value = true; // 显示ECharts弹窗
        initChart(); // 初始化ECharts图表
        isImageSelectorVisible.value = true; // 点击分析按钮后展示“提取结果”窗体  // 成功提示
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

// 日期点击处理
async function onDayClickHandler(day) {
  selectedDate.value = day.date;
  const year_str = day.year;
  const month_str = ("0" + day.month).slice(-2);
  const day_str = ("0" + day.day).slice(-2);
  const date_str = `${year_str}${month_str}${day_str}`;
  console.log("date_str:", date_str);

  // 查找对应的TIFF文件并加载
  loadSelectTiff(tifFiles, date_str, tiffRootPath, viewer);
}

// 加载点数据
// async function loadpoint(viewer) {
//   try {
//     const geo_json = "/sk10_platform/sk10_platform_point.json";
//     const dataSource = await Cesium.GeoJsonDataSource.load(geo_json, {
//       markerSymbol: "circle",
//       markerSize: 30,
//       stroke: Cesium.Color.HOTPINK,
//       fill: Cesium.Color.PINK.withAlpha(1),
//       strokeWidth: 3,
//       clampToGround: true,
//     });

//     dataSource.entities.values.forEach((value) => {
//       value.billboard = undefined;
//       if (value._properties._Frequency._value == 230) {
//         value.point = {
//           pixelSize: 6,
//           color: Cesium.Color.GREEN,
//           show: true,
//         };
//       } else {
//         value.point = {
//           pixelSize: 5,
//           color: Cesium.Color.RED,
//           show: true,
//         };
//       }
//     });

//     console.log(dataSource);
//     viewer.dataSources.add(dataSource);
//     viewer.flyTo(dataSource, {
//       duration: 1.5,
//       orientation: {
//         heading: Cesium.Math.toRadians(0),
//         pitch: Cesium.Math.toRadians(0),
//         roll: 0.0,
//       },
//     });
//   } catch (error) {
//     console.error("加载 GeoJSON 失败:", error);
//     alert("加载 GeoJSON 失败，请检查数据格式");
//   }
// }

// 初始化图表
function initChart() {
  decode_CSV(csvPath)
    .then((csv_data) => {
      const date_list = csv_data.map((item) => item.date);
      const number_list = csv_data.map((item) => parseInt(item.number));
      const anomaly_list = csv_data.map(
        (item) => parseInt(item.anomaly, 10) || 0
      );

      const myChart = echarts.init(chartContainer.value);
      myChart.clear();

      const option = {
        tooltip: {
          trigger: "axis",
          valueFormatter(value) {
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
          interval: 10,
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
              anomaly_list[params.dataIndex] === 1 ? 15 : 0,
            lineStyle: {
              color: "red",
              width: 3,
            },
            itemStyle: {
              color: (params) =>
                anomaly_list[params.dataIndex] === 1
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
        loadSelectTiff(tifFiles, date_str, tiffRootPath, viewer);
      });
      chartInstance.value = myChart;
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
