<template>
  <div>
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
      selectedCluster: null,
      selectedCoordinates: [0, 0],
      selectedImage: null,
    };
  },
  methods: {
    async updateChart() {
      try {
        const data = await this.fetchCoordinates();
        const coordinates = data.tsne_xys
        const labels = data.labels
        const cluster_count = data.cluster_count
        const fileNames = data.fnames

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
              this.selectedImage = process.env.BASE_URL + 'external-images/' + fileName;
              
              // Add error handling for image loading
              const img = new Image();
              img.onerror = () => {
                console.error(`Failed to load image: ${this.selectedImage}`);
                this.selectedImage = process.env.BASE_URL + 'external-images/placeholder.png'; // Fallback image
              };
              img.src = this.selectedImage;
            }
          });
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
    
    // Handle window resize
    window.addEventListener('resize', () => {
      this.myChart && this.myChart.resize();
    });
  },
  beforeDestroy() {
    // Clean up event listeners
    window.removeEventListener('resize', this.myChart.resize);
    this.myChart && this.myChart.dispose();
  }
};
</script>

<style scoped>
.selected-point-details {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

.cluster-image {
  /* max-width: 200px; */
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