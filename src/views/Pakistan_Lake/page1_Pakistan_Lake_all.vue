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

  // 添加哈萨纳巴德冰川堰塞湖
  cesium_viewer.entities.add({
    id: "Hassanabad",
    position: Cesium.Cartesian3.fromDegrees(74.56766, 36.56766, 10),
    point: {
      pixelSize: 10,
      color: Cesium.Color.RED,
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
    },
    label: {
      text: "哈萨纳巴德冰川堰塞湖",
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
    destination: Cesium.Cartesian3.fromDegrees(74, 36, 500000),
    duration: 2.5,
  });

  // 监听点击事件
  const handler = new Cesium.ScreenSpaceEventHandler(
    cesium_viewer.scene.canvas
  );
  handler.setInputAction((movement) => {
    const pickedObject = cesium_viewer.scene.pick(movement.position);
    if (Cesium.defined(pickedObject) && pickedObject.id?.id === "Hassanabad") {
      router.push("page2_Hassanabad"); // 跳转到 page2.vue
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
