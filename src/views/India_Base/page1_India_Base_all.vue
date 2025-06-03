<template>
  <div id="cesium-container"></div>
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
  cesium_viewer = new Cesium.Viewer("cesium-container", {
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

  // 添加杜尔布克营地实体
  cesium_viewer.entities.add({
    id: "durbuk_base",
    position: Cesium.Cartesian3.fromDegrees(78.13766, 34.06501, 10),
    point: {
      pixelSize: 10,
      color: Cesium.Color.RED,
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
    },
    label: {
      text: "杜尔布克营地",
      font: "18px sans-serif",
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 2,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
      pixelOffset: new Cesium.Cartesian2(0, -20),
    },
  });

  // 添加楚马要塞实体
  cesium_viewer.entities.add({
    id: "chummur_base",
    position: Cesium.Cartesian3.fromDegrees(78.55748, 32.66934, 10),
    point: {
      pixelSize: 10,
      color: Cesium.Color.RED,
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
    },
    label: {
      text: "楚马要塞",
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
    destination: Cesium.Cartesian3.fromDegrees(78.3, 33.5, 500000),
    duration: 2.5,
  });

  // 监听点击事件
  const handler = new Cesium.ScreenSpaceEventHandler(
    cesium_viewer.scene.canvas
  );
  handler.setInputAction((movement) => {
    const pickedObject = cesium_viewer.scene.pick(movement.position);
    if (Cesium.defined(pickedObject) && pickedObject.id?.id === "durbuk_base") {
      router.push("page2_Durbuk_Base"); // 跳转到 page2.vue
    }
    if (
      Cesium.defined(pickedObject) &&
      pickedObject.id?.id === "chummur_base"
    ) {
      router.push("page3_Chummur_Base"); // 跳转到 page2.vue
    }
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
});

onUnmounted(() => {
  cesium_viewer?.destroy();
});
</script>

<style scoped>
#cesium-container {
  position: absolute;
  width: 100%;
  height: 100%;
}
</style>
