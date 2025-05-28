<!-- 杜尔布克营地异常扩建动态监测 -->
<template>
  <div class="container">
    <div class="top-panel">
      <!-- 左上角的截止时间选择框 -->
      <div class="time-selector-box">
        <h2 class="title">贾布瓦空军基地监测时间</h2>
        <h3>开始日期</h3>
        <input type="date" v-model="selectedDate" @change="onDateChange" />
        <h3>截止日期</h3>
        <input type="date" v-model="secondDate" @change="onSecondDateChange" />
        <button @click="analyzeData">分析</button>
      </div>

      <!-- 选择影像文件的独立窗体 -->
      <div class="image-selector-box" v-if="isImageSelectorVisible">
        <h2 class="title">机场提取结果</h2>
        <Calendar transparent borderless :min-date="new Date(2016, 0, 1)" :max-date="new Date()"
          :attributes='attributes' @dayclick="onDayClickHandler">
          <DatePicker v-model="date"></DatePicker>
        </Calendar>
        <div v-if="selectedDate" class="selected-date">

        </div>
      </div>

    </div>

    <div id="loading" v-show="isLoading">
      <p>正在执行，请稍候...</p>
    </div>




    <!-- Cesium 3D地球容器 -->
    <div ref="cesiumContainer" :class="['cesium-container', { 'split-left': isSplit }]"></div>

    <!-- ECharts 图表弹窗 -->
    <div v-if="isChartModalVisible" class="modal">
      <div class="modal-content">
        <h2 class="title">贾布瓦空军基地异常扩建动态监测曲线</h2>
        <div ref="chartContainer" style="width: 600px; height: 400px;"></div>
      </div>
    </div>
  </div>
</template>



<script>
import { cesium_token } from "../../../my_package.json";
import { Viewer } from "cesium";
import * as Cesium from "cesium";
import * as echarts from "echarts";
import "cesium/Build/Cesium/Widgets/widgets.css";
import axios from "axios";  // 导入 axios
import * as d3 from "d3";
import * as GeoTIFF from "geotiff";
import proj4 from "proj4";  // 导入 proj4 用于坐标转换

import { Calendar, DatePicker } from 'v-calendar';
import 'v-calendar/style.css';
import { ref } from 'vue';

import { toRaw } from 'vue';


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

function generate_date_list(tifFiles) {
  var out_date_list = []
  for (var i = 0; i < tifFiles.length; i++) {
    var file = tifFiles[i]
    var year = file.substring(0, 4)
    var month = file.substring(4, 6)
    var day = file.substring(6, 8)
    out_date_list.push(new Date(year, month - 1, day))
  }
  return out_date_list
}

