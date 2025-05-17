<template>
  <div ref="chart" style="width: 100%; height: 500px"></div>
</template>

<script>
import * as echarts from "echarts";
import * as d3 from "d3";
var date_list = [];
var area_list = [];

function decode_CSV(csv_path) {
  return new Promise((resolve, reject) => {
    // 使用 D3.js 读取 CSV 文件
    d3.csv(csv_path)
      .then((data) => {
        // 成功读取文件，返回数据
        resolve(data);
      })
      .catch((error) => {
        // 读取文件失败，返回错误
        reject(new Error(`读取 CSV 文件时出错: ${error.message}`));
      });
  });
}

export default {
  name: "LineChart",
  mounted() {
    this.initChart();
  },
  methods: {
    initChart() {
      decode_CSV("src/assets/test_area.csv")
        .then((csv_data) => {
          // 成功读取文件，打印数据
          console.log("CSV 文件内容:", csv_data);
          date_list = csv_data.map((item) => item.date);
          area_list = csv_data.map((item) => item.area).map(Number);
          console.log(date_list);
          console.log(area_list);
          // 获取DOM元素
          const chartDom = this.$refs.chart;
          // 初始化ECharts实例
          const myChart = echarts.init(chartDom);

          // 配置折线图选项
          const option = {
            title: {
              text: "港口面积变化图",
            },
            tooltip: {
              trigger: "axis",
            },
            xAxis: {
              type: "category",
              name: "日期",
              // data: ["周一", "周二", "周三", "周四", "周五", "周六", "周日", "周一"],
              data: date_list,
            },
            yAxis: {
              type: "value",
              name: "平方千米",
              min: function (value) {
                return 0.95 * Math.min(...area_list);
              },
              max: function (value) {
                return 1.05 * Math.max(...area_list);
              },
              axisLabel: {
                formatter: (value, index) => {
                  // 保留3位小数
                  return value.toFixed(3);
                },
              },
            },
            series: [
              {
                name: "面积",
                type: "line",
                //data: [1,2,3,4,5,6,7,8],
                data: area_list,
                color: "red",
                smooth: true, // 平滑曲线
                showSymbol: true, //是否默认展示圆点
                symbol: "emptyCircle", //设定为空心点
                symbolSize: 10, //设定实心点的大小
              },
            ],
          };

          // 使用配置项绘制图表
          myChart.setOption(option);
        })
        .catch((error) => {
          // 处理错误
          console.error(error.message);
        });
    },
  },
};
</script>

<style scoped>
* {
  padding: 0;
  margin: 0;
  list-style: none;
}
</style>
