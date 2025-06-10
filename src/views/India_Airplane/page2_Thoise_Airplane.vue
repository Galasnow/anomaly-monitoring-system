<!-- 托伊斯空军基地飞机异常进出库动态监测 -->
<template>
  <div class="container">
    <div class="top-panel">
      <!-- 左上角的截止时间选择框 -->
      <div class="time-selector-box">
        <h2 class="title">托伊斯空军基地监测时间</h2>
        <h3>开始日期</h3>
        <input type="date" v-model="firstDate" @change="onDateChange" />
        <h3>截止日期</h3>
        <input type="date" v-model="secondDate" @change="onSecondDateChange" />
        <button @click="analyzeData">分析</button>
      </div>

      <!-- 选择影像文件的独立窗体 -->
      <div class="image-selector-box" v-if="isImageSelectorVisible">
        <h2 class="title">飞机提取结果</h2>
        <Calendar
          ref="calendarRef"
          transparent
          borderless
          :min-date="new Date(2016, 0, 1)"
          :max-date="new Date()"
          :attributes="attributes"
          @dayclick="onDayClickHandler"
        >
          <DatePicker v-model="calendarDate" />
        </Calendar>
        <div v-if="selectedDate" class="selected-date"></div>
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

    <!-- ECharts 图表弹窗 -->
    <div v-if="isChartModalVisible" class="modal">
      <div class="modal-content">
        <h2 class="title">托伊斯空军基地飞机异常进出库动态监测曲线</h2>
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
import "v-calendar/style.css";
import "../../styles/sub_area_page.scss";
import {
  decode_CSV,
  checkFolderExists,
  checkFinishStatus,
  loadSelectTiff,
} from "../utils/utils.js";

// Reactive state
const isSplit = ref(false);
const viewer = ref(null);
const chartInstance = ref(null);
const tifFiles = ref([]);
const cesiumContainer = ref(null);
const chartContainer = ref(null);
const isImageSelectorVisible = ref(false);
const mark_dates = ref([]);
const firstDate = ref("2016-01-01");
const secondDate = ref("2025-01-01");
const calendarDate = ref(null);
const selectedDate = defineModel();
const calendarRef = ref(null);
const isChartModalVisible = ref(false);
const isLoading = ref(false);

const tiffRootPath = "/05_India_Airplane/01_Thoise/02_Output";
const csvPath = "/05_India_Airplane/01_Thoise/Thoise_Airplane_Number.csv";

// Computed properties
const attributes = computed(() => [
  {
    key: "tif-dates",
    highlight: {
      fillMode: "light",
    },
    dates: mark_dates.value,
  },
]);

// Lifecycle hooks
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

// Methods
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

  viewer.value._cesiumWidget._creditContainer.style.display = "none";
  viewer.value.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(77.36129, 34.65526, 900.0),
  });
}

function analyzeData() {
  onAnalyzeButtonClick()
    .then((result) => {
      if (result.success) {
        console.log(result.message);
      } else {
        console.error(result.message);
      }
    })
    .catch((error) => {
      console.error("分析过程中出错:", error);
    });
}

async function onAnalyzeButtonClick() {
  try {
    // 1. 先检查文件夹是否存在
    const outTifFileUrl = "http://localhost:3017/api/files_Thoise";
    const folderExists = await checkFolderExists(outTifFileUrl);

    if (folderExists) {
      await fetchTiffFiles();
      isChartModalVisible.value = true;
      initChart();
      isImageSelectorVisible.value = true;
      console.log("文件夹存在，已加载 .tif 文件");
      return { success: true, message: "文件夹存在，已加载 .tif 文件" };
    } else {
      console.log("文件夹不存在，正在调用 Python 脚本进行处理...");
      const result = await runMainPythonScript();
      return { success: true, message: "，已加载 .tif 文件" };
    }
  } catch (error) {
    console.error("分析按钮点击时出错:", error);
    return { success: false, message: `出错: ${error.message}` };
  }
}

async function runMainPythonScript() {
  try {
    isLoading.value = true;
    const response = await axios.get(
      "http://localhost:3017/api/run_main_Bhatinda"
    );
    console.log("返回消息:", response.data.message);

    if (response.data.message === "main.py 执行已启动") {
      // 等待文件夹生成并检查是否有 finish.txt 文件
      const finishResponseUrl = "http://localhost:3017/api/files_txt_Bhatinda";
      const isFinished = await checkFinishStatus(finishResponseUrl);

      if (isFinished) {
        console.log("执行成功，main.py 执行完成");
        await fetchTiffFiles();
        isChartModalVisible.value = true;
        initChart();
        isImageSelectorVisible.value = true;
      } else {
        console.error("执行失败：没有找到 finish.txt 文件");
      }
    } else {
      console.error("执行失败:", response.data.message);
    }
  } catch (error) {
    console.error("分析执行失败:", error);
  } finally {
    isLoading.value = false;
  }
}

async function fetchTiffFiles() {
  try {
    const response = await axios.get("http://localhost:3017/api/files_Thoise");
    console.log("返回的数据:", response.data);

    tifFiles.value = response.data.files.map((file) => ({
      fullName: file,
      shortName: file.substring(0, 8),
    }));

    mark_dates.value = [];
    const files = tifFiles.value;
    for (let i = 0; i < tifFiles.value.length; i++) {
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

async function onDayClickHandler(day) {
  const selectedDate = ref(null);
  selectedDate.value = day.date;
  const year_str = day.year;
  const month_str = ("0" + day.month).slice(-2);
  const day_str = ("0" + day.day).slice(-2);
  const date_str = `${year_str}${month_str}${day_str}`;
  console.log("date_str:", date_str);

  // 查找对应的TIFF文件并加载
  loadSelectTiff(tifFiles, date_str, tiffRootPath, viewer);
}

function initChart() {
  decode_CSV(csvPath)
    .then((csv_data) => {
      // 提取日期、面积（保留4位小数）和abnormal值
      const date_list = csv_data.map((item) => item.date);
      const area_list = csv_data.map((item) => parseInt(item.number));
      const abnormal_list = csv_data.map(
        (item) => parseInt(item.abnormal, 10) || 0
      );

      console.log("date_list:", date_list);
      console.log("area_list:", area_list);
      console.log("abnormal_list:", abnormal_list);

      const myChart = echarts.init(chartContainer.value);
      myChart.clear();

      const option = {
        tooltip: {
          trigger: "axis",
          valueFormatter: function (value) {
            return value + "架";
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
          name: "数量 (架)",
          nameTextStyle: { fontSize: 18 },
          min: 0,
          max: 1,
          axisLabel: {
            formatter: (value) => {
              return [0, 1].includes(value) ? value.toFixed(0) : "";
            },
            fontSize: 18,
          },
        },
        series: [
          {
            name: "数量",
            type: "line",
            data: date_list.map((date, index) => [
              new Date(date).getTime(),
              area_list[index],
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
        loadSelectTiff(tifFiles, date_str, tiffRootPath, viewer);
      });
      chartInstance.value = myChart;
    })
    .catch((error) => console.error("CSV 解析错误: ", error));
}

function adjustLayout() {
  if (viewer.value && !viewer.value.isDestroyed()) {
    viewer.value.resize();
  }
  if (chartInstance.value) {
    chartInstance.value.resize();
  }
}

function handleResize() {
  adjustLayout();
}
</script>
