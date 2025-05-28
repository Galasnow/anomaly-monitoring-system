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
  // cesium_viewer._cesiumWidget._creditContainer.style.display = "none";
  // var provider = new Cesium.WebMapServiceImageryProvider({
  //   url: "http://127.0.0.1:13140/geoserver/satellitevisibility/",
  //   layers: "satellitevisibility:ZB-DEM",
  //   parameters: {
  //     service: "WMS",
  //     version: "1.1.1",
  //     request: "GetMap",
  //     format: "image/png",
  //     transparent: true,
  //     srs: "EPSG:4326",
  //   },
  // });
  // cesium_viewer.imageryLayers.addImageryProvider(provider);

  // 添加SK10实体
  const mande_haixia = cesium_viewer.entities.add({
    id: "mande_haixia",
    position: Cesium.Cartesian3.fromDegrees(43.9122, 12.4516, 10),
    point: {
      pixelSize: 10,
      color: Cesium.Color.RED,
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
    },
    label: {
      text: "曼德海峡",
      font: "16px sans-serif",
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 2,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
      pixelOffset: new Cesium.Cartesian2(0, -20),
    },
  });

  cesium_viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(43.9122, 12.4516, 650000),
    duration: 2,
  });

  // 监听点击事件
  const handler = new Cesium.ScreenSpaceEventHandler(
    cesium_viewer.scene.canvas
  );
  handler.setInputAction((movement) => {
    const pickedObject = cesium_viewer.scene.pick(movement.position);
    if (Cesium.defined(pickedObject) && pickedObject.id?.id === "mande_haixia")
      router.push("page_mandehaixia");
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
