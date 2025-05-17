<template>
  <div id="cesiumContainer"></div>
</template>

<script setup>
import { onMounted, onUnmounted } from "vue";
import * as Cesium from "cesium";
import { cesium_token } from "../../../my_package.json";

let cesium_viewer = null;
let minR1 = 4000; // 初始化圆的半径
let minR2 = 4000; // 初始化圆的半径
const deviationR = 2000; // 每次增加的大小
const maxR = 400000; // 最大半径

// 动态更新圆半径的函数
function changeRadius1() {
  minR1 += deviationR;
  if (minR1 >= maxR) {
    minR1 = 4000; // 重置半径
  }
  return minR1;
}

// 动态更新圆半径的函数
function changeRadius2() {
  minR2 += deviationR;
  if (minR2 >= maxR) {
    minR2 = 4000; // 重置半径
  }
  return minR2;
}

onMounted(async () => {
  Cesium.Ion.defaultAccessToken = cesium_token;
  cesium_viewer = new Cesium.Viewer("cesiumContainer");
  cesium_viewer.scene.frameState.creditDisplay.container.style.display = "none"; // 隐藏版权信息

  const position = Cesium.Cartesian3.fromDegrees(76.0, 36.5);

  // 分别为长半轴和短半轴创建独立的 CallbackProperty
  const dynamicSemiMajorAxis = new Cesium.CallbackProperty(() => {
    const radius = changeRadius1(); // 长半轴
    return radius; // 返回动态长半轴
  }, false);

  const dynamicSemiMinorAxis = new Cesium.CallbackProperty(() => {
    const radius = changeRadius2(); // 短半轴
    return radius; // 返回动态短半轴
  }, false);

  // 动态颜色需要一个有效的 MaterialProperty
  const dynamicColor = new Cesium.ColorMaterialProperty(
    new Cesium.CallbackProperty(() => {
      const alpha = 1 - minR1 / maxR; // 动态透明度
      return Cesium.Color.BLUE.withAlpha(alpha);
    }, false)
  );

  cesium_viewer.entities.add({
    position: position,
    name: "动态圆形",
    ellipse: {
      semiMajorAxis: dynamicSemiMajorAxis, // 使用独立的动态长半轴
      semiMinorAxis: dynamicSemiMinorAxis, // 使用独立的动态短半轴
      material: dynamicColor, // 动态颜色
      outline: false,
    },
  });

  // 飞行到初始位置
  cesium_viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(76.0, 36.5, 1000000), // 经纬度和高度
  });

  // 定时器控制动态更新
  setInterval(() => {
    changeRadius1();
    changeRadius2();
  }, 10000); // 每 10000 毫秒更新一次
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
