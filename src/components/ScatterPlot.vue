<template>
  <div>
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading chart data...</div>
      <div class="loading-progress">{{ loadingProgress }}%</div>
    </div>
    <div class="main-container">
      <!-- Left side: Chart -->
      <div class="chart-container">
        <div ref="scatterChart" style="width: 600px; height: 600px;"></div>
      </div>

      <!-- Right side: Images -->
      <div class="images-container" v-if="selectedCaseName">
        <div class="images-grid">
          <div v-for="(image, index) in caseImages" :key="index" class="image-item"
            :class="{ 'selected-image': image.isSelected }">
            <div class="image-with-time">
              <div class="time-label">{{ image.timeStep }}</div>
              <img :src="image.src" :alt="`${image.timeStep}`" />
            </div>
          </div>
        </div>
        <!-- Keep your existing selected point details for the bottom section -->
        <div v-if="selectedPoint !== null" class="selected-point-details">
          <img v-if="selectedImage" :src="selectedImage" alt="Cluster image" class="selected-detail-image" />
          <div class="point-info">
            <p>Case: {{ selectedCaseName }}</p>
            <p>Time step: {{ selectedTimeStep }}</p>
            <button @click="clearSelection" class="clear-button">Clear Selection</button>
          </div>
        </div>
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
      handler(newVal, oldVal) {
        console.log('graphObj changed:', 
          oldVal?.selectedComponent, 
          '->', 
          newVal?.selectedComponent);
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
      zoomFactor: 1.2, // Adjust this value to change zoom intensity
      caseImages: [], // Will hold all images for the selected case
      resizeHandler: null, // Store the resize handler reference
    };
  },
  methods: {
    async updateChart() {
      try {
        // Start loading state
        this.isLoading = true;
        console.log('Updating chart with component:', this.graphObj.selectedComponent);

        // Clear any previous selection
        this.clearSelection();
        
        // Important: Check if chart was disposed and needs recreation
        if (!this.myChart || this.myChart.isDisposed()) {
          console.log('Chart was disposed, recreating...');
          const chartDom = this.$refs.scatterChart;
          if (chartDom) {
            this.myChart = echarts.init(chartDom);
            
            // Re-attach event listeners
            this.myChart.on('datazoom', () => {
              if (this.selectedCaseSeries) {
                // Re-apply the line series when zooming to keep it visible
                this.myChart.setOption(this.selectedCaseSeries);
              }
            });
          } else {
            console.error('Chart DOM element not found');
            this.isLoading = false;
            return;
          }
        }

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
                const caseName = cases[index];
                const timeStep = times[index];
                return `Case: ${caseName}<br/>Time: ${timeStep}<br/>Cluster: ${labels[index]}`;
              }
            },
            grid: {
              left: '10%',
              right: '15%',
              bottom: '15%',
              containLabel: true
            },
            xAxis: {
              type: 'value',
              scale: true,
              name: 'X-axis',
              nameLocation: 'middle',
              nameGap: 30,
              splitLine: {
                lineStyle: {
                  type: 'dashed'
                }
              }
            },
            yAxis: {
              type: 'value',
              scale: true,
              name: 'Y-axis',
              nameLocation: 'middle',
              nameGap: 30,
              splitLine: {
                lineStyle: {
                  type: 'dashed'
                }
              }
            },
            toolbox: {
              feature: {
                dataZoom: {
                  yAxisIndex: 'none',
                  title: {
                    zoom: 'Zoom',
                    back: 'Reset Zoom'
                  }
                },
                restore: { title: 'Reset' },
                saveAsImage: { title: 'Save as Image' }
              },
              right: 20,
              top: 25
            },
            dataZoom: [
              {
                id: 'dataZoomX',
                type: 'slider',
                xAxisIndex: 0,
                filterMode: 'none', // Key setting - preserve all data points
                start: 0,
                end: 100,
                bottom: 10,
                height: 20
              },
              {
                id: 'dataZoomY',
                type: 'slider',
                yAxisIndex: 0,
                filterMode: 'none', // Key setting - preserve all data points
                start: 0,
                end: 100,
                right: 10,
                width: 20
              },
              {
                type: 'inside',
                xAxisIndex: 0,
                filterMode: 'none', // Key setting - preserve all data points
                start: 0,
                end: 100
              },
              {
                type: 'inside',
                yAxisIndex: 0,
                filterMode: 'none', // Key setting - preserve all data points
                start: 0,
                end: 100
              }
            ],
            // legend: {
            //   data: ['Scatter Data', 'Selected Case'],
            //   right: 10,
            //   top: 'center',
            //   orient: 'vertical'
            // },
            series: [{
              name: 'Scatter Data',
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

          // Add the datazoom event handler to handle the line visibility during zoom
          this.myChart.on('datazoom', () => {
            if (this.selectedCaseSeries) {
              // Re-apply the line series when zooming to keep it visible
              this.myChart.setOption(this.selectedCaseSeries);
            }
          });

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
                    // Keep the original scatter series for background points
                    {
                      id: 'main-scatter',
                      type: 'scatter',
                      symbolSize: 5,
                      z: 5 // Keep regular points in middle layer
                    },
                    // Add connecting line first (lowest z-index of active elements)
                    {
                      id: 'case-line',
                      type: 'line',
                      data: lineCoordinates,
                      lineStyle: {
                        color: '#000000',
                        width: 2
                      },
                      symbol: 'none', // Remove symbols on the line itself
                      z: 10 // Place line above background points
                    },
                    // Add highlighted points as a separate series (highest z-index)
                    // {
                    //   id: 'case-points',
                    //   type: 'scatter',
                    //   data: lineCoordinates,
                    //   symbolSize: 8,
                    //   itemStyle: {
                    //     color: '#ff5500', // Orange color for highlighted points
                    //     borderColor: '#ffffff',
                    //     borderWidth: 1
                    //   },
                    //   z: 15 // Place case points above everything
                    // }
                  ]
                };

                this.myChart.setOption(lineOption);
                this.selectedCaseSeries = lineOption;

                // Update selected point info
                this.selectedPoint = index;
                this.selectedCaseName = caseName;
                this.selectedTimeStep = times[index];

                // Get the component path for images
                const pathmap = { p: 'p', OH: 'oh', Mach: 'mach' };
                const path = pathmap[this.graphObj.selectedComponent] || 'p';

                // Generate the image path for the selected point
                this.selectedImage = process.env.BASE_URL + `external-images/${path}/` + fileName;

                // Generate images for all points in this case
                this.caseImages = casePoints.map(idx => {
                  return {
                    src: process.env.BASE_URL + `external-images/${path}/` + fileNames[idx],
                    timeStep: times[idx],
                    isSelected: idx === index // Mark the clicked point
                  };
                });

                // Sort images by time step
                this.caseImages.sort((a, b) => a.timeStep - b.timeStep);
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
      // Add safety check
      if (this.selectedCaseSeries && this.myChart && !this.myChart.isDisposed()) {
        // Reset to original visualization without highlighted case line
        const resetOption = {
          series: this.originalOption.series
        };

        this.myChart.setOption(resetOption);
        this.selectedPoint = null;
        this.selectedImage = null;
        this.selectedCaseName = null;
        this.selectedTimeStep = null;
        this.selectedCaseSeries = null;
        this.caseImages = [];
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
    // Store reference to the resize handler
    this.resizeHandler = () => {
      if (this.myChart && !this.myChart.isDisposed()) {
        this.myChart.resize();
      }
    };
    
    // Add event listener with the stored reference
    window.addEventListener('resize', this.resizeHandler);
    
    // Rest of mounted code...
    try {
      const chartDom = this.$refs.scatterChart;
      if (chartDom) {
        this.myChart = echarts.init(chartDom);
  
        // Initial chart load
        this.updateChart();
      } else {
        console.error('Chart DOM element not found in mounted');
      }
    } catch (e) {
      console.error('Error initializing chart:', e);
    }
  },
  
  beforeDestroy() {
    // Remove event listener using the same function reference
    window.removeEventListener('resize', this.resizeHandler);
    
    // Dispose chart if it exists and isn't already disposed
    if (this.myChart && !this.myChart.isDisposed()) {
      this.myChart.dispose();
      this.myChart = null;
    }
  }
};
</script>

