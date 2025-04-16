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
  data: function () {
    return {
      myChart: null
    };
  },
  methods: {
    async updateChart() {
      try {
        // Wait for coordinates to be fetched
        const coordinates = await this.fetchCoordinates();
        console.log('Coordinates:', coordinates);

        // Only proceed if we have valid coordinates
        if (Array.isArray(coordinates)) {
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
                symbolSize: 5,
                data: coordinates,
                type: 'scatter'
              }
            ]
          };

          this.myChart.setOption(option);
        } else {
          console.error('Invalid coordinates format:', coordinates);
        }
      } catch (error) {
        console.error('Error updating chart:', error);
      }
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
    }
  },
  mounted() {
    // Initialize the chart when the component is mounted
    const chartDom = this.$refs.scatterChart;
    this.myChart = echarts.init(chartDom);
  }
};
</script>

<style scoped>
/* Optional: Customize chart container styles */
</style>