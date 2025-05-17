<script setup>
import { onMounted, onUnmounted } from "vue";
import AMapLoader from "@amap/amap-jsapi-loader";
import { Amap_security_Code, Amap_key } from "../../../my_package.json";

let map = null;

onMounted(() => {
  window._AMapSecurityConfig = {
    securityJsCode: Amap_security_Code,
  };
  AMapLoader.load({
    key: Amap_key, // 申请好的Web端开发者Key，首次调用 load 时必填
    version: "2.0", // 指定要加载的 JSAPI 的版本，缺省时默认为 1.4.15
    plugins: ["AMap.Scale"], //需要使用的的插件列表，如比例尺'AMap.Scale'，支持添加多个如：['...','...']
    // Loca: { version: "2.0.0" }, // 是否加载 Loca， 缺省不加载, Loca 版本，缺省 1.3.2
  })
    .then((AMap) => {
      //1.初始化地图
      map = new AMap.Map("container", {
        // 设置地图容器id
        viewMode: "3D", // 是否为3D地图模式
        zoom: 4.1, // 初始化地图级别
        layers: [new AMap.TileLayer.Satellite(), new AMap.TileLayer.RoadNet()], //添加卫星图图层和路网图层
        center: [107.3384, 33.4], // 初始化地图中心点位置
      });

      // TODO:绘制边境线
      //2.创建国家简易行政区图层
      var distCountry = new AMap.DistrictLayer.Country({
        SOC: "CHN", //设置显示国家
        depth: 0, //设置数据显示层级，0：显示国家面，1：显示省级，当国家为中国时设置depth为2的可以显示市一级
        zIndex: 10, //设置图层层级
        opacity: 1, //图层透明度
        zooms: [2, 20], //设置图层显示范围
      });

      //3.设置行政区图层样式
      distCountry.setStyles({
        "stroke-width": 4, //描边线宽
        "coastline-stroke": [0.18, 0.63, 0.94, 0.4], //海岸线颜色
        "nation-stroke": "af70cd", //国境线颜色
        "province-stroke": [1, 1, 1, 0], //省界颜色

        fill: function (data) {
          //设置区域填充颜色，可根据回调信息返回区域信息设置不同填充色
          //回调返回区域信息数据，字段包括 SOC(国家代码)、NAME_ENG(英文名称)、NAME_CHN(中文名称)等
          //国家代码名称说明参考 https://a.amap.com/jsapi_demos/static/demo-center/js/soc-list.json
          return [1, 1, 1, 0];
        },
      });

      //4.将简易行政区图层添加到地图
      map.add(distCountry);

      //异步加载 AMap.GeoJSON 插件，该插件用于解析和渲染 GeoJSON 数据
      AMap.plugin("AMap.GeoJSON", function () {
        //创建 geoJSON 实例，传入 GeoJSON 数据和其他选项
        var geoJson = new AMap.GeoJSON({
          //将字符串形式的 GeoJSON 数据解析为对象
          geoJSON: South_China_Sea,
          //定义一个回调函数来创建多边形对象，该函数接收一个 geojson 对象和一个 lnglats 数组作为参数
          getPolygon: function (geojson, lnglats) {
            // 返回一个新的 AMap.Polygon 对象，传入路径、填充透明度、边框颜色和填充颜色等选项
            //还可以自定义 getMarker 和 getPolyline，用于创建标记和折线对象
            return new AMap.Polygon({
              path: lnglats,
              fillOpacity: 0.1,
              strokeColor: "red",
              fillColor: "red",
              strokeWeight: 3.5,
            });
          },
        });
        //将geoJson对象添加到地图上
        map.add(geoJson);
      });

      // 加载WMS图层
      var wms = new AMap.TileLayer.WMS({
        url: "http://127.0.0.1:13140/geoserver/_menu3/wms", //此处修改为你的地址
        blend: true,
        blend: true,
        tileSize: 256,
        params: {
          LAYERS: "_menu3:ZB-DEM", //此处修改为你的图层名称
          VERSION: "1.1.0",
          // STYLES: "style1", // 指定样式名称
        },
      });

      //显示WMS图层
      wms.setMap(map);

      //将图层添加至地图实例
      // map.add(imageLayer);

      // 创建文本覆盖物
      // var text = new AMap.Text({
      //   map: this.map,
      //   position: polygon.getBounds().getCenter(), // 设置位置为地块的中心点
      //   text: item.properties.XZQMC, // 文本内容，即地块名称
      //   offset: new AMap.Pixel(-30, 0), // 设置偏移量，将文本位置置于地块中心
      //   // 自定义样式
      //   style: {
      //     "background-color": "transparent", // 背景透明
      //     border: "none", // 无边框
      //     "font-size": "12px", // 字体大小
      //     color: "black", // 字体颜色
      //     // ...... 设置其他样式：字体大小、颜色等
      //   },
      // });

      // // TODO:南海
      // // 动态请求 GeoJSON 文件
      // fetch("src/views/testmap/test.json")
      //   .then((response) => response.json())
      //   .then((geoJsonData) => {
      //     var geo = new Loca.GeoJSONSource({
      //       url: "https://a.amap.com/Loca/static/loca-v2/demos/mock_data/hz_gn.json",
      //     });
      //     console.log(geoJsonData);
      //     // console.log(geoJsonData.features[0].geometry.coordinates);
      //   });

      // 使用Loca加载本地*.json文件并在map中显示,注意GeoJson格式
      // {
      //   // 初始化Loca
      //   var loca = new Loca.Container({ map: map });

      //   // 新建PolygonLayer图层
      //   var South_China_Sea_layer = new Loca.PolygonLayer({ loca: loca });
      //   var Taiwan_province_layer = new Loca.PolygonLayer({ loca: loca });
      //   var Taxkorgan_province_layer = new Loca.PolygonLayer({ loca: loca });

      //   // 读取本地标准GeoJson格式数据
      //   var South_China_Sea_geo = new Loca.GeoJSONSource({
      //     url: "src/views/testmap/South_China_Sea.json",
      //   });
      //   var Taiwan_province_geo = new Loca.GeoJSONSource({
      //     url: "src/views/testmap/Taiwan_province.json",
      //   });
      //   var Taxkorgan_province_geo = new Loca.GeoJSONSource({
      //     url: "src/views/testmap/Taxkorgan_province.json",
      //   });

      //   // 绑定本地标准GeoJson格式数据
      //   South_China_Sea_layer.setSource(South_China_Sea_geo);
      //   Taiwan_province_layer.setSource(Taiwan_province_geo);
      //   Taxkorgan_province_layer.setSource(Taxkorgan_province_geo);

      //   // 将图层添加到Loca,从而显示到map
      //   loca.add(South_China_Sea_layer);
      //   loca.add(Taiwan_province_layer);
      //   loca.add(Taxkorgan_province_layer);
      // }

      // axios动态获取*.json文件
      // axios.get("/geojson/XZXZQ.json").then((res) => {
      //   console.log(res.data, "res"); //res.data 就是文件内容
      //   let geojson = res.data;
      // });
    })
    .catch((e) => {
      console.log(e);
    });
});

onUnmounted(() => {
  map?.destroy();
});
</script>

<template>
  <div id="container"></div>
</template>

<style scoped>
#container {
  width: 100%;
  height: 800px;
}
</style>
