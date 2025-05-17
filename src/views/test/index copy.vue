<template>
  <div class="dashboard">
    <!-- 顶部标题栏 -->
    <header class="header">
      <span class="logo">LOGO-系统名称</span>
      <span>{{ currentDate }}</span>
    </header>

    <!-- 左侧面板 -->
    <div class="panel left-panel">
      <div id="map" class="map-container"></div>
      <ChartCard id="line-chart" title="折线图" />
      <ChartCard id="pie-chart" title="饼图" />
    </div>

    <!-- 中间主地图 -->
    <div id="main-map" class="center-panel"></div>

    <!-- 右侧面板 -->
    <div class="panel right-panel">
      <ChartCard id="bar-chart" title="柱状图" />
      <el-card class="circular-progress-card">
        <div class="circular-progress">
          <div class="progress-text">
            <span>6.66%</span>
            <p>今日流量</p>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onBeforeUnmount, ref } from "vue";
import * as echarts from "echarts";
import { EChartsOption } from "echarts";

// 当前时间
const currentDate = ref(new Date().toLocaleString());
const updateCurrentDate = () => {
  currentDate.value = new Date().toLocaleString();
};

// 图表初始化逻辑
const initChart = (domId: string, option: echarts.EChartsOption) => {
  const dom = document.getElementById(domId);
  if (dom) {
    const chart = echarts.init(dom);
    chart.setOption(option);
    return chart;
  } else {
    console.error(`${domId} DOM 元素未找到`);
    return null;
  }
};

// ECharts 图表选项
const lineOption: EChartsOption = {
  title: { text: "折线图" },
  xAxis: {
    type: "category", // 修改为严格类型值
    data: ["1", "2", "3", "4", "5", "6", "7"],
  },
  yAxis: {
    type: "value", // 保留原类型
  },
  series: [
    {
      data: [820, 932, 901, 934, 1290, 1330, 1320],
      type: "line", // 保留原类型
    },
  ],
};

const pieOption: EChartsOption = {
  title: { text: "饼图", left: "center" },
  series: [
    {
      name: "访问来源",
      type: "pie", // 保留原类型
      radius: "50%",
      data: [
        { value: 1048, name: "直接访问" },
        { value: 735, name: "邮件营销" },
        { value: 580, name: "联盟广告" },
        { value: 484, name: "视频广告" },
        { value: 300, name: "搜索引擎" },
      ],
    },
  ],
};

const barOption: EChartsOption = {
  title: { text: "柱状图" },
  xAxis: {
    type: "category", // 修改为严格类型值
    data: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
  },
  yAxis: {
    type: "value", // 保留原类型
  },
  series: [
    {
      data: [120, 200, 150, 80, 70, 110, 130],
      type: "bar", // 保留原类型
    },
  ],
};

// 生命周期逻辑
onMounted(() => {
  const intervalId = setInterval(updateCurrentDate, 1000); // 每秒更新时间
  onBeforeUnmount(() => clearInterval(intervalId)); // 清除定时器

  const charts = [
    { id: "line-chart", option: lineOption },
    { id: "pie-chart", option: pieOption },
    { id: "bar-chart", option: barOption },
  ];

  const chartInstances = charts.map(({ id, option }) => initChart(id, option));

  const resizeFn = () => chartInstances.forEach((chart) => chart?.resize());
  window.addEventListener("resize", resizeFn);

  onBeforeUnmount(() => {
    window.removeEventListener("resize", resizeFn);
    chartInstances.forEach((chart) => chart?.dispose());
  });
});
</script>

<style scoped>
.dashboard {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  grid-template-rows: auto 1fr;
  height: calc(100vh - 84px);
  gap: 10px;
}

.header {
  grid-column: 1 / 4;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: #123456;
  color: white;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.map-container,
.center-panel {
  background-color: #333;
  height: 100%;
}

.circular-progress-card {
  display: flex;
  justify-content: center;
  align-items: center;
}

.circular-progress {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: conic-gradient(#4caf50 66.6%, #ccc 66.6%);
  position: relative;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: white;
}

#bar-chart,
#line-chart,
#pie-chart {
  height: 150px;
  width: 100%;
}
</style>
