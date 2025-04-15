<template>
  <div id="app">
    <div class="main-content">
      <!-- <Sidebar @update-filters="updateFilters" /> -->
      <side-bar-2 @show-graph="handleShowGraph"/>
      <div class="chart-container">
        <ScatterPlot :selectedCases="selectedCasesToDisplay" :selected-component="selectedComponent" />
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
      selectedCasesToDisplay: [],
      selectedComponent: 'p', // Default selected component
    };
  },
  methods: {
    updateFilters(newFilters) {
      this.filters = newFilters;
    },
    handleShowGraph(selectedCases, selectedComponent) {
      this.selectedCasesToDisplay = selectedCases;
      this.selectedComponent = selectedComponent;
    }
  }
};
</script>

<style>
#app {
  display: flex;
}

.main-content {
  display: flex;
  flex-direction: row;
  width: 100%;
}

.chart-container {
  flex-grow: 1;
  margin-left: 320px; /* Make space for the sidebar */
}
</style>