<style scoped>
/* Add these new styles for the layout */
.main-container {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-container {
  flex: 3;
  position: relative;
}

.images-container {
  flex: 2;
  overflow-y: auto;
  /* max-height: 500px; */
  border-left: 1px solid #ddd;
  padding-left: 20px;
}

.images-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0px;
}

.image-item {
  border: 2px solid transparent;
  border-radius: 4px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.image-item img {
  width: 100%;
  height: auto;
  display: block;
}

.image-info {
  padding: 5px;
  background-color: #f5f5f5;
  font-size: 12px;
  text-align: center;
}

.selected-image {
  border-color: #ff5500;
  box-shadow: 0 0 10px rgba(255, 85, 0, 0.5);
}

.selected-detail-image {
  max-width: 300px;
  max-height: 300px;
  margin-right: 20px;
}

/* Your existing styles */
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
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
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
  width: 50%;
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

/* New styles for image-with-time and time-label */
.image-with-time {
  display: flex;
  align-items: center;
  gap: 10px;
  background-color: #f9f9f9;
  border-radius: 4px;
  overflow: hidden;
}

.time-label {
  flex: 0 0 30px;
  /* Fixed width for time labels */
  padding: 2px;
  background-color: #eaeaea;
  color: #333;
  font-weight: bold;
  font-size: 14px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  border-right: 1px solid #ddd;
}

.image-with-time img {
  flex: 1;
  max-width: calc(100% - 90px);
  /* Account for label width + gap */
  height: auto;
  display: block;
}

/* Adjust the image-item to work with the new layout */
.image-item {
  border: 2px solid transparent;
  border-radius: 4px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.selected-image .image-with-time {
  background-color: #fff7f2;
}

.selected-image .time-label {
  background-color: #ff5500;
  color: white;
}
</style>