export default {
  components: {
    Calendar,
    DatePicker,
  },
  data() {
    return {
      isSplit: false,
      viewer: null,
      chartInstance: null,
      tifFiles: [], // 存储 .tif 文件名
      selectedTiff: null, // 选择的 .tif 文件
      isImageSelectorVisible: false, // 控制“港口提取结果”窗体的显示与隐藏
      mark_dates: null,
      isChartModalVisible: false, // 控制ECharts弹窗的显示
      isLoading: false,
    };
  },
  computed: {
    attributes() {
      return [{
        key: 'tif-dates',
        highlight: {
          fillMode: 'light',
        },
        dates: this.mark_dates
      }]
    }
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
    async initCesium() {
      // 初始化Cesium Viewer
      Cesium.Ion.defaultAccessToken = cesium_token
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
        destination: Cesium.Cartesian3.fromDegrees(95.120166, 27.466836, 700.0),
      });
    },


    // 点击“分析”按钮时，执行该方法
    analyzeData() {
      // 先执行文件夹检查，进而加载.tif文件或调用Python 脚本
      this.onAnalyzeButtonClick().then(result => {
        if (result.success) {
          console.log(result.message);

        } else {
          console.error(result.message);  // 错误提示
        }
      }).catch(error => {
        console.error('分析过程中出错:', error);
      });

    },


    async onAnalyzeButtonClick() {
      try {
        // 1. 先检查文件夹是否存在
        const folderExists = await this.checkFolderExists();

        if (folderExists) {
          // 2. 如果文件夹存在，直接加载 .tif 文件并展示
          await this.fetchTiffFiles();
          // await this.loadSelectedTiff();
          this.isChartModalVisible = true; // 显示ECharts弹窗
          this.initChart(); // 初始化ECharts图表
          this.isImageSelectorVisible = true; // 点击分析按钮后展示“港口提取结果”窗体  // 成功提示
          console.log('文件夹存在，已加载 .tif 文件');
          return { success: true, message: '文件夹存在，已加载 .tif 文件' };
        } else {
          // 3. 如果文件夹不存在，调用后端的 main.py 进行处理
          console.log('文件夹不存在，正在调用 Python 脚本进行处理...');
          const result = await this.runMainPythonScript();
          return { success: true, message: '，已加载 .tif 文件' }; // 返回 Python 脚本的执行结果
        }
      } catch (error) {
        console.error('分析按钮点击时出错:', error);
        return { success: false, message: `出错: ${error.message}` };
      }
    },

    async checkFolderExists() {
      try {
        const response = await axios.get('http://localhost:3017/api/check_folder_Chabua');

        // 根据返回的数据格式进行判定
        if (response.data.files) {
          return true;  // 如果文件夹中有 .tif 文件
        } else if (response.data.error || response.data.message) {
          return false;  // 如果发生错误或没有找到文件
        }
      } catch (error) {
        console.error('检查文件夹是否存在时出错:', error);
        return false;  // 出现错误时认为文件夹不存在
      }
    },


    async runMainPythonScript() {
      try {
        // 开始执行时显示加载框
        this.isLoading = true;  // 显示加载框

        // 点击“分析”按钮时，先执行 main.py 生成 .tif 文件
        const response = await axios.get('http://localhost:3017/api/run_main_Chabua');
        console.log('返回消息:', response.data.message);  // 确认是否成功执行

        // 检查返回值
        if (response.data.message === "main.py 执行已启动") {
          // 等待文件夹生成并检查是否有 finish.txt 文件
          const isFinished = await this.checkFolderAndLoadFiles();

          if (isFinished) {
            console.log('执行成功，main.py 执行完成');
            // 执行完成后，继续后续的操作，如加载文件
            await this.fetchTiffFiles();
            // await this.loadSelectedTiff(); 
            this.isChartModalVisible = true; // 显示ECharts弹窗
            this.initChart(); // 初始化ECharts图表
            this.isImageSelectorVisible = true; // 点击分析按钮后展示“港口提取结果”窗体  // 成功提示
          } else {
            console.error('执行失败：没有找到 finish.txt 文件');
          }
        } else {
          console.error('执行失败:', response.data.message);
        }
      } catch (error) {
        console.error('分析执行失败:', error);
      } finally {
        // 执行完毕后隐藏加载框
        this.isLoading = false;  // 隐藏加载框
      }
    },



    checkFolderAndLoadFiles() {
      return new Promise((resolve, reject) => {
        const startTime = Date.now();  // 获取开始时间
        const timeLimit = 20 * 60 * 1000; // 20分钟的时间限制 (单位：毫秒)

        const intervalId = setInterval(async () => {
          try {
            // 检查是否超时
            if (Date.now() - startTime > timeLimit) {
              clearInterval(intervalId);  // 停止定时器
              console.log('时间已到，未找到 finish.txt 文件');
              resolve(false);  // 返回失败标志
              return;
            }

            // 尝试获取文件夹中的文件
            const response = await axios.get('http://localhost:3017/api/files_txt_Chabua');

            // 查找是否存在 finish.txt 文件
            const finishFile = response.data.files.find(file => file === "finish.txt");


            // 如果 finish.txt 文件存在，表示 main.py 执行完成
            if (finishFile) {
              clearInterval(intervalId);  // 停止定时器
              console.log('main.py 执行完成，文件夹中存在 finish.txt');
              resolve(true);  // 返回执行完成的标志
            }
          } catch (error) {
            console.error('获取文件列表时出错:', error);
          }
        }, 30000); // 每30秒检查一次
      });
    },





    async fetchTiffFiles() {
      try {
        const response = await axios.get('http://localhost:3017/api/files_Chabua');
        console.log('返回的数据:', response.data); // 确认返回的数据格式

        // 保存完整文件名和前8位文件名的映射
        this.tifFiles = response.data.files.map(file => ({
          fullName: file,  // 完整的文件名
          shortName: file.substring(0, 8)  // 文件名的前8位
        }));
        this.mark_dates = [] // 清空旧数据
        const files = toRaw(this.tifFiles)
        for (var i = 0; i < this.tifFiles.length; i++) {
          var file = files[i].fullName
          var year = file.substring(0, 4)
          var month = file.substring(4, 6)
          var day = file.substring(6, 8)
          this.mark_dates.push(new Date(year, month - 1, day))
        }
      } catch (error) {
        console.error("获取文件列表时出错:", error);
      }
    },



    async onDayClickHandler(day) {
      const selectedDate = ref(null);
      selectedDate.value = day.date;
      const year_str = day.year
      const month_str = ("0" + (day.month)).slice(-2)
      const day_str = ("0" + (day.day)).slice(-2)
      const date_str = `${year_str}${month_str}${day_str}`
      console.log('date_str:', date_str)
      const selectedTiff = this.tifFiles.filter(element => element.shortName == date_str)[0];
      if (selectedTiff) {
        const tiffUrl = `public/03_India_Airport/06_Chabua_Air_Force_Station/02_Output/${selectedTiff.fullName}`;  // 根据选择的完整文件名拼接 URL
        await this.loadTiffImage(tiffUrl);
      }
    },


    // async loadSelectedTiff() {
    //   try {
    //     // 假设 this.selectedTiff 存储了 TIFF 文件的文件名
    //     if (this.selectedTiff) {
    //       // 拼接完整的 URL 以指向后端提供的静态文件 xss
    //       const tiffUrl = `http://localhost:3017/api/files/${this.selectedTiff}`;
    //       console.log('TIFF file URL:', tiffUrl);

    //       await this.loadTiffImage(tiffUrl);  // 调用加载 TIFF 影像的方法
    //     } else {
    //       throw new Error("未选择 TIFF 文件");
    //     }
    //   } catch (error) {
    //     console.error("Error loading selected TIFF:", error);
    //   }
    // },




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

        const utmProjection = 'EPSG:32646'; //WGS_1984_UTN_Zone_46N
        const wgs84Projection = 'EPSG:4326';

        const lowerLeft = proj4(utmProjection, wgs84Projection, [bbox[0], bbox[1]]);
        const upperRight = proj4(utmProjection, wgs84Projection, [bbox[2], bbox[3]]);

        const minLon = lowerLeft[0];
        const minLat = lowerLeft[1];
        const maxLon = upperRight[0];
        const maxLat = upperRight[1];

        console.log("Converted Bounding box (WGS84):", [minLon, minLat, maxLon, maxLat]);

        // 确保影像是三波段的
        if (rasters.length < 3) {
          throw new Error("This TIFF image doesn't have 3 bands.");
        }

        const redBand = rasters[0];   // 第一个波段（红色）
        const greenBand = rasters[1]; // 第二个波段（绿色）
        const blueBand = rasters[2];  // 第三个波段（蓝色）

        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = width;
        canvas.height = height;

        const imageData = ctx.createImageData(width, height);
        for (let i = 0; i < redBand.length; i++) {
          // R、G、B 分别对应每个波段的数据
          imageData.data[i * 4] = redBand[i];     // Red channel
          imageData.data[i * 4 + 1] = greenBand[i];  // Green channel
          imageData.data[i * 4 + 2] = blueBand[i];   // Blue channel
          imageData.data[i * 4 + 3] = 255;       // Alpha channel (不透明)
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

          this.viewer.imageryLayers.addImageryProvider(imageryProvider);
        });
      } catch (error) {
        console.error("Error loading TIFF image:", error);
      }
    },

    // toggleSplit() {
    //   this.isSplit = !this.isSplit;
    //   this.$nextTick(() => {
    //     this.adjustLayout();
    //     if (this.isSplit && !this.chartInstance) {
    //       this.initChart();
    //     }
    //     // 点击分析按钮时加载.tif影像
    //     if (this.isSplit) {
    //       this.loadTiffImage();
    //     }
    //   });
    // },


    initChart() {
      decode_CSV("public/03_India_Airport/06_Chabua_Air_Force_Station/Chabua_Airport_Area.csv")
        .then(csv_data => {
          // 提取日期、面积（保留4位小数）和abnormal值
          const date_list = csv_data.map(item => item.date);
          // const area_list = csv_data.map(item => parseFloat(item.area).toFixed(4)); // 保留4位小数
          const area_list = csv_data.map(item => parseFloat(item.area).toFixed(0)); // 保留04位小数
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
          grid: {
            left: 80,  // 你可以试试 80、100 或更大，单位是像素
          },
          tooltip: {
            trigger: "axis",
            valueFormatter: function (value) {
              return value + " m²";
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
              name: '面积 (m²)',
              nameTextStyle: { fontSize: 18 },
              min: Math.min(...area_list) * 0.95,
              max: Math.max(...area_list) * 1.05,
              
              axisLabel: {
                formatter: (value) => value.toFixed(0),
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

/* 港口提取结果选择面板 */
.image-selector-box {
  position: absolute;
  top: 10px;
  left: 300px;

  background-color: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: auto;
  height: 300px;
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



/* Echart弹框的位置 */
.modal {
  display: flex;
  position: fixed;
  top: 410px;
  left: 310px;
  width: 500px;
  height: 450px;
  background-color: rgba(0, 0, 0, 0.5);

}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 10px;
}


#loading {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  /* 将元素居中 */
  padding: 20px;
  background-color: rgba(0, 0, 0, 0.7);
  /* 半透明背景 */
  color: white;
  font-size: 20px;
  border-radius: 5px;
  z-index: 9999;
  /* 确保 loading 层位于其他内容之上 */

}
</style>
