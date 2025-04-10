<template>
  <div>
    <button class="toggle-button" @click="toggleSidebar">
      {{ isSidebarVisible ? 'Hide Sidebar' : 'Show Sidebar' }}
    </button>
    <div :class="['sidebar', { 'sidebar-hidden': !isSidebarVisible }]">
      <div v-if="isSidebarVisible">
        <div class="filter">
          <label for="p">Pressure (Mpa):</label>
          <div class="filter-row">
            <div class="slider-container">
              <vue-slider v-model="pRange" :min="80" :max="210" :interval="5" />
            </div>
            <input type="number" v-model="pRange[0]" :min="80" :max="210" />
            <input type="number" v-model="pRange[1]" :min="80" :max="210" />
          </div>
        </div>

        <div class="filter">
          <label for="T">Temperature (K):</label>
          <div class="filter-row">
            <div class="slider-container">
              <vue-slider v-model="tRange" :min="500" :max="900" :interval="10" />
            </div>
            <input type="number" v-model="tRange[0]" :min="500" :max="900" />
            <input type="number" v-model="tRange[1]" :min="500" :max="900" />
          </div>
        </div>

        <div class="filter">
          <label for="H2O">H2O Content (%):</label>
          <div class="filter-row">
            <div class="slider-container">
              <vue-slider v-model="h2oRange" :min="0" :max="20" />
            </div>
            <input type="number" v-model="h2oRange[0]" :min="0" :max="20" />
            <input type="number" v-model="h2oRange[1]" :min="0" :max="20" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import VueSlider from 'vue-slider-component';
import 'vue-slider-component/theme/antd.css';

export default {
  name: 'SideBar',
  components: {
    VueSlider
  },
  data() {
    return {
      isSidebarVisible: true,  // Controls whether the sidebar is visible or hidden
      // Pressure (p) values
      pRange: [80, 210], // Using a range for pressure
      // Temperature (T) values
      tRange: [500, 900], // Using a range for temperature
      // H2O content values
      h2oRange: [0, 20], // Using a range for H2O content
    };
  },
  methods: {
    toggleSidebar() {
      this.isSidebarVisible = !this.isSidebarVisible;
      // Emit the filter values whenever the sidebar is toggled
      this.emitFilters();
    },
    emitFilters() {
      this.$emit('update-filters', {
        pRange: this.pRange,
        tRange: this.tRange,
        h2oRange: this.h2oRange,
      });
    }
  },
  watch: {
    // Directly call emitFilters() to update filters when the values change
    pRange() { this.emitFilters(); },
    tRange() { this.emitFilters(); },
    h2oRange() { this.emitFilters(); },
  }
};
</script>

<style scoped>
.sidebar {
  width: 300px;
  padding: 20px;
  background-color: #f5f5f5;
  height: 100vh;
  position: fixed;
  /* top: 0; */
  left: 0;
  transition: all 0.3s ease;
}

.sidebar-hidden {
  transform: translateX(-100%);
}

.toggle-button {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 10px;
  margin-bottom: 20px;
  cursor: pointer;
  display: block;
  width: 100%;
}

.filter {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 10px;
}

input[type="number"] {
  margin-top: 0;
  width: 60px;
}

.filter-row {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.slider-container {
  flex-grow: 1;
  margin-right: 10px;
}
</style>
