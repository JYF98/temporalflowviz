<template>
  <div id="app">
    <div class="main-content">
      <!-- <Sidebar @update-filters="updateFilters" /> -->
      <side-bar-2 @show-graph="handleShowGraph"/>
      <div class="chart-container">
        <ScatterPlot :graphObj="graphObj" />
      </div>
    </div>
  </div>
</template>

<script>
// import Sidebar from './components/SideBar.vue';
import SideBar2 from './components/SideBar2.vue';
import ScatterPlot from './components/ScatterPlot.vue';

export default {
  name: 'App',
  components: {
    SideBar2,
    ScatterPlot
  },
  data() {
    return {
      filters: {
        pRange: [80, 210],
        tRange: [500, 900],
        h2oRange: [0, 20]
      },
      // selectedCasesToDisplay: [],
      // selectedComponent: 'p', // Default selected component
      graphObj: {
        // selectedCases: [],
        // selectedComponent: 'p', // Default selected component
        // minSamples: 5, // DBSCAN minSamples
        // eps: 0.5, // DBSCAN eps
      },
    };
  },
  methods: {
    updateFilters(newFilters) {
      this.filters = newFilters;
    },
    handleShowGraph(graphObj) {
      this.graphObj = JSON.parse(JSON.stringify(graphObj));
    }
  }
};
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  /* overflow: auto;  */
}

#app {
  padding: 5px;
  display: flex;
  /* overflow: auto;  */
}

.main-content {
  display: flex;
  flex-direction: row;
  width: 100%;
  /* height: 100%; This now works because parent has explicit height */
}

.chart-container {
  flex-grow: 1;
  /* height: 100%; Full height of the parent */
  /* overflow: auto; Add scrolling here if needed */
}
</style>
