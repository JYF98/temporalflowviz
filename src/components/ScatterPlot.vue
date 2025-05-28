<template>
  <div>
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading chart data...</div>
    </div>
    <div class="main-container">
      <!-- Left side: Chart -->
      <div class="chart-container">
        <div class="chart-controls">
          <!-- <p>Current Case: {{ selectedCaseName }}</p> -->
          <button class="control-button" @click="toggleCentroids" :class="{ 'active': showCentroids }">
            {{ showCentroids ? 'Hide Centroids' : 'Show Centroids' }}
          </button>
        </div>
        <div ref="scatterChart" style="flex: 1; height: 450px;"></div>
        <!-- Similar trajectories section -->
        <div class="similar-trajectories">
          <h3>Similar Case Trajectories</h3>
          <div class="trajectories-container">
            <div v-for="(similarCase, index) in similarCases" :key="index" class="similar-case">
              <h4>{{ similarCase.caseName }} (Diff: {{ similarCase.mse.toFixed(2) }})</h4>
              <!-- <h4>{{ similarCase.caseName }}</h4> -->
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
            <div class="image-with-time" @click="imgOnClick(image.timeStep)">
              <div class="time-label">{{ image.timeStep }}</div>
              <img :src="image.src" :alt="`${image.timeStep}`" />
            </div>
          </div>
        </div>
        <!-- Description editor section -->
        <div v-if="selectedPoint !== null" class="description-section">
          <h3>Frame Description</h3>
          <el-input type="textarea" rows="6" placeholder="No description available for this point"
            v-model="currentDescription">
          </el-input>
          <div class="description-actions">
            <el-button size="small" type="success" @click="submitDescription"
              :disabled="!descriptionChanged || submittingDescription">
              {{ submittingDescription ? 'Submitting...' : 'Save Description' }}
            </el-button>
            <el-button size="small" type="primary" @click="generateDescription">
              {{ generatingDescription ? 'Generating...' : 'Generate Description' }}
            </el-button>
            <span v-if="descriptionUpdateStatus" class="status-message" :class="descriptionUpdateStatus.type">
              {{ descriptionUpdateStatus.message }}
            </span>
          </div>
          <h3>Case Summary</h3>
          <el-input type="textarea" rows="6" placeholder="No description available for this case"
            v-model="currentCaseDescription"></el-input>
          <div class="description-actions">
            <el-button size="small" type="success" @click="submitCaseDescription"
              :disabled="!caseDescriptionChanged || submittingCaseDescription">
              {{ submittingCaseDescription ? 'Submitting...' : 'Save Description' }}
            </el-button>
            <el-button size="small" type="primary" @click="generateCaseDescription">
              {{ generatingCaseDescription ? 'Generating...' : 'Generate Description' }}
            </el-button>
            <span v-if="caseDescriptionUpdateStatus" class="status-message" :class="caseDescriptionUpdateStatus.type">
              {{ caseDescriptionUpdateStatus.message }}
            </span>
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
      case_xys_dict: {}, 
      fileNames: [], // Will hold filenames of the points
      labels: [], // Will hold cluster labels
      cases: [], // Will hold case names
      caseMap: {}, // Will hold a map of case names to their point indices
      times: [], // Will hold time steps
      iscentroid: [], // Will hold centroid information
      centroid_indices: [], // Will hold centroid indices
      showCentroids: false, // Track centroids visibility
      centroidSeries: null, // Store centroid series for toggling
      descriptions: [], // Will hold descriptions of the images
      similarCases: [], // Will hold similar cases data
      similarCharts: [], // Will hold references to the chart instances
      currentDescription: '', // Will hold the current description being edited
      originalDescription: '', // To track if description has changed
      submittingDescription: false, // Flag for submission status
      descriptionUpdateStatus: null, // For status messages
      generatingDescription: false, // Flag for generating description
      currentCaseDescription: '', // Will hold the current case description being edited
      originalCaseDescription: '', // To track if case description has changed
      submittingCaseDescription: false, // Flag for submission status
      caseDescriptionUpdateStatus: null, // For status messages
      generatingCaseDescription: false, // Flag for generating case description
    };
  },

  computed: {
    descriptionChanged() {
      return this.currentDescription !== this.originalDescription;
    },
    caseDescriptionChanged() {
      return this.currentCaseDescription !== this.originalCaseDescription;
    }
  },

  methods: {
    toggleCentroids() {
      this.showCentroids = !this.showCentroids;

      if (this.showCentroids) {
        this.showClusterCentroids();
      } else {
        this.hideClusterCentroids();
      }
    },

    showClusterCentroids() {
      if (!this.myChart || this.myChart.isDisposed() || !Array.isArray(this.iscentroid)) {
        return;
      }

      // Get current chart options
      const currentOption = this.myChart.getOption();
      const currentSeries = currentOption.series;

      // Get coordinates of centroids
      const coordinates = currentOption.series[0].data;
      const centroidCoordinates = [];
      const centroidxys = this.centroid_indices.map(index => coordinates[index]);
      const centroidlbls = this.centroid_indices.map(index => this.labels[index]);

      // Find all centroid points based on iscentroid array
      this.iscentroid.forEach((isCentroid, index) => {
        if (isCentroid === true) {
          centroidCoordinates.push({
            value: coordinates[index],
            clusterIndex: this.labels[index]
          });
        }
      });

      if (centroidCoordinates.length === 0) {
        console.warn('No centroid points found in the data');
        return;
      }

      // Create a new series for centroids
      const centroidSeries = {
        name: 'Centroids',
        type: 'scatter',
        // data: centroidCoordinates.map(point => point.value),
        data: centroidxys,
        symbolSize: 15,
        symbol: 'diamond',
        itemStyle: {
          color: (params) => {
            // const clusterIndex = centroidCoordinates[params.dataIndex].clusterIndex;
            const clusterIndex = centroidlbls[params.dataIndex];
            const cluster_count = Math.max(...this.labels) - Math.min(...this.labels) + 1;
            return `hsl(${(clusterIndex / cluster_count) * 360}, 100%, 50%)`;
          },
          borderColor: '#fff',
          borderWidth: 2,
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.3)'
        },
        z: 0,
        tooltip: {
          formatter: (params) => {
            const clusterIndex = centroidlbls[params.dataIndex];
            const index = this.centroid_indices[params.dataIndex];
            return `Centroid of Cluster ${clusterIndex}<br/>Case: ${this.cases[index]}<br/>Time: ${this.times[index]}<br/>Cluster: ${this.labels[index]}`;
          }
        }
      };

      // Store the centroid series for later toggling
      this.centroidSeries = centroidSeries;

      // Add the centroid series to the existing series array
      // This preserves the original scatter plot
      const newSeries = [...currentSeries, centroidSeries];

      // Update the chart with all series
      this.myChart.setOption({
        series: newSeries
      });
    },

    hideClusterCentroids() {
      if (!this.myChart || this.myChart.isDisposed()) {
        return;
      }

      // Get all current series except the centroid series
      const option = this.myChart.getOption();

      // Debug the series names to identify any mismatch
      console.log('Current series:', option.series.map(s => s.name));

      // Filter series more robustly to ensure centroids are removed
      const filteredSeries = option.series.filter(series => {
        return series.name !== 'Centroids';
      });

      // Update the chart with the filtered series
      option.series = filteredSeries;
      this.myChart.setOption(option, true); // Set true to completely replace series instead of merging

      // Clear the reference
      this.centroidSeries = null;
    },


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
        this.caseMap = this.buildCaseMap(this.cases);
        this.case_xys_dict = data.case_xys_dict;
        this.descriptions = data.descriptions;
        this.iscentroid = data.iscentroid;
        this.centroid_indices = data.centroid_indices;

        if (Array.isArray(coordinates) && coordinates.length > 0) {
          const option = {
            title: {
              text: 'Scatter Plot',
            },
            tooltip: {
              trigger: 'item',
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
              symbolSize: 4,
              itemStyle: {
                color: (params) => {
                  const clusterIndex = this.labels[params.dataIndex];
                  return clusterIndex < cluster_count ? `hsl(${(clusterIndex / cluster_count) * 360}, 100%, 50%)` : '#000';
                },
              },
              tooltip: {
                trigger: 'item',
                formatter: (params) => {
                  const index = params.dataIndex;
                  const caseName = this.cases[index];
                  const timeStep = this.times[index];
                  return `Case: ${caseName}<br/>Time: ${timeStep}<br/>Cluster: ${this.labels[index]}`;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.5)',
              },
            }]
          };

          // Store the original option for resetting view
          this.originalOption = JSON.parse(JSON.stringify(option));
          this.myChart.setOption(option);

          this.myChart.on('click', (params) => {
            if (params.componentType === 'series') {
              let index = 0;
              if (params.seriesName === 'Centroids') {
                index = this.centroid_indices[params.dataIndex];
                console.log('Clicked centroid:', index);
              } else if (params.seriesName === 'Scatter Data') {
                index = params.dataIndex;
                console.log('Clicked point:', index);
              } else if (params.seriesName === 'Case Line') {
                index = this.caseMap[this.selectedCaseName][params.dataIndex];
                console.log('Clicked trajectory:', params);
              }
              // console.log('Clicked params.dataIndex: ', params.dataIndex, 'Clicked index:', index, 'Series name:', params.seriesName, 'Case:', this.cases[index], 'Time:', this.times[index]);
              const fileName = this.fileNames[index];
              const caseName = this.cases[index];

              // Find all points from the same case
              const casePointIndices = this.caseMap[caseName] || [];
              console.log('Case points:', casePointIndices);

              if (casePointIndices.length > 0) {
                casePointIndices.sort((a, b) => this.times[a] - this.times[b]);
                const lineCoordinates = casePointIndices.map(idx => coordinates[idx]);
                console.log('Line coordinates:', lineCoordinates);

                // Add a line series connecting the points in time order
                const lineOption = {
                  animation: false,
                  series: [
                    // Keep the original scatter series for background points
                    {
                      id: 'main-scatter',
                      name: 'Scatter Data',
                      type: 'scatter',
                      data: coordinates,
                      symbolSize: function (value, params) {
                        // Check if this point belongs to the selected case
                        if (this.cases && this.cases[params.dataIndex] === caseName) {
                          return 6; // Bigger symbol size for selected case points
                        }
                        return 4; // Default size for other points
                      }.bind(this),
                      symbol: 'circle',
                      // emphasis: {
                      //   itemStyle: {
                      //     borderWidth: 1,
                      //     borderColor: '#000'
                      //   }
                      // },
                      z: 5 // Keep regular points in middle layer
                    },
                    // Add connecting line first (lowest z-index of active elements)
                    {
                      id: 'case-line',
                      name: 'Case Line',
                      type: 'line',
                      data: lineCoordinates,
                      lineStyle: {
                        color: '#000',
                        width: 3,
                        type: 'solid',
                      },
                      itemStyle: {
                        bordercolor: '#000',
                        color: '#000',
                        borderWidth: 1,
                      },
                      tooltip: {
                        disabled: true // Disable tooltip for line
                      },
                      symbolSize: 6,
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

                // Set the description for editing
                this.currentDescription = this.descriptions[index] || '';
                this.originalDescription = this.currentDescription;
                this.descriptionUpdateStatus = null; // Reset status message

                // Get the component path for images
                const pathmap = { p: 'p_crop_trans/', OH: 'imgs/oh_trans/', Mach: 'imgs/mach_trans/' };
                const path = 'external_images/' + (pathmap[this.graphObj.selectedComponent] || pathmap.p);
                this.selectedImage = process.env.BASE_URL + path + fileName;

                // Generate images for all points in this case
                this.caseImages = casePointIndices.map(idx => {
                  return {
                    src: process.env.BASE_URL + path + this.fileNames[idx],
                    timeStep: this.times[idx],
                    isSelected: idx === index // Mark the clicked point
                  };
                });
                // this.caseImages.sort((a, b) => a.timeStep - b.timeStep);
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

    imgOnClick(timeStep){
      this.selectedTimeStep = timeStep;
      this.selectedPoint = this.caseMap[this.selectedCaseName][timeStep-1];
      this.currentDescription = this.descriptions[this.selectedPoint] || '';
      this.originalDescription = this.currentDescription;
      this.caseImages.forEach((image, index) => {
        image.isSelected = index === timeStep - 1; // Update selected state based on timeStep
      });
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

    async submitDescription() {
      if (this.selectedPoint === null || !this.descriptionChanged) return;

      this.submittingDescription = true;
      this.descriptionUpdateStatus = null;

      try {
        // Get the filename for the current point
        const fileName = this.fileNames[this.selectedPoint];

        // Send the updated description to the server
        const response = await axios.post('http://localhost:5000/update_description', {
          index: this.selectedPoint,
          fileName: fileName,
          description: this.currentDescription,
          component: this.graphObj.selectedComponent
        });

        if (response.data.success) {
          // Update the local descriptions array
          this.descriptions[this.selectedPoint] = this.currentDescription;
          this.originalDescription = this.currentDescription;
          this.descriptionUpdateStatus = {
            type: 'success',
            message: 'Saved'
          };
        } else {
          this.descriptionUpdateStatus = {
            type: 'error',
            message: 'Failed to update description: ' + (response.data.message || 'Unknown error')
          };
        }
      } catch (error) {
        console.error('Error updating description:', error);
        this.descriptionUpdateStatus = {
          type: 'error',
          message: 'Error updating description: ' + (error.message || 'Network error')
        };
      } finally {
        this.submittingDescription = false;

        // Clear status message after a delay
        setTimeout(() => {
          if (this.descriptionUpdateStatus && this.descriptionUpdateStatus.type === 'success') {
            this.descriptionUpdateStatus = null;
          }
        }, 3000);
      }
    },

    async generateDescription() {
      if (this.selectedPoint === null) return;

      this.generatingDescription = true;
      this.descriptionUpdateStatus = null;

      try {
        // Get the filename for the current point
        const fileName = this.fileNames[this.selectedPoint];

        // Send the request to generate a description
        const response = await axios.post('http://localhost:5000/generate_description', {
          index: this.selectedPoint,
          fileName: fileName,
          caseName: this.selectedCaseName,
          timeStep: this.selectedTimeStep,
          component: this.graphObj.selectedComponent,
          cluster: this.labels[this.selectedPoint]
        });

        if (response.data.success) {
          // Update the description field with the generated description
          this.currentDescription = response.data.description;
          this.descriptionUpdateStatus = {
            type: 'success',
            message: 'Description generated successfully'
          };
        } else {
          this.descriptionUpdateStatus = {
            type: 'error',
            message: 'Failed to generate description: ' + (response.data.message || 'Unknown error')
          };
        }
      } catch (error) {
        console.error('Error generating description:', error);
        this.descriptionUpdateStatus = {
          type: 'error',
          message: 'Error generating description: ' + (error.message || 'Network error')
        };
      } finally {
        this.generatingDescription = false;

        // Clear success message after a delay
        setTimeout(() => {
          if (this.descriptionUpdateStatus && this.descriptionUpdateStatus.type === 'success') {
            this.descriptionUpdateStatus = null;
          }
        }, 3000);
      }
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
        // console.log('Cuurent Option: ', this.myChart.getOption(), 'Resetting chart to original option:', resetOption);
        this.myChart.setOption(resetOption, {replaceMerge:['series']});
        this.selectedPoint = null;
        this.selectedImage = null;
        this.selectedCaseName = null;
        this.selectedTimeStep = null;
        this.selectedCaseSeries = null;
        this.caseImages = [];
        this.currentDescription = '';
        this.originalDescription = '';
        this.descriptionUpdateStatus = null;
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
      this.similarCases = similarities.slice(1, 7);

      // Render the similar case charts after DOM update
      this.$nextTick(() => {
        this.renderSimilarCharts(allCoordinates);
      });
    },

    // Calculate trajectory similarity using Mean Squared Error between points
    calculateTrajectoryMSE(trajectory1, trajectory2) {
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
            top: '0%',
            left: '2%',
            right: '2%',
            bottom: '0%',
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
                index = this.caseMap[similarCase.caseName][params.dataIndex];
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
            },
            axisLabel: {
              show: false // Hide x-axis labels
            }
          },
          yAxis: {
            type: 'value',
            scale: true,
            splitLine: {
              lineStyle: { type: 'dashed' }
            },
            axisLabel: {
              show: false // Hide y-axis labels
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
              symbolSize: 5,
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
            const pathmap = { p: 'p_crop_trans/', OH: 'imgs/oh_trans/', Mach: 'imgs/mach_trans/' };
            const path = 'external_images/' + (pathmap[this.graphObj.selectedComponent] || pathmap.p);
            if (params.seriesName === 'Trajectory') {
              index = this.caseMap[similarCase.caseName][index];
            }
            this.selectedPoint = index;
            this.selectedTimeStep = this.times[index]

            // Set the description for editing
            this.currentDescription = this.descriptions[index] || '';
            this.originalDescription = this.currentDescription;
            this.descriptionUpdateStatus = null; // Reset status message

            // Generate the image path for the selected point
            this.selectedImage = process.env.BASE_URL + path + this.fileNames[index];
            this.selectedCaseName = this.cases[index];

            // Generate images for all points in this case
            this.caseImages = this.caseMap[this.selectedCaseName].map(idx => {
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
.chart-controls {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
  padding: 0 10px;
}

.control-button {
  background-color: #f0f0f0;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.control-button:hover {
  background-color: #e0e0e0;
}

.control-button.active {
  background-color: #4CAF50;
  color: white;
  border-color: #3e8e41;
}

.main-container {
  display: flex;
  width: 100%;
  /* height: 100%; */
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
  /* overflow-y: auto; */
  /* max-height: 500px; */
  border-left: 1px solid #ddd;
  padding-left: 10px;
}

.images-grid {
  height: 50vh;
  display: grid;
  grid-template-columns: 1fr;
  gap: 0px;
  overflow: scroll;
}

.image-item {
  width: 100%;
  border: 2px solid transparent;
  border-radius: 4px;
  /* transition: all 0.3s ease; */
}

/* .image-item img {
  height: 30px;
  display: block;
} */

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
  padding: 5px;
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
  margin-left: 8px;
  /* margin-top: 10px; */
}

.clear-button:hover {
  background-color: #d32f2f;
}

/* New styles for image-with-time and time-label */
.image-with-time {
  display: flex;
  align-items: center;
  /* gap: 2px; */
  /* width: 100%; */
  background-color: #f9f9f9;
  border: 2px;
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
  /* width: auto; */
  max-width: calc(100% - 60px);
  /* Account for label width + gap */
  height: auto;
  display: block;
}

/* Adjust the image-item to work with the new layout */
/* .image-item {
  border: 2px solid transparent;
  border-radius: 4px;
  overflow: hidden;
  transition: all 0.3s ease;
} */

.selected-image .image-with-time {
  background-color: #fff7f2;
}

.selected-image .time-label {
  background-color: #ff5500;
  color: white;
}

.similar-trajectories {
  margin-top: 5px;
  border-top: 1px solid #ddd;
  padding-top: 5px;
}

.trajectories-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr); /* 3 columns */
  grid-template-rows: repeat(2, auto);   /* 2 rows */
  gap: 10px;
  margin-top: 10px;
}

.similar-case {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px;
  /* height: auto; */
  background-color: #f9f9f9;
}

.similar-chart {
  width: 100%;
  height: 150px
}

h4 {
  margin-top: 0;
  margin-bottom: 5px;
  font-size: 12 px;
  color: #333;
  text-align: center;
}

/* Styles for the description section */

.description-section {
  margin: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 15px;
  background-color: #f9f9f9;
}

.description-textarea {
  width: 95%;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 10px;
  font-family: inherit;
  font-size: 14px;
  resize: vertical;
}

.description-actions {
  display: flex;
  align-items: center;
  margin-top: 10px;
}

.submit-button {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 4px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.submit-button:hover:not(:disabled) {
  background-color: #45a049;
}

.submit-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.status-message {
  margin-left: 15px;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 14px;
}

.success {
  background-color: #dff0d8;
  color: #3c763d;
}

.error {
  background-color: #f2dede;
  color: #a94442;
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