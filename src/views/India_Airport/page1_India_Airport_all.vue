<template>
  <div id="cesiumContainer"></div>
</template>

<script setup>
import { onMounted, onUnmounted } from "vue";
import * as Cesium from "cesium";
import { useRouter } from "vue-router";
import { cesium_token } from "../../../my_package.json";

let cesium_viewer = null;
const router = useRouter();

onMounted(async () => {
  Cesium.Ion.defaultAccessToken = cesium_token;
  cesium_viewer = new Cesium.Viewer("cesiumContainer", {
    animation: false,
    baseLayerPicker: true,
    fullscreenButton: false,
    geocoder: true,
    homeButton: true,
    infoBox: true,
    sceneModePicker: true,
    selectionIndicator: true,
    shouldAnimate: true,
    showRenderLoopErrors: false,
    timeline: false,
    navigationHelpButton: false,
    navigationInstructionsInitiallyVisible: false,
  });

  cesium_viewer.scene.frameState.creditDisplay.container.style.display = "none";

  // 添加比夏纳空军基地实体
  cesium_viewer.entities.add({
    id: "Bhatinda_Air_Force_Station",
    position: Cesium.Cartesian3.fromDegrees(74.75552, 30.27766, 10),
    point: {
      pixelSize: 10,
      color: Cesium.Color.RED,
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
    },
    label: {
      text: "比夏纳空军基地",
      font: "18px sans-serif",
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 2,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
      pixelOffset: new Cesium.Cartesian2(0, -20),
    },
  });

  // 添加锡尔恰尔机场实体
  cesium_viewer.entities.add({
    id: "Silchar_Airport",
    position: Cesium.Cartesian3.fromDegrees(92.97897, 24.9145, 10),
    point: {
      pixelSize: 10,
      color: Cesium.Color.RED,
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
    },
    label: {
      text: "锡尔恰尔机场",
      font: "18px sans-serif",
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 2,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
      pixelOffset: new Cesium.Cartesian2(0, -20),
    },
  });


    // 添加德拉敦机场实体
  cesium_viewer.entities.add({
    id: "Dehradun_Airport",
    position: Cesium.Cartesian3.fromDegrees(78.190046, 30.193041, 10),
    point: {
      pixelSize: 10,
      color: Cesium.Color.RED,
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
    },
    label: {
      text: "德拉敦机场",
      font: "18px sans-serif",
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 2,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
      pixelOffset: new Cesium.Cartesian2(0, -20),
    },
  });


  // 添加列城机场实体
  cesium_viewer.entities.add({
    id: "Leh_Airport",
    position: Cesium.Cartesian3.fromDegrees(77.540251, 34.135811, 10),
    point: {
      pixelSize: 10,
      color: Cesium.Color.RED,
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
    },
    label: {
      text: "列城机场",
      font: "18px sans-serif",
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 2,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
      pixelOffset: new Cesium.Cartesian2(0, -20),
    },
  });


  // 添加伦格普伊机场实体
  cesium_viewer.entities.add({
    id: "Lengpui_Airport",
    position: Cesium.Cartesian3.fromDegrees(92.618786, 23.839196, 10),
    point: {
      pixelSize: 10,
      color: Cesium.Color.RED,
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
    },
    label: {
      text: "伦格普伊机场",
      font: "18px sans-serif",
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 2,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
      pixelOffset: new Cesium.Cartesian2(0, -20),
    },
  });

    // 添加伦格普伊机场实体
  cesium_viewer.entities.add({
    id: "Chabua_Air_Force_Station",
    position: Cesium.Cartesian3.fromDegrees(95.114966, 27.467536, 10),
    point: {
      pixelSize: 10,
      color: Cesium.Color.RED,
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
    },
    label: {
      text: "贾布瓦空军基地",
      font: "18px sans-serif",
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 2,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
      pixelOffset: new Cesium.Cartesian2(0, -20),
    },
  });

  cesium_viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(83.71, 30.38, 3000000), duration:2.5
  });

  // 监听点击事件
  const handler = new Cesium.ScreenSpaceEventHandler(cesium_viewer.scene.canvas);
  handler.setInputAction((movement) => {
    const pickedObject = cesium_viewer.scene.pick(movement.position);
    if (Cesium.defined(pickedObject) && pickedObject.id?.id === "Bhatinda_Air_Force_Station") {
      router.push("page2_Bhatinda_Air_Force_Station"); // 跳转到 page2_Bhatinda_Air_Force_Station.vue
    }
    if (Cesium.defined(pickedObject) && pickedObject.id?.id === "Silchar_Airport") {
      router.push("page3_Silchar_Airport"); // 跳转到 page3_Silchar_Airport.vue
    }
    if (Cesium.defined(pickedObject) && pickedObject.id?.id === "Dehradun_Airport") {
      router.push("page4_Dehradun_Airport"); // 跳转到 page4_Dehradun_Airport.vue
    }
    if (Cesium.defined(pickedObject) && pickedObject.id?.id === "Leh_Airport") {
      router.push("page5_Leh_Airport"); // 跳转到 page5_Leh_Airport.vue
    }
    if (Cesium.defined(pickedObject) && pickedObject.id?.id === "Lengpui_Airport") {
      router.push("page6_Lengpui_Airport"); // 跳转到 page6_Lengpui_Airport.vue
    }
    if (Cesium.defined(pickedObject) && pickedObject.id?.id === "Chabua_Air_Force_Station") {
      router.push("page7_Chabua_Air_Force_Station"); // 跳转到 page6_Lengpui_Airport.vue
    }
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
});

onUnmounted(() => {
  cesium_viewer?.destroy();
});
</script>

<style scoped>
#cesiumContainer {
  width: 100%;
  height: 100%;
  position: absolute;
}
</style>
