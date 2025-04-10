<template>
    <div ref="scatterChart" style="height: 500px;"></div>
  </template>
  
  <script>
  import * as echarts from 'echarts';
  
  export default {
    name: 'ScatterPlot',
    props: {
      filters: Object
    },
    watch: {
      filters(newFilters) {
        this.updateChart(newFilters);
      }
    },
    methods: {
      updateChart(filters) {
        // You can replace this with actual data filtering based on the 'filters' prop
        const data = this.generateData(filters);
  
        const chartDom = this.$refs.scatterChart;
        const myChart = echarts.init(chartDom);
  
        const option = {
          title: {
            text: 'Scatter Plot Example'
          },
          tooltip: {
            trigger: 'item'
          },
          xAxis: {
            type: 'value',
            name: 'X Axis'
          },
          yAxis: {
            type: 'value',
            name: 'Y Axis'
          },
          series: [
            {
              symbolSize: 10,
              data: data,
              type: 'scatter'
            }
          ]
        };
  
        myChart.setOption(option);
      },
      generateData(filters) {
        // Use filters to generate or fetch data for the plot
        // Example data based on the filter values
        return [
          [filters.p, filters.T],
          [filters.p + 10, filters.T + 10],
          [filters.p + 20, filters.T + 20],
          [filters.p + 30, filters.T + 30]
        ];
      }
    }
  };
  </script>
  
  <style scoped>
  /* Optional: Customize chart container styles */
  </style>
  