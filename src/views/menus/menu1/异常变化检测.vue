<template>
  <div>
    <div id="map" ref="mapContainer" style="width: 100%; height: 500px"></div>
    <div>
      <select v-model="selectedLayer">
        <option value="road:abnormal_bridge">桥梁异常检测</option>
        <option value="road:abnormal_buildings">建筑异常检测</option>
        <option value="road:abnormal_airport">机场设施异常检测</option>
      </select>
      <button @click="loadLayer">处理</button>
    </div>

    <!-- 进度条 -->
    <div v-if="isProcessing">
      <p>处理中：{{ progress }}%</p>
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
import { fromLonLat } from "ol/proj"; // 用于经纬度转换

export default {
  name: "GeoServerMap",
  data() {
    return {
      map: null, // 地图实例
      layers: {}, // 图层引用
      isProcessing: false, // 是否加载中
      progress: 0, // 进度值
      selectedLayer: "", // 默认未选中图层
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
              url: "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            }),
          }),
        ],
        view: new View({
          projection: "EPSG:3857",
          center: fromLonLat([75.27566966688369, 37.662625482855894]), // 转换为 Web Mercator 投影坐标
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

      if (this.layers[this.selectedLayer]) {
        alert(`${this.selectedLayer} 图层已经加载`);
        return;
      }

      // 判断加载的图层，如果是 "通达性" 或 "中巴公路安全态势" 才显示进度条
      if (
        this.selectedLayer === "road:2023tdx1" ||
        this.selectedLayer === "road:中巴公路500m"
      ) {
        this.isProcessing = true;
        this.progress = 0;

        let progressInterval = setInterval(() => {
          if (this.progress < 100) {
            this.progress += 20; // 加快进度更新速度，每次增加20%
          } else {
            clearInterval(progressInterval);
            this.isProcessing = false;
            this.addLayerToMap();
          }
        }, 300); // 缩短时间间隔，300ms更新一次
      } else {
        // 否则直接加载图层
        this.addLayerToMap();
      }
    },

    // 将图层添加到地图并设置视图定位和缩放
    addLayerToMap() {
      const layerName = this.selectedLayer;

      const wmsLayer = new TileLayer({
        source: new TileWMS({
          url: "http://localhost:13140/geoserver/road/wms",
          params: {
            LAYERS: layerName,
            SRS: "EPSG:3857",
            VERSION: "1.1.0",
            FORMAT: "image/png",
          },
        }),
      });

      this.layers[layerName] = wmsLayer;
      this.map.addLayer(wmsLayer);

      // 根据图层名设置定位和缩放范围
      let viewSettings = {};
      switch (layerName) {
        case "road:TJ_WGS84":
          viewSettings = {
            center: fromLonLat([75.27566966688369, 37.662625482855894]),
            zoom: 10,
          };
          break;
        case "road:abnormal_bridge":
          viewSettings = {
            center: fromLonLat([75.27566966688369, 37.662625482855894]),
            zoom: 12,
          };
          break;
        case "road:abnormal_buildings":
          viewSettings = {
            center: fromLonLat([75.27566966688369, 37.662625482855894]),
            zoom: 12,
          };
          break;
        case "road:abnormal_airport":
          viewSettings = {
            center: fromLonLat([75.27566966688369, 37.662625482855894]),
            zoom: 14,
          }; // 红其拉甫机场坐标
          break;
        default:
          viewSettings = {
            center: fromLonLat([75.27566966688369, 37.662625482855894]),
            zoom: 7.5,
          };
      }

      this.map.getView().animate({
        center: viewSettings.center,
        zoom: viewSettings.zoom,
        duration: 1000, // 动画持续时间，1秒
      });
    },

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
</style>
