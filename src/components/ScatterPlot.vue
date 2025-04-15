<template>
  <div ref="scatterChart" style="height: 500px;"></div>
</template>

<script>
import * as echarts from 'echarts';
import axios from 'axios';

export default {
  name: 'ScatterPlot',
  props: {
    selectedCases: {
      type: Array,
    },
    selectedComponent: {
      type: String,
      default: 'p'
    }
  },
  watch: {
    selectedCases() {
      this.updateChart();
    },
    selectedComponent() {
      this.updateChart();
    }
  },
  methods: {
    updateChart() {
      const chartDom = this.$refs.scatterChart;
      const myChart = echarts.init(chartDom);
      const coordinates = this.fetchCoordinates();

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
            data: coordinates,
            type: 'scatter'
          }
        ]
      };

      myChart.setOption(option);
    },
    async fetchCoordinates() {
      try {
        const response = await axios.post('http://localhost:5000/coordinates', {
          selectedCases: this.selectedCases,
          selectedComponent: this.selectedComponent
        });
        return response.data;
      } catch (error) {
        console.error('Error fetching coordinates:', error);
        return [];
      }
    },
  }
};
</script>

<style scoped>
/* Optional: Customize chart container styles */
</style>