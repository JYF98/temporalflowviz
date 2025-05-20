<template>
  <div>
    <el-radio-group v-model="isCollapse" style="margin-bottom: 20px;">
      <el-radio-button :label="false">Expand</el-radio-button>
      <el-radio-button :label="true">Wrap</el-radio-button>
    </el-radio-group>
    <el-menu default-active="2-1" class="el-menu-vertical-demo" @open="handleOpen" @close="handleClose"
      :collapse="isCollapse" :default-openeds="['1', '2']">
      <el-submenu index="1">
        <template slot="title">
          <i class="el-icon-location"></i>
          <span slot="title">Initial parameters filters</span>
        </template>
        <el-menu-item-group>
          <span slot="title">P (Mpa):</span>
          <el-menu-item index="1-1" style="position: relative;">
            <el-row :gutter="10">
              <el-col :span="12">
                <div class="grid-content slider-container">
                  <vue-slider v-model="pRange" :min="0.8" :max="2.1" :interval="0.05"/>
                </div>
              </el-col>
              <el-col :span="6">
              <div class="grid-content" style="display: flex; align-items: center; height: 100%;">
                <input class="myinput" type="number" v-model="pRange[0]" :min="0.8" :max="2.1" style="width: 100%;"/>
              </div>
              </el-col>
              <el-col :span="6">
                <div class="grid-content" style="display: flex; align-items: center; height: 100%;">
                  <input class="myinput" type="number" v-model="pRange[1]" :min="0.8" :max="2.1" style="width: 100%;" />
                </div>
              </el-col>
            </el-row>
          </el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group>
          <span slot="title">Temperature (K):</span>
          <el-menu-item index="1-2">
            <el-row :gutter="10">
              <el-col :span="12">
                <div class="grid-content slider-container"><vue-slider v-model="tRange" :min="500" :max="900" :interval="10" /></div>
              </el-col>
              <el-col :span="6">
                <div class="grid-content"><input class="myinput" type="number" v-model="tRange[0]" :min="500" :max="900" /></div>
              </el-col>
              <el-col :span="6">
                <div class="grid-content"><input class="myinput" type="number" v-model="tRange[1]" :min="500" :max="900" /></div>
              </el-col>
            </el-row>
          </el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group>
          <span slot="title">H2O (%):</span>
          <el-menu-item index="1-3">
            <el-row :gutter="10">
              <el-col :span="12">
                <div class="grid-content  slider-container"><vue-slider v-model="h2oRange" :min="0" :max="20" /></div>
              </el-col>
              <el-col :span="6">
                <div class="grid-content"><input class="myinput" type="number" v-model="h2oRange[0]" :min="0" :max="20" /></div>
              </el-col>
              <el-col :span="6">
                <div class="grid-content"><input class="myinput" type="number" v-model="h2oRange[1]" :min="0" :max="20" /></div>
              </el-col>
            </el-row>
          </el-menu-item>
        </el-menu-item-group>
      </el-submenu>
      <el-menu-item-group>
        <span slot="title">Selected Cases:</span>
        <template>
          <el-table ref="multipleTable" :data="cases" tooltip-effect="dark" 
            style="width: 100%" height="200" 
            :row-style="{height:0+'px'}"
            :cell-style="{padding:0+'px'}"
            :header-cell-style="{padding:'0px'}"
            :hidden="isCollapse" @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="55">
            </el-table-column>
            <el-table-column sortable fixed prop="case" label="Case" width="120" show-overflow-tooltip>
            </el-table-column>
            <el-table-column sortable prop="p" label="P">
            </el-table-column>
            <el-table-column sortable prop="t" label="T">
            </el-table-column>
            <el-table-column sortable prop="h2o" label="H2O">
            </el-table-column>
          </el-table>
          <!-- <div style="margin-top: 20px">
            <el-button @click="toggleSelection([cases[1], cases[2]])">切换第二、第三行的选中状态</el-button>
            <el-button @click="toggleSelection()">取消选择</el-button>
          </div> -->
        </template>
      </el-menu-item-group>
      <el-submenu index="2">
        <template slot="title">
          <i class="el-icon-location"></i>
          <span slot="title">Clustering Parameters</span>
        </template>
        <el-menu-item-group>
          <span slot="title">Selected Component:</span>
          <el-menu-item index="2-1">
            <el-radio-group v-model="graphObj.selectedComponent" size="small">
              <el-radio-button label="p">p</el-radio-button>
              <el-radio-button label="OH">OH</el-radio-button>
              <el-radio-button label="Mach">Mach</el-radio-button>
            </el-radio-group>
          </el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group>
          <span slot="title">DBSCAN Parameters:</span>
          <el-menu-item index="2-2">
            <div>
              <label>minSamples:</label>
              <el-slider v-model="graphObj.minSamples" show-input>
              </el-slider>
            </div>
            <div>
              <label>eps:</label>
              <el-slider v-model="graphObj.eps" show-input></el-slider>
            </div>
          </el-menu-item>
        </el-menu-item-group>
      </el-submenu>
      <el-menu-item index="3" style="text-align: center;">
        <el-button type="primary" @click="showGraph">Draw Scatter Plot</el-button>
      </el-menu-item>
      <!-- <el-menu-item index="4">
        <el-upload
          ref="upload"
          :limit=1
          action="http://localhost:5000/imgsearch"
          accept="image/jpeg,image/jpg,image/png"
          :on-preview="handlePreview"
          :on-remove="handleRemove"
          :on-change="handleLimit"
          :file-list="fileList"
          list-type="picture-card"
          :auto-upload="false">
          <el-button slot="trigger" size="small" type="primary">Select Image</el-button>
          <div slot="tip" class="el-upload__tip">jpg/jpeg/png only</div>
          <el-button style="margin: 10px auto; display: block;" size="small" type="success" @click="submitUpload">Upload</el-button>
        </el-upload>
      </el-menu-item> -->
    </el-menu>
  </div>
