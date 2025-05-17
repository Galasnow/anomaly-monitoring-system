<template>
  <div>
    <!-- 左上角按钮容器 -->
    <div class="button-container">
      <el-button class="top-button" type="primary" @click="onDirectLoadClick">
        直接加载
      </el-button>
      <el-button
        class="top-button"
        type="primary"
        :disabled="isProcessing"
        @click="onButtonClick"
      >
        {{ isProcessing ? "正在进行卫星可见性评价中..." : "开始评价" }}
      </el-button>
    </div>
    <div id="cesiumContainer"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import * as Cesium from "cesium";
import { cesium_token } from "../../../../my_package.json";
import { ElMessage } from "element-plus";
import { FusionRequest, FusionType } from "@/api/lzjt/menu1/fusion/model";
import FusionAPI from "@/api/lzjt/menu1/fusion";

let cesium_viewer: Cesium.Viewer | null = null;

// 将 Image1 和 Image2 保存服务端返回的对象
const Image1 = ref({ name: "", url: "" });
const Image2 = ref({ name: "", url: "" });
const resultImageUrl = ref(""); // 保存处理后图片的URL
const isProcessing = ref(false); // 控制处理状态

// 按钮点击事件：直接加载 WMS 图层
const onDirectLoadClick = async () => {
  await addWmsLayer();
};

/**
 * 异步函数：添加 WMS 图层到 Cesium Viewer
 * @returns {Promise<void>}
 */
const addWmsLayer = async () => {
  if (!cesium_viewer) {
    console.error("Cesium Viewer 尚未初始化!");
    return;
  }

  try {
    const provider = new Cesium.WebMapServiceImageryProvider({
      // 创建一个图层
      url: "http://127.0.0.1:13140/geoserver/satellitevisibility/wms",
      layers: "	satellitevisibility:ZB-DEM",
      parameters: {
        service: "WMS",
        version: "1.1.0",
        request: "GetMap",
        format: "image/pngSS",
        transparent: true, // 确保设置透明
        srs: "EPSG:4326", // 或者使用 CRS
      },
    });

    // 添加图层到 Cesium Viewer
    cesium_viewer.imageryLayers.addImageryProvider(provider);
    ElMessage.success("WMS 图层已成功添加!");
  } catch (error) {
    console.error("添加 WMS 图层失败:", error);
    ElMessage.error("添加 WMS 图层失败，请检查配置!");
  }
};

/**
 * 主处理函数：执行评价并添加 WMS 图层
 */
const onButtonClick = async () => {
  // 防止重复点击
  if (isProcessing.value) return;

  // if (!Image1.value.url) {
  //   ElMessage.error("请上传影像后再执行操作!");
  //   return;
  // }

  const requestData = {
    Image1_name: Image1.value.name,
    Image2_name: Image2.value.name,
    type: FusionType.Satellite_Visibility,
  };

  try {
    // 显示加载状态
    isProcessing.value = true;

    // 发送请求到后端
    const response = await FusionAPI.startFusion(requestData);
    // 请求成功，返回处理后的图片URL
    resultImageUrl.value = response.url;
    ElMessage.success("评价完成!");
    // 调用添加 WMS 图层函数
    await addWmsLayer();
  } catch (error) {
    ElMessage.error("评价失败，请重试!");
    console.error(error);
  } finally {
    // 取消加载状态
    isProcessing.value = false;
  }
};

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
  });
  cesium_viewer.scene.frameState.creditDisplay.container.style.display = "none"; // 隐藏logo和版权信息

  // 飞行到某位置
  cesium_viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(76.0, 36.5, 1000000), //经纬度和高度
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
.button-container {
  position: absolute;
  z-index: 1000;
  gap: 10px; /* 按钮间距 */
}
</style>
