<template>
  <div>
    <div id="map" ref="mapContainer" style="width: 100%; height: 500px"></div>

    <!-- 影响因素选择按钮 -->
    <div>
      <button @click="toggleImpactFactors">道路安全态势要素</button>
    </div>

    <!-- 影响因素选择滑动窗口 -->
    <transition name="slide-fade">
      <div v-show="isImpactFactorsVisible" class="impact-factors-container">
        <select v-model="selectedImpactFactors" multiple>
          <option value="road:TJ_WGS84">塔县</option>
          <option value="road:一级公路">一级公路</option>
          <option value="road:二级公路">二级公路</option>
          <option value="road:三级公路">三级公路</option>
          <option value="road:四级公路">四级公路</option>
          <option value="road:地震">地震</option>
          <option value="road:孤立建筑">孤立建筑</option>
          <option value="road:滑坡">滑坡</option>
          <option value="road:交通站点">交通站点</option>
          <option value="road:居民点">居民点</option>
          <option value="road:泥石流">泥石流</option>
          <option value="road:桥隧">桥隧</option>
          <option value="road:塔">塔</option>
        </select>
        <button @click="loadImpactFactors">加载选定影响因素</button>
      </div>
    </transition>

    <!-- 图层选择 -->
    <div>
      <select v-model="selectedLayer">
        <option value="road:ZB_TDX">通达性</option>
        <option value="road:road_anquan">中巴公路安全态势</option>
      </select>
      <button @click="loadLayer">处理</button>
    </div>

    <!-- 进度条 -->
    <div v-if="isProcessing">
      <p>{{ progressTitle }}</p>
      <!-- 动态显示标题 -->
      <progress :value="progress" max="100"></progress>
    </div>
  </div>
</template>

<script>
import "ol/ol.css";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import XYZ from "ol/source/XYZ";
import TileWMS from "ol/source/TileWMS";

export default {
  name: "GeoServerMap",
  data() {
    return {
      map: null, // 地图实例
      layers: {}, // 图层引用
      isProcessing: false, // 是否加载中
      progress: 0, // 进度值
      progressTitle: "", // 进度条标题
      selectedLayer: "", // 默认未选中图层
      selectedImpactFactors: [], // 选择的影响因素（多个）
      isImpactFactorsVisible: false, // 影响因素选择滑动窗口是否显示
    };
  },
  mounted() {
    this.initializeMap();
  },
  beforeUnmount() {
    this.cleanupMap();
  },
  methods: {
    // 初始化地图
    initializeMap() {
      if (this.map) return;

      this.map = new Map({
        target: this.$refs.mapContainer,
        layers: [
          new TileLayer({
            source: new XYZ({
              url: `https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`,
            }),
          }),
        ],
        view: new View({
          projection: "EPSG:3857", // Google Earth 使用 EPSG:3857 投影
          center: [8375779, 4387623], // 新疆喀什塔县地区中心坐标 (EPSG:3857)
          zoom: 7.5,
        }),
      });
    },

    // 单一按钮加载图层
    loadLayer() {
      if (this.selectedLayer === "") {
        alert("请选择一个图层");
        return;
      }

      // 每次都重新加载图层
      this.isProcessing = true;
      this.progressTitle = "处理中"; // 设置为 "处理中"
      this.progress = 0;

      let progressInterval = setInterval(() => {
        if (this.progress < 100) {
          this.progress += 20; // 加快进度更新速度，每次增加20%
        } else {
          clearInterval(progressInterval);
          this.isProcessing = false;
          this.addLayerToMap(this.selectedLayer); // 加载图层
        }
      }, 300); // 缩短时间间隔，300ms更新一次
    },

    // 加载图层并添加到地图
    addLayerToMap(layerName) {
      const wmsLayer = new TileLayer({
        source: new TileWMS({
          url: "http://localhost:13140/geoserver/road/wms",
          params: {
            LAYERS: layerName,
            SRS: "EPSG:3857", // 确保与地图投影匹配
            VERSION: "1.1.0",
            FORMAT: "image/png",
          },
          serverType: "geoserver", // 添加服务器类型
        }),
      });

      // 每次都覆盖原有图层，不判断是否已经加载
      this.layers[layerName] = wmsLayer;
      this.map.addLayer(wmsLayer);
    },

    // 加载多个影响因素图层
    loadImpactFactors() {
      if (this.selectedImpactFactors.length === 0) {
        alert("请选择至少一个影响因素");
        return;
      }

      this.isProcessing = true;
      this.progressTitle = "加载中"; // 设置为 "加载中"
      this.progress = 0;

      let progressInterval = setInterval(() => {
        if (this.progress < 100) {
          // 根据选择的影响因素数目动态增加进度
          this.progress += Math.floor(100 / this.selectedImpactFactors.length);
        } else {
          clearInterval(progressInterval);
          this.isProcessing = false;
          this.addImpactLayers(); // 加载影响因素图层
        }
      }, 300); // 缩短时间间隔，300ms更新一次
    },

    // 添加影响因素图层到地图
    addImpactLayers() {
      this.selectedImpactFactors.forEach((factor) => {
        const wmsLayer = new TileLayer({
          source: new TileWMS({
            url: "http://localhost:13140/geoserver/road/wms",
            params: {
              LAYERS: factor,
              SRS: "EPSG:3857", // 投影系统需匹配 Google Earth
              VERSION: "1.1.0",
              FORMAT: "image/png",
            },
            serverType: "geoserver", // 添加服务器类型
          }),
        });

        // 每次都覆盖原有图层，不判断是否已经加载
        this.layers[factor] = wmsLayer;
        this.map.addLayer(wmsLayer);
      });
    },

    // 切换影响因素选择滑动窗口的显示状态
    toggleImpactFactors() {
      this.isImpactFactorsVisible = !this.isImpactFactorsVisible;
    },

    // 清理地图实例
    cleanupMap() {
      if (this.map) {
        this.map.setTarget(null);
      }
    },
  },
};
</script>

<style scoped>
#map {
  width: 100%;
  height: 500px;
}

/* 滑动窗口的样式 */
.impact-factors-container {
  margin-top: 20px;
  padding: 10px;
  background-color: #f9f9f9;
  border: 1px solid #ccc;
  border-radius: 5px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition:
    transform 0.5s ease-in-out,
    opacity 0.5s ease-in-out;
}

.slide-fade-enter,
.slide-fade-leave-to {
  transform: translateY(-20px);
  opacity: 0;
}
</style>
