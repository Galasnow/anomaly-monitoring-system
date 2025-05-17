<!-- @src/views/dashboard/加载本地wms服务.vue -->
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
  cesium_viewer = new Cesium.Viewer("cesiumContainer", {
    animation: false, // 是否打开创建动画小控件，即左下角的仪表
    baseLayerPicker: true, // 是否显示图层选择器
    fullscreenButton: false, // 是否显示全屏按钮
    geocoder: true, // 是否显示Geocoder(右上角的查询按钮)
    homeButton: true, // 是否显示Home按钮
    infoBox: true, // 是否显示信息框
    orderIndependentTranslucency: false, // 设置背景透明
    sceneModePicker: true, // 是否显示三维地球/二维地图选择器
    selectionIndicator: true, // 是否显示选取指示器
    shouldAnimate: true, //执行模型动画
    showRenderLoopErrors: false, // 是否显示渲染错误
    timeline: false, // 是否关闭时间线
    navigationHelpButton: false, // 帮助提示按钮
    navigationInstructionsInitiallyVisible: false, //是否显示帮助信息控件
  });
  cesium_viewer.scene.frameState.creditDisplay.container.style.display = "none"; // 隐藏logo和版权信息

  // viewer.scene.globe.enableLighting = true; //启用使用场景光源照亮地球
  // viewer.clock.currentTime = Cesium.JulianDate.now(); // 设置时间（可选）以影响光照
  // viewer.clock.multiplier = 1000; // 时间流逝的倍数，可以加快显示昼夜交替

  // viewer.terrainProvider = await Cesium.createWorldTerrainAsync({
  //   requestVertexNormals: true,
  //   requestWaterMask: true,
  // }); // 加入地形和水纹.
  // viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider({}); // 普通底图
  // viewer.imageryLayers.remove(viewer.imageryLayers.get(0)); // 去掉初始图层
  cesium_viewer.baseLayerPicker.viewModel.imageryProviderViewModels = [];

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

  var provider = new Cesium.WebMapServiceImageryProvider({
    // 创建一个图层
    url: "http://127.0.0.1:13140/geoserver/satellitevisibility/",
    layers: "satellitevisibility:ZB-DEM",
    parameters: {
      service: "WMS",
      version: "1.1.1",
      request: "GetMap",
      format: "image/png",
      transparent: true, // 确保设置透明
      srs: "EPSG:4326", // 或者使用CRS
    },
  });
  cesium_viewer.imageryLayers.addImageryProvider(provider);
  cesium_viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(76.0, 36.5, 1000000), //经纬度和高度
  });
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
