<!-- @src/views/dashboard/加载天地图.vue -->
<template>
  <div id="cesiumContainer"></div>
</template>

<script setup>
import { onMounted, onUnmounted } from "vue";
import * as Cesium from "cesium";
import AMapLoader from "@amap/amap-jsapi-loader";
import { cesium_token } from "../../../my_package.json";

let cesium_viewer = null;

onMounted(async () => {
  Cesium.Ion.defaultAccessToken = cesium_token;

  var imageryViewModels = [];
  var tiandituyx = new Cesium.ProviderViewModel({
    name: "天地图影像",
    tooltip: "天地图影像及标注图层",
    iconUrl: "./sampleData/images/tianditu.jpg",
    creationFunction: function () {
      var mapsources = [];
      var yx = new Cesium.WebMapTileServiceImageryProvider({
        url: "http://t0.tianditu.com/img_w/wmts?service=wmts&request=GetTile&version=1.0.0&LAYER=img&tileMatrixSet=w&TileMatrix={TileMatrix}&TileRow={TileRow}&TileCol={TileCol}&style=default&format=tiles&tk=8b207a527da69c7a32f636801fa194d4",
        layer: "tdtBasicLayer",
        style: "default",
        format: "image/jpeg",
        tileMatrixSetID: "GoogleMapsCompatible",
        show: false,
      });
      var jd = new Cesium.WebMapTileServiceImageryProvider({
        url: "http://t0.tianditu.gov.cn/cia_w/wmts?service=wmts&request=GetTile&version=1.0.0&LAYER=cia&tileMatrixSet=w&TileMatrix={TileMatrix}&TileRow={TileRow}&TileCol={TileCol}&style=default&format=tiles&tk=8b207a527da69c7a32f636801fa194d4",
        layer: "tiandituImgMarker",
        style: "default",
        format: "image/jpeg",
        tileMatrixSetID: "tiandituImgMarker",
        show: true,
        maximumLevel: 16,
      });
      mapsources.push(yx, jd);
      return mapsources;
    },
  });
  imageryViewModels.push(tiandituyx);
  var tianditujd = new Cesium.ProviderViewModel({
    name: "天地图街道",
    tooltip: "天地图街道图层",
    iconUrl: "./sampleData/images/tianditu.jpg",
    creationFunction: function () {
      return new Cesium.WebMapTileServiceImageryProvider({
        url: "http://t0.tianditu.com/vec_w/wmts?service=wmts&request=GetTile&version=1.0.0&LAYER=vec&tileMatrixSet=w&TileMatrix={TileMatrix}&TileRow={TileRow}&TileCol={TileCol}&style=default&format=tiles&tk=8b207a527da69c7a32f636801fa194d4",
        layer: "tdtVecBasicLayer",
        style: "default",
        format: "image/jpeg",
        tileMatrixSetID: "GoogleMapsCompatible",
        show: false,
      });
    },
  });
  imageryViewModels.push(tianditujd);
  var tiandituzj = new Cesium.ProviderViewModel({
    name: "天地图标注",
    tooltip: "天地图标注图层",
    iconUrl: "./sampleData/images/tianditu.jpg",
    creationFunction: function () {
      return new Cesium.WebMapTileServiceImageryProvider({
        url: "http://t0.tianditu.gov.cn/cia_w/wmts?service=wmts&request=GetTile&version=1.0.0&LAYER=cia&tileMatrixSet=w&TileMatrix={TileMatrix}&TileRow={TileRow}&TileCol={TileCol}&style=default&format=tiles&tk=8b207a527da69c7a32f636801fa194d4",
        layer: "tiandituImgMarker",
        style: "default",
        format: "image/jpeg",
        tileMatrixSetID: "tiandituImgMarker",
        show: true,
        maximumLevel: 16,
      });
    },
  });
  imageryViewModels.push(tiandituzj);
  var tianditugjx = new Cesium.ProviderViewModel({
    name: "天地图国界线",
    tooltip: "天地图国界线数据",
    iconUrl: "./sampleData/images/tianditu.jpg",
    creationFunction: function () {
      return new Cesium.WebMapTileServiceImageryProvider({
        url: "https://t0.tianditu.gov.cn/ibo_w/wmts?service=wmts&request=GetTile&version=1.0.0&LAYER=ibo&tileMatrixSet=w&TileMatrix={TileMatrix}&TileRow={TileRow}&TileCol={TileCol}&style=default&format=tiles&tk=8b207a527da69c7a32f636801fa194d4",
        layer: "tiandituImg",
        style: "default",
        format: "image/jpeg",
        tileMatrixSetID: "tiandituImg",
        show: true,
        maximumLevel: 16,
      });
    },
  });
  imageryViewModels.push(tianditugjx);

  cesium_viewer = new Cesium.Viewer("cesiumContainer", {
    baseLayerPicker: true, //是否显示图层选择器
    imageryProviderViewModels: imageryViewModels,
    selectedImageryProviderViewModel: tianditujd,
  });
  cesium_viewer.imageryLayers.removeAll();
  cesium_viewer.cesiumWidget.screenSpaceEventHandler.removeInputAction(
    Cesium.ScreenSpaceEventType.LEFT_CLICK
  );
  cesium_viewer.cesiumWidget.screenSpaceEventHandler.removeInputAction(
    Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK
  );

  // viewer.terrainProvider = await Cesium.createWorldTerrainAsync({
  //   requestVertexNormals: true,
  //   requestWaterMask: true,
  // }); // 加入地形和水纹.
  // viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider({}); // 普通底图
  // viewer.imageryLayers.remove(viewer.imageryLayers.get(0)); // 去掉初始图层
  // viewer.baseLayerPicker.viewModel.imageryProviderViewModels = [];

  // 获取图层选择器中的图层
  var imageryLayers =
    cesium_viewer.baseLayerPicker.viewModel.imageryProviderViewModels;

  // // 打印每个图层的所有属性
  // imageryLayers.forEach(function (layer) {
  //   console.log(layer); // 直接输出对象查看所有属性
  // });

  // // 打印当前选中的图层的所有属性
  // var selectedLayer = viewer.baseLayerPicker.viewModel.selectedImagery;
  // console.log(selectedLayer); // 直接输出对象查看所有属性
});

onUnmounted(() => {
  cesium_viewer?.destroy();
});
</script>

<style scoped>
#container {
  width: 100%;
  height: 800px;
}
</style>

<style scoped>
#cesiumContainer {
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>