</template>

<style>
.myinput {
  border-radius: 5px; 
  border-color: darkgray;
  text-indent: 0.3em;
}

.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 400px;
  height: auto;
}

.el-row {
  margin-bottom: 0px;

  &:last-child {
    margin-bottom: 0;
  }
}

.el-col {
  border-radius: 4px;
}

.el-table .cell {
  padding-top: 4px;
  padding-bottom: 4px;
}

/* For even more compact rows*/
.el-table .cell {
  line-height: 18px;
}

/* Make the entire table more compact */
.el-table td, .el-table th {
  padding: 6px 0;
}

.bg-purple-dark {
  background: #99a9bf;
}

.bg-purple {
  background: #d3dce6;
}

.bg-purple-light {
  background: #e5e9f2;
}

.grid-content {
  border-radius: 4px;
  min-height: 36px;
}

.row-bg {
  padding: 10px 0;
  background-color: #f9fafc;
}

/* Add this new class to center the slider */
.slider-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 0 10px;
}

/* Make the slider itself take up appropriate width */
.vue-slider {
  width: 90% !important; /* Override any inline width */
  max-width: 250px;
  margin: 0 auto;
}
</style>

<script>
import VueSlider from 'vue-slider-component';
import 'vue-slider-component/theme/antd.css';
import axios from 'axios';

export default {
  name: "side-bar-2",
  components: {
    VueSlider
  },
  data() {
    return {
      pRange: [0.8, 2.1], // Using a range for pressure
      tRange: [500, 900], // Using a range for temperature
      h2oRange: [0, 20], // Using a range for H2O content
      isCollapse: false,
      cases: [],
      graphObj: {
        selectedCases: [],
        selectedComponent: 'p', // Default selected component
        minSamples: 20, // DBSCAN minSamples
        eps: 1.5, // DBSCAN eps
      },
      fileList: [],
      uploadDisabled: false,
    };
  },
  created() {
    this.fetchCases(); // Fetch cases when the component is created
  },
  methods: {
    handleOpen(key, keyPath) {
      console.log(key, keyPath);
    },

    handleClose(key, keyPath) {
      console.log(key, keyPath);
    },

    handleLimit(fileList) {
      if (fileList.length >= 1) {
        this.uploadDisabled = true;
      } else {
        this.uploadDisabled = false;
      }
    },

    emitFilters() {
      this.$emit('update-filters', {
        pRange: this.pRange,
        tRange: this.tRange,
        h2oRange: this.h2oRange,
      });
      this.fetchCases(); // Fetch cases whenever filters are updated
    },

    async fetchCases() {
      try {
        //send ranges to backend
        const response = await axios.post('http://localhost:5000/cases', {
          pRange: this.pRange,
          tRange: this.tRange,
          h2oRange: this.h2oRange
        });
        this.cases = response.data;
        console.log('Fetched cases:', this.cases);
      } catch (error) {
        console.error('Error fetching cases:', error);
      }
    },

    toggleSelection(rows) {
      if (rows) {
        rows.forEach(row => {
          this.$refs.multipleTable.toggleRowSelection(row);
        });
      } else {
        this.$refs.multipleTable.clearSelection();
      }
    },

    handleSelectionChange(val) {
      this.graphObj.selectedCases = val;
    },

    showGraph() {
      const graphObjCopy = JSON.parse(JSON.stringify(this.graphObj)); //deep copy
      this.$emit('show-graph', graphObjCopy);
    },

    submitUpload() {
      this.$refs.upload.submit();
    },
    
    handleRemove(file, fileList) {
      console.log(file, fileList);
    },

    handlePreview(file) {
      console.log(file);
    }
  },
  watch: {
    // Directly call emitFilters() to update filters when the values change
    pRange() { this.emitFilters(); },
    tRange() { this.emitFilters(); },
    h2oRange() { this.emitFilters(); },
  }
}
</script>