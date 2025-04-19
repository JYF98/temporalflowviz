<template>
  <div>
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading chart data...</div>
      <div class="loading-progress">{{ loadingProgress }}%</div>
    </div>
    <div class="chart-container">
      <div ref="scatterChart" style="height: 500px; width: 70%;"></div>
      <!-- <div class="zoom-controls">
        <button @click="zoomIn" class="zoom-button">+</button>
        <button @click="zoomOut" class="zoom-button">-</button>
        <button @click="resetZoom" class="zoom-button">Reset</button>
      </div> -->
    </div>
    <div v-if="selectedPoint !== null" class="selected-point-details">
      <img v-if="selectedImage" :src="selectedImage" alt="Cluster image" class="cluster-image" />
      <div class="point-info">
        <p>Case: {{ selectedCaseName }}</p>
        <p>Time step: {{ selectedTimeStep }}</p>
        <button @click="clearSelection" class="clear-button">Clear Selection</button>
      </div>
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
      selectedCaseName: null,
      selectedTimeStep: null,
      selectedCaseSeries: null,
      isLoading: false,
      loadingProgress: 0,
      originalOption: null,
      zoomLevel: 1,
      zoomFactor: 1.2 // Adjust this value to change zoom intensity
    };
  },
  methods: {
    async updateChart() {
      try {
        // Start loading state
        this.isLoading = true;
        
        // Clear any previous selection
        this.clearSelection();
        
        // Fetch data
        this.loadingProgress = 30;
        const data = await this.fetchCoordinates();
        
        this.loadingProgress = 60;
        const coordinates = data.tsne_xys;
        const labels = data.labels;
        const cluster_count = data.cluster_count;
        const fileNames = data.fnames;
        const times = data.times;
        const cases = data.cases;
        const caseMap = this.buildCaseMap(cases);
        
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
                const caseName = cases[index]; // Extract case name from filename
                const timeStep = times[index];
                return `Case: ${caseName}<br/>Time: ${timeStep}<br/>Cluster: ${labels[index]}`;
              }
            },
            xAxis: {
              type: 'value',
              scale: true
            },
            yAxis: {
              type: 'value',
              scale: true
            },
            toolbox: {
              feature: {
                dataZoom: {
                  yAxisIndex: 'none'
                },
                restore: {},
                saveAsImage: {}
              }
            },
            dataZoom: [
              {
                type: 'inside',
                xAxisIndex: 0,
                filterMode: 'empty'
              },
              {
                type: 'inside',
                yAxisIndex: 0,
                filterMode: 'empty'
              }
            ],
            series: [{
              type: 'scatter',
              id: 'main-scatter',
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

          // Store the original option for resetting view
          this.originalOption = JSON.parse(JSON.stringify(option));
          
          this.loadingProgress = 90;
          this.myChart.setOption(option);
          
          // Using arrow function to preserve 'this' context
          this.myChart.on('click', (params) => {
            if (params.componentType === 'series') {
              const index = params.dataIndex;
              const fileName = fileNames[index];
              const caseName = cases[index]; // Extract case name from filename
              
              // Find all points from the same case
              const casePoints = caseMap[caseName] || [];
              
              if (casePoints.length > 0) {
                // Sort points by time
                casePoints.sort((a, b) => times[a] - times[b]);
                
                // Extract coordinates for the line
                const lineCoordinates = casePoints.map(idx => coordinates[idx]);
                
                // Add a line series connecting the points in time order
                const lineOption = {
                  series: [
                    // Keep the original scatter series
                    {
                      id: 'main-scatter',
                      type: 'scatter'
                    },
                    // Add line series to connect points from the same case
                    {
                      id: 'case-line',
                      type: 'line',
                      data: lineCoordinates,
                      lineStyle: {
                        color: '#ff5500',
                        width: 2
                      },
                      symbol: 'circle',
                      symbolSize: 8,
                      emphasis: {
                        lineStyle: {
                          width: 3
                        },
                        symbolSize: 10
                      },
                      z: 10 // Ensure line is drawn above scatter points
                    }
                  ]
                };
                
                this.myChart.setOption(lineOption);
                this.selectedCaseSeries = lineOption;
                
                // Update selected point info
                this.selectedPoint = index;
                this.selectedCaseName = caseName;
                this.selectedTimeStep = times[index];
                
                // Load the corresponding image
                const pathmap = {p: 'p', OH: 'oh', Mach: 'mach'};
                const path = pathmap[this.graphObj.selectedComponent] || 'p';
                this.selectedImage = process.env.BASE_URL + `external-images/${path}/` + fileName;
              }
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
    
    // Zoom in function for button control
    zoomIn() {
      if (!this.myChart) return;
      
      // Get current axes options
      const option = this.myChart.getOption();
      const currentXMin = option.xAxis[0].min;
      const currentXMax = option.xAxis[0].max;
      const currentYMin = option.yAxis[0].min;
      const currentYMax = option.yAxis[0].max;
      
      // Calculate new zoom range
      const xRange = currentXMax - currentXMin;
      const yRange = currentYMax - currentYMin;
      const xCenter = (currentXMin + currentXMax) / 2;
      const yCenter = (currentYMin + currentYMax) / 2;
      
      // Apply zoom
      const newOption = {
        xAxis: [{
          min: xCenter - xRange / (2 * this.zoomFactor),
          max: xCenter + xRange / (2 * this.zoomFactor)
        }],
        yAxis: [{
          min: yCenter - yRange / (2 * this.zoomFactor),
          max: yCenter + yRange / (2 * this.zoomFactor)
        }]
      };
      
      this.myChart.setOption(newOption);
      this.zoomLevel *= this.zoomFactor;
    },
    
    // Zoom out function for button control
    zoomOut() {
      if (!this.myChart) return;
      
      // Get current axes options
      const option = this.myChart.getOption();
      const currentXMin = option.xAxis[0].min;
      const currentXMax = option.xAxis[0].max;
      const currentYMin = option.yAxis[0].min;
      const currentYMax = option.yAxis[0].max;
      
      // Calculate new zoom range
      const xRange = currentXMax - currentXMin;
      const yRange = currentYMax - currentYMin;
      const xCenter = (currentXMin + currentXMax) / 2;
      const yCenter = (currentYMin + currentYMax) / 2;
      
      // Apply zoom
      const newOption = {
        xAxis: [{
          min: xCenter - xRange * this.zoomFactor / 2,
          max: xCenter + xRange * this.zoomFactor / 2
        }],
        yAxis: [{
          min: yCenter - yRange * this.zoomFactor / 2,
          max: yCenter + yRange * this.zoomFactor / 2
        }]
      };
      
      this.myChart.setOption(newOption);
      this.zoomLevel /= this.zoomFactor;
    },
    
    // Reset zoom to original view
    resetZoom() {
      if (!this.myChart || !this.originalOption) return;
      
      const resetOption = {
        xAxis: [{
          min: null,
          max: null
        }],
        yAxis: [{
          min: null,
          max: null
        }]
      };
      
      this.myChart.setOption(resetOption);
      this.zoomLevel = 1;
    },
    
    // Build a map of case names to their point indices
    buildCaseMap(cases) {
      const caseMap = {};
      
      cases.forEach((caseName, index) => {
        if (!caseMap[caseName]) {
          caseMap[caseName] = [];
        }
        caseMap[caseName].push(index);
      });
      
      return caseMap;
    },
    
    clearSelection() {
      if (this.selectedCaseSeries && this.myChart) {
        // Reset to original visualization without highlighted case line
        // const currentOption = this.myChart.getOption();
        // Preserve current zoom level when clearing selection
        const resetOption = {
          series: this.originalOption.series
        };
        
        this.myChart.setOption(resetOption);
        this.selectedPoint = null;
        this.selectedImage = null;
        this.selectedCaseName = null;
        this.selectedTimeStep = null;
        this.selectedCaseSeries = null;
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
.chart-container {
  position: relative;
}

.zoom-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  z-index: 5;
}

.zoom-button {
  width: 30px;
  height: 30px;
  margin-bottom: 5px;
  background-color: rgba(255, 255, 255, 0.8);
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.zoom-button:hover {
  background-color: rgba(240, 240, 240, 0.9);
}

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

.loading-progress {
  margin-top: 5px;
  font-size: 14px;
  color: #666;
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
  width:50%;
  margin-right: 20px;
}

.point-info {
  flex-grow: 1;
}

h3 {
  margin-top: 0;
  margin-bottom: 15px;
}

.clear-button {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

.clear-button:hover {
  background-color: #d32f2f;
}
</style>