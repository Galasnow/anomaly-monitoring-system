<template>
  <div id="app">
    <div class="container">
      <!-- 高德地图 -->
      <div class="section">
        <h2>评论IP发布地址地图</h2>
        <div id="container" style="height: 600px"></div>
      </div>

      <!-- 数据爬取 -->
      <div class="section" style="padding-bottom: 20px; overflow: hidden">
        <h2>爬取指定文章</h2>
        <div
          class="spider"
          v-loading="loading"
          element-loading-text="请稍等，数据正在爬取中..."
          style="overflow: auto; height: 300px"
        >
          <!-- 新增的爬取内容 -->
          <div class="crawler">
            <input
              v-model="keyword"
              type="text"
              placeholder="请输入关键词"
              class="url-input"
            />
            页码：
            <input
              style="width: 80px"
              v-model="page"
              type="number"
              class="url-input"
            />

            <button
              @click="startCrawl"
              class="crawl-button"
              style="margin-left: 20px"
            >
              开始爬取
            </button>
            <div v-if="data">
              <h2>爬取的内容：</h2>
              <p v-for="(item, index) in data" :key="index">{{ item }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 词云图 -->
      <div class="section">
        <h2
          style="
            display: flex;
            justify-content: space-between;
            padding-right: 20px;
          "
        >
          词云图
        </h2>
        <div class="word-cloud" style="height: auto">
          <div
            class="word-cloud-controls"
            v-loading="loading"
            element-loading-text="请稍等，数据正在爬取中..."
            style="
              display: flex;
              justify-content: center;
              height: auto;
              min-height: 400px;
            "
          >
            <!-- 添加图片显示区域 -->
            <img
              v-if="wordCloudSrc"
              :src="wordCloudSrc"
              alt="Generated Word Cloud"
              style="width: 600px;height: 500px;margin: 0'
           ;"
            />
          </div>
        </div>
      </div>

      <!-- 饼图 -->
      <div class="section">
        <h2>情感占比</h2>
        <div class="pie-chart">
          <div
            class="word-cloud-controls"
            v-loading="loading"
            element-loading-text="请稍等，数据正在爬取中..."
            style="
              display: flex;
              justify-content: center;
              height: auto;
              min-height: 400px;
            "
          >
            <!-- 添加图片显示区域 -->
            <img
              v-if="motionSrc"
              :src="motionSrc"
              alt="Generated Word Cloud"
              style="width: 600px;height: 400px;margin: 0'
           ;"
            />
          </div>
        </div>
      </div>

      <!-- 预警任务 -->
      <div class="section">
        <h2>预警任务</h2>
        <div class="predict">
          <v-chart :options="wordCloudOptions" style="height: 400px" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import AMapLoader from "@amap/amap-jsapi-loader";
import { Amap_security_Code, Amap_key } from "../../../../my_package.json";
import axios from "axios";

let map = null;
const loading = ref(false);

const page = ref(1);
const wordCloudSrc = ref("");
const motionSrc = ref("");
onMounted(() => {
  window._AMapSecurityConfig = {
    securityJsCode: Amap_security_Code,
  };
  AMapLoader.load({
    key: Amap_key, // 申请好的Web端开发者Key，首次调用 load 时必填
    version: "2.0", // 指定要加载的 JSAPI 的版本，缺省时默认为 1.4.15
    plugins: ["AMap.Scale"], //需要使用的的插件列表，如比例尺'AMap.Scale'，支持添加多个如：['...','...']
    // Loca: { version: "2.0.0" }, // 是否加载 Loca， 缺省不加载, Loca 版本，缺省 1.3.2
  })
    .then((AMap) => {
      //1.初始化地图
      map = new AMap.Map("container", {
        // 设置地图容器id
        viewMode: "3D", // 是否为3D地图模式
        zoom: 4.1, // 初始化地图级别
        layers: [new AMap.TileLayer.Satellite(), new AMap.TileLayer.RoadNet()], //添加卫星图图层和路网图层
        center: [107.3384, 33.4], // 初始化地图中心点位置
      });

      // TODO:绘制边境线
      //2.创建国家简易行政区图层
      var distCountry = new AMap.DistrictLayer.Country({
        SOC: "CHN", //设置显示国家
        depth: 0, //设置数据显示层级，0：显示国家面，1：显示省级，当国家为中国时设置depth为2的可以显示市一级
        zIndex: 10, //设置图层层级
        opacity: 1, //图层透明度
        zooms: [2, 20], //设置图层显示范围
      });

      //3.设置行政区图层样式
      distCountry.setStyles({
        "stroke-width": 4, //描边线宽
        "coastline-stroke": [0.18, 0.63, 0.94, 0.4], //海岸线颜色
        "nation-stroke": "af70cd", //国境线颜色
        "province-stroke": [1, 1, 1, 0], //省界颜色

        fill: function (data) {
          //设置区域填充颜色，可根据回调信息返回区域信息设置不同填充色
          //回调返回区域信息数据，字段包括 SOC(国家代码)、NAME_ENG(英文名称)、NAME_CHN(中文名称)等
          //国家代码名称说明参考 https://a.amap.com/jsapi_demos/static/demo-center/js/soc-list.json
          return [1, 1, 1, 0];
        },
      });

      //4.将简易行政区图层添加到地图
      map.add(distCountry);

      //异步加载 AMap.GeoJSON 插件，该插件用于解析和渲染 GeoJSON 数据
      AMap.plugin("AMap.GeoJSON", function () {
        //创建 geoJSON 实例，传入 GeoJSON 数据和其他选项
        var geoJson = new AMap.GeoJSON({
          //将字符串形式的 GeoJSON 数据解析为对象
          geoJSON: South_China_Sea,
          //定义一个回调函数来创建多边形对象，该函数接收一个 geojson 对象和一个 lnglats 数组作为参数
          getPolygon: function (geojson, lnglats) {
            // 返回一个新的 AMap.Polygon 对象，传入路径、填充透明度、边框颜色和填充颜色等选项
            //还可以自定义 getMarker 和 getPolyline，用于创建标记和折线对象
            return new AMap.Polygon({
              path: lnglats,
              fillOpacity: 0.1,
              strokeColor: "red",
              fillColor: "red",
              strokeWeight: 3.5,
            });
          },
        });
        //将geoJson对象添加到地图上
        map.add(geoJson);
      });

      // 加载WMS图层
      var wms = new AMap.TileLayer.WMS({
        url: "http://127.0.0.1:13140/geoserver/_menu3/wms", //此处修改为你的地址
        blend: true,
        blend: true,
        tileSize: 256,
        params: {
          LAYERS: "_menu3:ZB-DEM", //此处修改为你的图层名称
          VERSION: "1.1.0",
          // STYLES: "style1", // 指定样式名称
        },
      });

      //显示WMS图层
      wms.setMap(map);
    })
    .catch((e) => {
      console.log(e);
    });
});

onUnmounted(() => {
  map?.destroy();
});

// 变量定义
const keyword = ref(""); // 用户输入的关键词
//const url = ref(""); // 用户输入的网址
const data = ref(null); // 爬取的内容
const crawlLoading = ref(false); // 爬取状态
const crawlError = ref(""); // 爬取错误信息
const crawlSuccess = ref(""); // 爬取成功信息

// 词云图配置
const wordCloudOptions = ref({
  tooltip: {},
  series: [
    {
      type: "wordCloud",
      gridSize: 8,
      sizeRange: [12, 60],
      rotationRange: [-90, 90],
      shape: "circle",
      textStyle: {
        normal: {
          color: () =>
            `rgb(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255})`,
        },
      },
      data: [], // 初始化为空
    },
  ],
});

// 饼图配置
const pieChartOptions = ref({
  tooltip: {
    trigger: "item",
  },
  series: [
    {
      name: "情感分析",
      type: "pie",
      radius: "50%",
      data: [], // 初始化为空
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: "rgba(0, 0, 0, 0.5)",
        },
      },
    },
  ],
});

