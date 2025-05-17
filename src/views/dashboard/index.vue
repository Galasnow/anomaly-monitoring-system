<template>
  <div id="cesiumContainer"></div>
</template>

<script setup>
import { onMounted, onUnmounted } from "vue";
import * as Cesium from "cesium";
import { cesium_token } from "../../../my_package.json";

let cesium_viewer = null;

onMounted(async () => {
  document.body.style.overflow = "hidden"; // 禁用滚动条
  Cesium.Ion.defaultAccessToken = cesium_token;
  cesium_viewer = new Cesium.Viewer("cesiumContainer", {
    animation: false, // 是否打开创建动画小控件，即左下角的仪表
    baseLayerPicker: false, // 是否显示图层选择器
    fullscreenButton: false, // 是否显示全屏按钮
    geocoder: false, // 是否显示Geocoder(右上角的查询按钮)
    homeButton: false, // 是否显示Home按钮
    infoBox: false, // 是否显示信息框
    maximumRenderTimeChange: Infinity, // 请求新帧的时间
    navigationHelpButton: false, // 是否显示右上角帮助按钮
    navigationInstructionsInitiallyVisible: false, //是否显示帮助信息
    requestRenderMode: false, // 显式渲染，渲染优化
    orderIndependentTranslucency: false, // 设置背景透明
    sceneMode: Cesium.SceneMode.SCENE3D, //3d视角展示
    sceneModePicker: false, // 是否显示三维地球/二维地图选择器
    selectionIndicator: false, // 是否显示选取指示器
    shadows: false, //光照的阴影效果
    shouldAnimate: true, //执行模型动画
    showRenderLoopErrors: false, // 是否显示渲染错误
    timeline: false, // 是否关闭时间轴
    vrButton: false, // 是否显示VR控件

    // terrainProvider: await Cesium.createWorldTerrainAsync({
    //   requestVertexNormals: true,
    //   requestWaterMask: true,
    // }), // 展示地形和水纹
  });

  cesium_viewer.cesiumWidget.creditContainer.style.display = "none"; // 隐藏logo和版权信息
  // cesium_viewer.scene.globe.enableLighting = true; //启用使用场景光源照亮地球
  // cesium_viewer.clock.currentTime = Cesium.JulianDate.now(); // 设置时间（可选）以影响光照
  // cesium_viewer.clock.multiplier = 1000; // 时间流逝的倍数，可以加快显示昼夜交替

  // cesium_viewer.camera.flyTo({ // 飞行至指定经纬度和高度
  //   destination: Cesium.Cartesian3.fromDegrees(116.4, 39.9, 20000000), //经纬度和高度
  // });

  // 设置旋转的初始参数
  let longitude = 108;
  const rotateSpeed = 0.1; // 设置旋转速度（每帧移动的经度）

  // 定义旋转函数
  function rotateEarth(isRotating) {
    // 检查cesium视图是否被销毁, 或者接到停止旋转命令
    if (!isRotating || !cesium_viewer) {
      console.warn(
        "Cesium Viewer has been destroyed or rotation has been stopped."
      );
      return;
    }

    // 更新经度，使地球不断旋转
    longitude += rotateSpeed;
    if (longitude >= 360) {
      longitude -= 360;
    }

    // 更新摄像机的视角位置
    cesium_viewer.scene.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(longitude, 30, 20000000), // 设置摄像机位置（高度可根据需要调整）
    });

    // 使用 requestAnimationFrame 递归调用来持续旋转
    requestAnimationFrame(() => rotateEarth(isRotating));
  }

  // 开始旋转
  rotateEarth(true);
});

onUnmounted(() => {
  cesium_viewer?.destroy();

  cesium_viewer = null;
});
</script>

<style scoped>
.app-container {
  width: 100%;
  height: 100vh;
  margin: 0;
  padding: 0;
  position: relative;
}

/** 开启tag标签  */
/* .hasTagsView {
  #cesiumContainer {
    height: 100%;
    margin: 0;
    padding: 0;
    width: 100%;
  }
} */

#cesiumContainer {
  width: 100%;
  height: 100%;
  position: absolute;
  pointer-events: none; /* 禁用所有鼠标事件 */
}

.el-scrollbar {
  overflow: hidden; /* 禁用滚动条 */
}
</style>
