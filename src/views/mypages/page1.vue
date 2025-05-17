<template>
  <div>
    <div id="cesiumContainer"></div>
    <Popup
      :visible="isPopupVisible"
      :videoUrls="videoUrls"
      :deviceNames="deviceNames"
      :timestamps="timestamps"
      :location="location"
      @close="handlePopupClose"
    />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import * as Cesium from "cesium";
import {
  AMapImageryProvider,
  BaiduImageryProvider,
  GeoVisImageryProvider,
  GoogleImageryProvider,
  TdtImageryProvider,
  TencentImageryProvider,
} from "@cesium-china/cesium-map";
import { cesium_token } from "../../../my_package.json";
import Popup from "@/components/Popup/index.vue"; // 引入 Popup 组件
import CircleRippleMaterialProperty from "@/assets/CircleRippleMaterial"; // 导入材质类

let cesium_viewer = null;
let customEntities = []; // 用来存储多个自定义图标的实体
let customellipseEntities = [];
let isPopupVisible = ref(false); // 用来标记弹出框是否已显示
let videoUrls = ref([]);
let deviceNames = ref([]);
let timestamps = ref([]);
let location = ref("");

// 关闭弹出框
const handlePopupClose = () => {
  isPopupVisible.value = false;
};

onMounted(async () => {
  Cesium.Ion.defaultAccessToken = cesium_token;

  var imageryViewModels = [];
  var AMapImagery = new Cesium.ProviderViewModel({
    name: "高德地图",
    tooltip: "高德地图数据",
    iconUrl: "./sampleData/images/tianditu.jpg",
    creationFunction: function () {
      return new AMapImageryProvider({
        style: "img", // style: img(卫星)、elec(普通)、cva(路网标注)
        crs: "WGS84", // 使用84坐标系，默认为：GCJ02
      });
    },
  });
  imageryViewModels.push(AMapImagery);

  cesium_viewer = new Cesium.Viewer("cesiumContainer", {
    terrain: Cesium.Terrain.fromWorldTerrain(),
    animation: false, // 是否打开创建动画小控件，即左下角的仪表
    baseLayerPicker: true, // 是否显示图层选择器
    fullscreenButton: false, // 是否显示全屏按钮
    geocoder: true, // 是否显示Geocoder(右上角的查询按钮)
    homeButton: true, // 是否显示Home按钮
    infoBox: false, // 是否显示信息框
    maximumRenderTimeChange: Infinity, // 请求新帧的时间
    navigationHelpButton: false, // 是否显示右上角帮助按钮
    navigationInstructionsInitiallyVisible: false, //是否显示帮助信息
    requestRenderMode: true, // 显式渲染，渲染优化
    orderIndependentTranslucency: false, // 设置背景透明
    sceneMode: Cesium.SceneMode.SCENE3D, //3d视角展示
    sceneModePicker: false, // 是否显示三维地球/二维地图选择器
    selectionIndicator: true, // 是否显示选取指示器
    shadows: false, //光照的阴影效果
    shouldAnimate: false, //执行模型动画
    showRenderLoopErrors: false, // 是否显示渲染错误
    timeline: false, // 是否关闭时间轴
    vrButton: false, // 是否显示VR控件
    imageryProviderViewModels: imageryViewModels,
    selectedImageryProviderViewModel: AMapImagery,
  });
  cesium_viewer.scene.frameState.creditDisplay.container.style.display = "none";

  // 设置多个自定义图标
  const positions = [
    {
      lon: 76.0,
      lat: 36.5,
      location: "自定义地点1",
      videoUrls: [
        "http://localhost:13140/localdata/static/VIFB/elecbike/VI.jpg",
        "http://localhost:13140/localdata/static/VIFB/elecbike/IR.jpg",
        "http://localhost:13140/localdata/static/VIFB/elecbike/result.jpg",
      ],
      deviceNames: ["设备1 真彩色画面", "设备2 红外画面", "系统融合画面"],
      timestamps: ["2024-12-12 18:09", "2024-12-12 18:09", "2024-12-12 18:10"],
      label: "A",
      color: "#ff0000",
    },
    {
      lon: 77.0,
      lat: 37.5,
      location: "自定义地点2",
      videoUrls: [
        "http://localhost:13140/localdata/static/INO_Dataset/MainEntrance/VI.mp4",
        "http://localhost:13140/localdata/static/INO_Dataset/MainEntrance/IR.mp4",
        "http://localhost:13140/localdata/static/INO_Dataset/MainEntrance/result.mp4",
      ],
      deviceNames: ["设备2"],
      timestamps: ["2024-12-12 18:10"],
      label: "B",
      color: "#00ff00",
    },
    {
      lon: 78.0,
      lat: 38.5,
      location: "自定义地点3",
      videoUrls: ["https://example.com/image3.jpg"],
      deviceNames: ["设备3"],
      timestamps: ["2024-12-12 18:11"],
      label: "C",
      color: "#0000ff",
    },
  ];

  const pinBuilder = new Cesium.PinBuilder();
  positions.forEach((pos, index) => {
    const entity = cesium_viewer.entities.add({
      name: `预警地点${index + 1}`,
      position: Cesium.Cartesian3.fromDegrees(pos.lon, pos.lat),
      billboard: {
        image: pinBuilder
          .fromText(pos.label, Cesium.Color.fromCssColorString(pos.color), 48)
          .toDataURL(),
        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
    });
    customEntities.push({ entity, ...pos });
  });

  // 设置点击事件
  const handler = new Cesium.ScreenSpaceEventHandler(cesium_viewer.canvas);
  handler.setInputAction(function (click) {
    const pickedObject = cesium_viewer.scene.pick(click.position);

    if (Cesium.defined(pickedObject)) {
      const pickedEntity = customEntities.find(
        (item) => item.entity === pickedObject.id
      );
      if (pickedEntity) {
        location.value = pickedEntity.location;
        videoUrls.value = pickedEntity.videoUrls;
        deviceNames.value = pickedEntity.deviceNames;
        timestamps.value = pickedEntity.timestamps;
        isPopupVisible.value = true;
      } else {
        isPopupVisible.value = false;
      }
    } else {
      isPopupVisible.value = false;
    }
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

  cesium_viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(76.0, 36.5, 1000000),
  });
});

onUnmounted(() => {
  cesium_viewer?.destroy();
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

#cesiumContainer {
  width: 100%;
  height: 100%;
  position: absolute;
}
</style>