// 开始爬取函数
const startCrawl = async () => {
  if (!keyword.value) {
    crawlError.value = "请输入关键词";
    crawlSuccess.value = ""; // 清空成功信息
    return;
  }
  loading.value = true;
  crawlLoading.value = true;
  crawlError.value = "";
  crawlSuccess.value = "";
  data.value = null;

  try {
    const response = await axios.get(
      `http://127.0.0.1:8989/api/v1/spider/startSpider/${keyword.value}/${page.value}`
    );

    const result = response.data;
    if (result.data.length > 0) {
      loading.value = false;
      alert("爬取完毕");
    }
    console.log(result);
    data.value = result.data; // 爬取的主要内容

    const response_2 = await axios.get(
      `http://127.0.0.1:8989/api/v1/spider/wordCloud/${keyword.value}`
    );

    const result_2 = response_2.data;
    console.log(result_2);
    updateWordCloud(result_2.data[0]); // 动态更新词云图

    const response_3 = await axios.get(
      `http://127.0.0.1:8989/api/v1/spider/motion/${keyword.value}`
    );
    const result_3 = response_3.data;
    updatePieChart(result_3.data[0]); // 动态更新饼图

    console.log(result_3);
  } catch (err) {
    crawlError.value =
      "爬取失败：" + (err.response?.data?.error || err.message);
  } finally {
    crawlLoading.value = false;
  }
};

