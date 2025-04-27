<template>
  <div>
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading chart data...</div>
    </div>
    <div class="main-container">
      <!-- Left side: Chart -->
      <div class="chart-container">
        <div ref="scatterChart" style="flex: 1; height: 500px;"></div>
        <!-- Similar trajectories section -->
        <div class="similar-trajectories">
          <h3>Similar Case Trajectories</h3>
          <div class="trajectories-container">
            <div v-for="(similarCase, index) in similarCases" :key="index" class="similar-case">
              <h4>{{ similarCase.caseName }} (MSE: {{ similarCase.mse.toFixed(2) }})</h4>
              <div :ref="`similarChart${index}`" class="similar-chart"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right side: Images -->
      <div class="images-container">
        <div v-if="selectedPoint !== null" class="selected-point-details">
          <div class="point-info">
            <span>Case: {{ selectedCaseName }} Time: {{ selectedTimeStep }}</span>
            <button @click="clearSelection" class="clear-button">Clear Selection</button>
          </div>
        </div>
        <div class="images-grid">
          <div v-for="(image, index) in caseImages" :key="index" class="image-item"
            :class="{ 'selected-image': image.isSelected }">
            <div class="image-with-time">
              <div class="time-label">{{ image.timeStep }}</div>
              <img :src="image.src" :alt="`${image.timeStep}`" />
            </div>
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
      originalOption: null,
      caseImages: [], // Will hold all images for the selected case
      resizeHandler: null, // Store the resize handler reference
      case_xys_dict: {}, // Dictionary to hold case names and their corresponding indices
      fileNames: [], // Will hold filenames of the points
      labels: [], // Will hold cluster labels
      cases: [], // Will hold case names
      times: [], // Will hold time steps
      similarCases: [], // Will hold similar cases data
      similarCharts: [], // Will hold references to the chart instances
    };
  },
  methods: {
    async updateChart() {
      try {
        // Start loading state
        this.isLoading = true;

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
        const data = await this.fetchCoordinates();
        const coordinates = data.tsne_xys;
        this.labels = data.labels;
        const cluster_count = data.cluster_count;
        this.fileNames = data.fnames;
        this.times = data.times;
        this.cases = data.cases;
        const caseMap = this.buildCaseMap(this.cases);
        this.case_xys_dict = data.case_xys_dict;

        if (Array.isArray(coordinates) && coordinates.length > 0) {
          const option = {
            title: {
              text: 'Scatter Plot'
            },
            tooltip: {
              trigger: 'item',
              formatter: (params) => {
                const index = params.dataIndex;
                const caseName = this.cases[index];
                const timeStep = this.times[index];
                return `Case: ${caseName}<br/>Time: ${timeStep}<br/>Cluster: ${this.labels[index]}`;
              }
            },
            grid: {
              left: '0%',
              right: '0%',
              bottom: '0%',
              top: '0%',
              containLabel: false
            },
            xAxis: {
              type: 'value',
              scale: true,
              name: 'X-axis',
              nameLocation: 'middle',
              nameGap: 10,
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
              nameGap: 10,
              splitLine: {
                lineStyle: {
                  type: 'dashed'
                }
              }
            },
            dataZoom: [
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
            series: [{
              name: 'Scatter Data',
              type: 'scatter',
              id: 'main-scatter',
              data: coordinates,
              symbolSize: 5,
              itemStyle: {
                color: (params) => {
                  const clusterIndex = this.labels[params.dataIndex];
                  return clusterIndex < cluster_count ? `hsl(${(clusterIndex / cluster_count) * 360}, 100%, 50%)` : '#000';
                },
              }
            }]
          };

          // Store the original option for resetting view
          this.originalOption = JSON.parse(JSON.stringify(option));
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
              const fileName = this.fileNames[index];
              const caseName = this.cases[index]; // Extract case name from filename

              // Find all points from the same case
              const casePoints = caseMap[caseName] || [];

              if (casePoints.length > 0) {
                // Sort points by time
                casePoints.sort((a, b) => this.times[a] - this.times[b]);

                // Extract coordinates for the line
                const lineCoordinates = casePoints.map(idx => coordinates[idx]);

                // Add a line series connecting the points in time order
                const lineOption = {
                  series: [
                    // Keep the original scatter series for background points
                    {
                      id: 'main-scatter',
                      type: 'scatter',
                      data: coordinates,
                      symbolSize: (params) => {
                        // Check if this point belongs to the selected case
                        if (this.cases[params.dataIndex] === caseName) {
                          return 15; // Bigger symbol size for selected case points
                        }
                        return 5; // Default size for other points
                      },
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
                      symbol: 'none',
                      tooltip: {
                        show: false // Disable tooltip for the line
                      },
                      z: 10 // Place line above background points
                    },
                  ]
                };

                this.myChart.setOption(lineOption);
                this.selectedCaseSeries = lineOption;

                // Update selected point info
                this.selectedPoint = index;
                this.selectedCaseName = caseName;
                this.selectedTimeStep = this.times[index];

                // Get the component path for images
                const pathmap = { p: 'p_cropped_img2/', OH: 'imgs/oh/', Mach: 'imgs/mach/' };
                const path = pathmap[this.graphObj.selectedComponent] || pathmap.p;
                this.selectedImage = process.env.BASE_URL + path + fileName;

                // Generate images for all points in this case
                this.caseImages = casePoints.map(idx => {
                  return {
                    src: process.env.BASE_URL + path + this.fileNames[idx],
                    timeStep: this.times[idx],
                    isSelected: idx === index // Mark the clicked point
                  };
                });
                this.caseImages.sort((a, b) => a.timeStep - b.timeStep);
              }
              this.findSimilarCases(caseName, coordinates);
            }
          });
        } else {
          console.error('Invalid coordinates format:', coordinates);
        }
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
      this.clearSimilarCharts();
      this.similarCases = [];
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
    },

    findSimilarCases(selectedCaseName, allCoordinates) {
      // Clear previous similar cases and charts
      this.clearSimilarCharts();
      this.similarCases = [];

      if (!selectedCaseName || !this.case_xys_dict[selectedCaseName]) return;

      // Get the trajectory of the selected case
      const selectedTrajectory = this.case_xys_dict[selectedCaseName];

      // Calculate similarity with all other cases
      const similarities = [];

      for (const caseName in this.case_xys_dict) {
        // Skip the selected case
        if (caseName === selectedCaseName) continue;

        const caseTrajectory = this.case_xys_dict[caseName];
        if (!caseTrajectory || caseTrajectory.length === 0) continue;

        // Calculate mse error
        const mse = this.calculateTrajectoryMSE(selectedTrajectory, caseTrajectory);

        similarities.push({
          caseName,
          mse,
          trajectory: caseTrajectory
        });
      }

      // Sort by mse (lower is more similar)
      similarities.sort((a, b) => a.mse - b.mse);

      // Take top 3 similar cases
      this.similarCases = similarities.slice(0, 3);

      // Render the similar case charts after DOM update
      this.$nextTick(() => {
        this.renderSimilarCharts(allCoordinates);
      });
    },

    // Calculate trajectory similarity using Mean Squared Error between points
    calculateTrajectoryMSE(trajectory1, trajectory2) {
      // Need to align trajectories for comparison
      // First, ensure both have the same number of points by sampling
      const targetLength = Math.min(
        Math.max(trajectory1.length, trajectory2.length),
        50  // Cap maximum points to consider for performance
      );

      // Sample both trajectories to have equal number of points
      const sampledTrajectory1 = this.sampleTrajectory(trajectory1, targetLength);
      const sampledTrajectory2 = this.sampleTrajectory(trajectory2, targetLength);

      // Calculate MSE between corresponding points
      let totalSquaredError = 0;

      for (let i = 0; i < targetLength; i++) {
        const p1 = sampledTrajectory1[i];
        const p2 = sampledTrajectory2[i];

        // Calculate squared error between points
        const dx = p1[0] - p2[0];
        const dy = p1[1] - p2[1];
        totalSquaredError += dx * dx + dy * dy;
      }

      // Calculate MSE
      const mse = totalSquaredError / targetLength;

      return mse;
    },

    // Sample trajectory to have exactly targetLength points evenly distributed
    sampleTrajectory(trajectory, targetLength) {
      if (trajectory.length === targetLength) {
        return [...trajectory]; // Return a copy to avoid modifying original
      }

      const result = [];

      if (targetLength === 1) {
        // If target length is 1, return middle point
        return [trajectory[Math.floor(trajectory.length / 2)]];
      }

      // Linear interpolation between points
      for (let i = 0; i < targetLength; i++) {
        // Calculate the position in the original trajectory
        const position = (i / (targetLength - 1)) * (trajectory.length - 1);
        const index = Math.floor(position);
        const fraction = position - index;

        if (index >= trajectory.length - 1) {
          // Last point
          result.push(trajectory[trajectory.length - 1]);
        } else {
          // Interpolate between two points
          const point1 = trajectory[index];
          const point2 = trajectory[index + 1];

          const x = point1[0] + fraction * (point2[0] - point1[0]);
          const y = point1[1] + fraction * (point2[1] - point1[1]);

          result.push([x, y]);
        }
      }

      return result;
    },

    // Render the similar case charts
    renderSimilarCharts(allCoordinates) {
      // Clear previous charts
      this.clearSimilarCharts();

      // Create charts for each similar case
      this.similarCases.forEach((similarCase, index) => {
        const chartDom = this.$refs[`similarChart${index}`][0];
        if (!chartDom) return;

        const chart = echarts.init(chartDom);

        // Create a smaller version of the main chart
        const option = {
          grid: {
            top: '5%',
            left: '5%',
            right: '5%',
            bottom: '5%',
            containLabel: false
          },
          tooltip: {
            trigger: 'item',
            formatter: (params) => {
              if (params.seriesName === 'Background') {
                const index = params.dataIndex;
                const caseName = this.cases[index];
                const timeStep = this.times[index];
                return `Case: ${caseName}<br/>Time: ${timeStep}<br/>Cluster: ${this.labels[index]}`;
              } else {
                const caseMap = this.buildCaseMap(this.cases);
                index = caseMap[similarCase.caseName][params.dataIndex];
                // This is for the Trajectory series
                return `Point ${params.dataIndex + 1} in ${similarCase.caseName}<br/>Cluster: ${this.labels[index]}`;
              }
            }
          },
          xAxis: {
            type: 'value',
            scale: true,
            splitLine: {
              lineStyle: { type: 'dashed' }
            }
          },
          yAxis: {
            type: 'value',
            scale: true,
            splitLine: {
              lineStyle: { type: 'dashed' }
            }
          },
          series: [
            // Background points (all points with reduced opacity)
            {
              name: 'Background',
              type: 'scatter',
              data: allCoordinates,
              symbolSize: (params) => {
                // Check if this point belongs to the selected case
                if (this.cases[params.dataIndex] === similarCase.caseName) {
                  return 6; // Bigger symbol size for selected case points
                }
                return 3; // Default size for other points
              },
              itemStyle: {
                color: 'rgba(200, 200, 200, 0.3)'
              },
              z: 1
            },
            // The similar case line
            {
              name: 'Trajectory',
              type: 'line',
              data: similarCase.trajectory,
              lineStyle: {
                color: '#3366cc',
                width: 2
              },
              symbol: 'circle',
              symbolSize: 6,
              itemStyle: {
                color: '#3366cc'
              },
              z: 10
            }
          ]
        };

        chart.setOption(option);
        chart.on('click', (params) => {
          if (params.componentType === 'series') {
            let index = params.dataIndex;
            const caseMap = this.buildCaseMap(this.cases);
            const pathmap = { p: 'p_cropped_img2/', OH: 'imgs/oh/', Mach: 'imgs/mach/' };
            const path = pathmap[this.graphObj.selectedComponent] || pathmap.p;
            if (params.seriesName === 'Trajectory') {
              index = caseMap[similarCase.caseName][index];
            }
            this.selectedPoint = index;
            this.selectedTimeStep = this.times[index]

            // Generate the image path for the selected point
            this.selectedImage = process.env.BASE_URL + path + this.fileNames[index];
            this.selectedCaseName = this.cases[index];

            // Generate images for all points in this case
            this.caseImages = caseMap[this.selectedCaseName].map(idx => {
              return {
                src: process.env.BASE_URL + path + this.fileNames[idx],
                timeStep: this.times[idx],
                isSelected: idx === index // Mark the clicked point
              };
            });
            this.caseImages.sort((a, b) => a.timeStep - b.timeStep);
          }
        });
        this.similarCharts.push(chart);
      });
    },

    // Clear similar charts to prevent memory leaks
    clearSimilarCharts() {
      this.similarCharts.forEach(chart => {
        if (chart && !chart.isDisposed()) {
          chart.dispose();
        }
      });
      this.similarCharts = [];
    },
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
    this.clearSimilarCharts();
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
  width: 100%;
  height: 100%;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-container {
  flex: 2;
  position: relative;
  height: auto;
}

.images-container {
  flex: 1;
  height: 100%;
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
  margin-top: 10px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

.point-info {
  flex-grow: 1;
}

h3 {
  margin-top: 0;
  margin-bottom: 5px;
}

.clear-button {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 8px 8px;
  border-radius: 4px;
  cursor: pointer;
  /* margin-top: 10px; */
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

/* Add these styles for the similar trajectories section */
.similar-trajectories {
  margin-top: 5px;
  border-top: 1px solid #ddd;
  padding-top: 5px;
}

.trajectories-container {
  display: flex;
  gap: 10px;
  margin-top: 5px;
}

.similar-case {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px;
  height: auto;
  /* background-color: #f9f9f9; */
}

.similar-chart {
  width: 100%;
  height: 200px
}

h4 {
  margin-top: 0;
  margin-bottom: 5px;
  font-size: 12 px;
  color: #333;
  text-align: center;
}

/* Responsive layout for smaller screens */
@media (max-width: 1200px) {
  .trajectories-container {
    flex-direction: column;
  }

  .similar-case {
    margin-bottom: 20px;
  }
}
</style>