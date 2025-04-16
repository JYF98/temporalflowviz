<template>
  <div ref="scatterChart" style="height: 500px;"></div>
</template>

<script>
import * as echarts from 'echarts';
// import ecStat from 'echarts-stat';
import axios from 'axios';

// echarts.registerTransform(ecStat.transform.clustering);

export default {
  name: 'ScatterPlot',
  props: {
    graphObj: {
      type: Object,
      required: true
    },
  },
  watch: {
    graphObj: {
      handler() {
        this.updateChart();
      },
      deep: true
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
        const data = await this.fetchCoordinates();
        const coordinates = data.tsne_xys
        const labels = data.labels
        const cluster_count = data.cluster_count

        if (Array.isArray(coordinates) && coordinates.length > 0) {
          const option = {
            title: {
              text: 'Scatter Plot'
            },
            tooltip: {},
            xAxis: {
              type: 'value',
              name: 'X-axis'
            },
            yAxis: {
              type: 'value',
              name: 'Y-axis'
            },
            series: [{
              type: 'scatter',
              data: coordinates,
              symbolSize: 5,
              itemStyle: {
                color: function (params) {
                  const clusterIndex = labels[params.dataIndex];
                  return clusterIndex < cluster_count ? `hsl(${(clusterIndex / cluster_count) * 360}, 100%, 50%)` : '#000';
                }
              }
            }]
          };

          option && this.myChart.setOption(option);
        } else {
          console.error('Invalid coordinates format:', coordinates);
        }
      } catch (error) {
        console.error('Error updating chart:', error);
      }
    },
    async fetchCoordinates() {
      try {
        const response = await axios.post('http://localhost:5000/coordinates', this.graphObj);
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