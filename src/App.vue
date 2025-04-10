<template>
  <div id="app">
    <div class="main-content">
      <Sidebar @update-filters="updateFilters" />
      <div class="chart-container">
        <ScatterPlot :filters="filters" />
      </div>
    </div>
  </div>
</template>

<script>
import Sidebar from './components/SideBar.vue';
import ScatterPlot from './components/ScatterPlot.vue';

export default {
  name: 'App',
  components: {
    Sidebar,
    ScatterPlot
  },
  data() {
    return {
      filters: {
        pRange: [80, 210],
        tRange: [500, 900],
        h2oRange: [0, 20]
      }
    };
  },
  methods: {
    updateFilters(newFilters) {
      this.filters = newFilters;
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
