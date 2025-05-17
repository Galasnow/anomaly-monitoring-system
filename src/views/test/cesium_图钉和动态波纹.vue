<template>
  <div>
    <div id="cesiumContainer"></div>
    <Popup
      :visible="isPopupVisible"
      :content="popupContent"
      :cesiumContainerHeight="cesiumHeight"
      :position="popupPosition"
      @close="handlePopupClose"
    />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from "vue";
import * as Cesium from "cesium";
import { cesium_token } from "../../../my_package.json";
import CircleRippleMaterialProperty from "@/assets/CircleRippleMaterial"; // 导入材质类
import Popup from "@/components/Popup/index.vue"; // 引入 Popup 组件

let cesium_viewer = null;
const rippleSize = ref(1); // 用于存储波纹的大小系数
let billboardEntity = null; // 用来存储自定义图标的实体
let ellipseEntity = null;
let isPopupVisible = ref(false); // 用来标记弹出框是否已显示
let popupContent = ref(""); // 弹出框的内容
let popupPosition = ref({ x: 0, y: 0 }); // 弹出框的位置
let cesiumHeight = ref(0); // 保存 cesiumContainer 的高度
let position = null;

// 关闭弹出框
const handlePopupClose = () => {
  isPopupVisible.value = false;
};

onMounted(async () => {
  Cesium.Ion.defaultAccessToken = cesium_token;
  cesium_viewer = new Cesium.Viewer("cesiumContainer", {
    terrain: Cesium.Terrain.fromWorldTerrain(),
  });
  cesium_viewer.scene.frameState.creditDisplay.container.style.display = "none"; // 隐藏logo和版权信息
  cesium_viewer.scene.globe.depthTestAgainstTerrain = false; // 设置为 false 禁用地形深度测试

  // 设置自定义图标
  position = Cesium.Cartesian3.fromDegrees(76.0, 36.5);

  // 波纹效果
  {
    // 监听相机位置变化，根据相机高度调整波纹大小
    cesium_viewer.scene.preRender.addEventListener(() => {
      const cameraPosition = cesium_viewer.camera.positionCartographic;
      const height = cameraPosition.height; // 获取相机高度
      rippleSize.value = Math.max(0.01, height / 560000); // 根据相机高度调整波纹的大小，避免波纹过小
      rippleSize.value = Math.min(20, rippleSize.value);
    });

    // 添加带有波纹效果的实体
    ellipseEntity = cesium_viewer.entities.add({
      name: "波纹效果",
      position: position,
      ellipse: {
        height: 0,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        semiMinorAxis: new Cesium.CallbackProperty(() => {
          return 30000 * rippleSize.value;
        }, false),
        semiMajorAxis: new Cesium.CallbackProperty(() => {
          return 30000 * rippleSize.value;
        }, false),
        // 使用 new 创建材质实例
        material: new CircleRippleMaterialProperty({
          color: Cesium.Color.RED,
          speed: 10,
          count: 3,
          gradient: 0.5,
        }),
      },
      allowPicking: false, // 禁用选中
    });
  }

  // 添加图钉标记
  {
    const pinBuilder = new Cesium.PinBuilder();
    billboardEntity = cesium_viewer.entities.add({
      name: "自定义图标",
      position: position,
      billboard: {
        image: pinBuilder.fromText("警", Cesium.Color.YELLOW, 32).toDataURL(),
        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND, // 让图标始终贴地面
        //disableDepthTestDistance: Number.POSITIVE_INFINITY, // 禁用深度测试
      },
    });

    // 设置点击事件
    const handler = new Cesium.ScreenSpaceEventHandler(cesium_viewer.canvas);
    handler.setInputAction(function (click) {
      const pickedObject = cesium_viewer.scene.pick(click.position); // 获取点击的物体

      // 确保是点击的我们自定义的图标
      if (
        Cesium.defined(pickedObject) &&
        (pickedObject.id === billboardEntity ||
          pickedObject.id === ellipseEntity)
      ) {
        const canvasPosition =
          cesium_viewer.scene.cartesianToCanvasCoordinates(position);
        popupPosition.value = { x: canvasPosition.x, y: canvasPosition.y }; // 设置弹出框位置
        popupContent.value = "这是一个自定义标记！"; // 设置弹出框内容
        isPopupVisible.value = true; // 显示弹出框
      } else {
        // 点击其他地方时关闭弹出框
        isPopupVisible.value = false;
      }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
  }

  // cesium_viewer.flyTo(entity); // 飞到该实体
  // 飞行到初始位置
  cesium_viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(76.0, 36.5, 1000000), // 经纬度和高度
  });
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
