<template>
  <div>
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading chart data...</div>
    </div>
    <div ref="scatterChart" style="height: 500px;"></div>
    <div v-if="selectedPoint !== null" class="selected-point-details">
      <img v-if="selectedImage" :src="selectedImage" alt="Cluster image" class="cluster-image" />
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import axios from 'axios';

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
      myChart: null,
      selectedPoint: null,
      selectedImage: null,
      isLoading: false,
      loadingProgress: 0
    };
  },
  methods: {
    async updateChart() {
      try {
        // Start loading state
        this.isLoading = true;
        this.loadingProgress = 10;
        
        // Fetch data
        this.loadingProgress = 30;
        const data = await this.fetchCoordinates();
        
        this.loadingProgress = 60;
        const coordinates = data.tsne_xys
        const labels = data.labels
        const cluster_count = data.cluster_count
        const fileNames = data.fnames
        
        this.loadingProgress = 80;
        
        if (Array.isArray(coordinates) && coordinates.length > 0) {
          const option = {
            title: {
              text: 'Scatter Plot'
            },
            tooltip: {
              trigger: 'item',
              formatter: function (params) {
                const index = params.dataIndex;
                return `Cluster: ${labels[index]}<br/>File: ${fileNames[index]}`;
              }
            },
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

          this.loadingProgress = 90;
          option && this.myChart.setOption(option);
          
          // Using arrow function to preserve 'this' context
          this.myChart.on('click', (params) => {
            if (params.componentType === 'series') {
              const index = params.dataIndex;
              const cluster = labels[index];
              const point = coordinates[index];
              const fileName = fileNames[index];
              
              // Update the selected point data
              this.selectedPoint = index;
              this.selectedCluster = cluster;
              this.selectedCoordinates = point;
              
              // FIXED: Correct path to images in public folder
              const pathmap = {p: 'p', OH: 'oh', Mach: 'mach'};
              const path = pathmap[this.graphObj.selectedComponent];
              this.selectedImage = process.env.BASE_URL + `external-images/${path}/` + fileName;
            }
          });
        } else {
          console.error('Invalid coordinates format:', coordinates);
        }
        
        this.loadingProgress = 100;
      } catch (error) {
        console.error('Error updating chart:', error);
      } finally {
        // End loading state
        this.isLoading = false;
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
    
    // Handle window resize
    window.addEventListener('resize', () => {
      this.myChart && this.myChart.resize();
    });
    
    // Initial chart load
    this.updateChart();
  },
  beforeDestroy() {
    // Clean up event listeners
    window.removeEventListener('resize', this.myChart.resize);
    this.myChart && this.myChart.dispose();
  }
};
</script>

<style scoped>
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.7);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.loading-spinner {
  border: 6px solid #f3f3f3;
  border-radius: 50%;
  border-top: 6px solid #3498db;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
}

.loading-text {
  margin-top: 15px;
  font-size: 16px;
  color: #333;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.selected-point-details {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

.cluster-image {
  max-height: 150px;
  margin-right: 20px;
}

.point-info {
  flex-grow: 1;
}

h3 {
  margin-top: 0;
  margin-bottom: 15px;
}
</style>