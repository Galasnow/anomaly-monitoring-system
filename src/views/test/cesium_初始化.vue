<!-- @src/views/dashboard/cesium初始化.vue -->
<template>
  <div id="cesiumContainer"></div>
</template>

<script setup>
import { onMounted, onUnmounted } from "vue";
import * as Cesium from "cesium";
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
    maximumRenderTimeChange: Infinity, // 请求新帧的时间
    navigationHelpButton: false, // 是否显示右上角帮助按钮
    navigationInstructionsInitiallyVisible: false, //是否显示帮助信息
    requestRenderMode: true, // 显式渲染，渲染优化
    orderIndependentTranslucency: false, // 设置背景透明
    sceneMode: Cesium.SceneMode.SCENE3D, //3d视角展示
    sceneModePicker: true, // 是否显示三维地球/二维地图选择器

    selectionIndicator: true, // 是否显示选取指示器
    shadows: true, //光照的阴影效果
    shouldAnimate: true, //执行模型动画
    showRenderLoopErrors: false, // 是否显示渲染错误
    timeline: false, // 是否关闭时间轴
    vrButton: false, // 是否显示VR控件

    // 无效果?
    // imageryProvider: new Cesium.ArcGisMapServerImageryProvider({
    //   url: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer",
    // }), // 默认加载arcgis在线地图

    // terrainProvider: await Cesium.createWorldTerrainAsync({
    //   requestVertexNormals: true,
    //   requestWaterMask: true,
    // }), // 展示地形和水纹
  });
  cesium_viewer.scene.frameState.creditDisplay.container.style.display = "none"; // 方案1:隐藏logo和版权信息
  // cesium_viewer.cesiumWidget.creditContainer.style.display = "none"; // 方案2:去cesium logo水印

  // 设置光照和昼夜交替
  {
    cesium_viewer.scene.globe.enableLighting = true; //启用使用场景光源照亮地球
    cesium_viewer.clock.currentTime = Cesium.JulianDate.now(); // 设置时间（可选）以影响光照
    cesium_viewer.clock.multiplier = 1000; // 时间流逝的倍数，可以加快显示昼夜交替
  }

  cesium_viewer.scene.setTerrainExaggeration(2.0); // 地形夸张
  cesium_viewer.scene.primitives.add(Cesium.createOsmBuildings()); // 建筑osm
  cesium_viewer.scene.globe.depthTestAgainstTerrain = true; //深度检测
  cesium_viewer.scene.screenSpaceCameraController.maximumZoomDistance = 40000000; //最大缩放高度
  cesium_viewer.scene.screenSpaceCameraController.minimumZoomDistance = 1000; // 最小缩放高度

  // 清空地图选择器
  // viewer.baseLayerPicker.viewModel.imageryProviderViewModels = [];

  // 动态更换图层选择器中的图层，在此为Arcgis卫星图层
  // cesium_viewer.baseLayerPicker.viewModel.selectedImagery =
  //   cesium_viewer.baseLayerPicker.viewModel.imageryProviderViewModels[3];

  // 获取图层选择器中的图层
  // var imageryLayers0 =
  //   cesium_viewer.baseLayerPicker.viewModel.imageryProviderViewModels;
  // 获取当前选择的图层
  // var selectedLayer = viewer.baseLayerPicker.viewModel.selectedImagery;

  // 打印每个图层的所有属性
  // imageryLayers0.forEach(function (layer) {
  //   console.log(layer);
  // });

  // viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider({}); // 普通底图
  // viewer.imageryLayers.remove(viewer.imageryLayers.get(0)); // 去掉初始图层

  const tileset = Cesium.createOsmBuildings({
    style: new Cesium.Cesium3DTileStyle({
      color: {
        conditions: [
          //为不同类型建筑设置渲染color
          ["${feature['building']} === 'hospital'", "color('purple', 0.9)"],
          ["${feature['building']} === 'school'", "color('red', 0.9)"],
          [
            "${feature['building']} === 'apartments'",
            "color('CHARTREUSE', 0.9)",
          ],
          ["${feature['building']} === 'residential'", "color('cyan', 0.9)"],
          [
            "${feature['building']} === 'office'",
            "color('MEDIUMSLATEBLUE', 0.9)",
          ],
          ["${feature['building']} === 'commercial'", "color('yellow', 0.9)"],
          [true, "color('#orange')"],
          //为不同高度建筑设置渲染color
          // ['${Height} >= 100', 'color("purple", 0.5)'],
          // ['${Height} >= 50', 'color("red")'],
          // ['true', 'color("blue")']
        ],
      },
    }),
  }); // 建筑osm
  scene.primitives.add(tileset);
});

onUnmounted(() => {
  cesium_viewer?.destroy();
});
</script>

<style scoped>
#cesiumContainer {
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>