// 更新词云图
const updateWordCloud = (keywords) => {
  wordCloudSrc.value = "http://127.0.0.1:13140/localdata/temp/" + keywords;
};

// 更新饼图
const updatePieChart = function (keywords) {
  motionSrc.value = "http://127.0.0.1:13140/localdata/temp/" + keywords;
};
</script>

<style scoped>
.container {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: space-between;
  padding: 20px;
}

.section {
  width: 100%;
  padding: 10px;
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.map-container {
  width: 100%;
  height: 400px;
  border-radius: 10px;
}

.spider {
  width: 100%;
  height: 100px;
  border-radius: 10px;
}

.word-cloud,
.pie-chart,
.predict {
  width: 100%;
  height: 400px;
  border-radius: 10px;
}

.crawler {
  margin-top: 20px;
}

.url-input {
  font-size: 18px; /* 放大字体 */
  padding: 10px; /* 增加内边距 */
  width: 100%; /* 让输入框宽度充满父容器 */
  max-width: 600px; /* 最大宽度限制 */
  margin-bottom: 10px; /* 输入框和按钮之间的间距 */
  border: 1px solid #ccc; /* 边框颜色 */
  border-radius: 5px; /* 圆角边框 */
}

.crawl-button {
  font-size: 18px; /* 放大字体 */
  padding: 12px 20px; /* 增加内边距 */
  background-color: #007bff; /* 按钮背景色 */
  color: white; /* 按钮字体颜色 */
  border: none; /* 去掉按钮边框 */
  border-radius: 5px; /* 圆角按钮 */
  cursor: pointer; /* 鼠标悬停时显示手指图标 */
  width: auto; /* 自动调整宽度 */
  max-width: 600px; /* 最大宽度限制 */
}

.crawl-button:hover {
  background-color: #0056b3; /* 鼠标悬停时的背景颜色 */
}

.error-message {
  color: red;
  margin-top: 10px;
}

.success-message {
  color: green;
  margin-top: 10px;
}

.word-cloud-controls {
  margin-top: 20px;
}

.path-input {
  font-size: 16px;
  padding: 10px;
  width: 100%;
  max-width: 400px;
  margin-right: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

.generate-button {
  font-size: 16px;
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.generate-button:hover {
  background-color: #0056b3;
}
</style>
