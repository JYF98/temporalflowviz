<template>
  <div>
    <el-radio-group v-model="isCollapse" style="margin-bottom: 20px;">
      <el-radio-button :label="false">展开</el-radio-button>
      <el-radio-button :label="true">收起</el-radio-button>
    </el-radio-group>
    <el-menu default-active="1-3" class="el-menu-vertical-demo" @open="handleOpen" @close="handleClose"
      :collapse="isCollapse">
      <el-submenu index="1">
        <template slot="title">
          <i class="el-icon-location"></i>
          <span slot="title">初始参数范围</span>
        </template>
        <el-menu-item-group>
          <span slot="title">静压(Mpa):</span>
          <el-menu-item index="1-1">
            <el-row :gutter="10">
              <el-col :span="12">
                <div class="grid-content"><vue-slider v-model="pRange" :min="0.8" :max="2.1" :interval="0.05" /></div>
              </el-col>
              <el-col :span="6">
                <div class="grid-content"><input type="number" v-model="pRange[0]" :min="0.8" :max="2.1" /></div>
              </el-col>
              <el-col :span="6">
                <div class="grid-content"><input type="number" v-model="pRange[1]" :min="0.8" :max="2.1" /></div>
              </el-col>
            </el-row>
          </el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group>
          <span slot="title">温度(K):</span>
          <el-menu-item index="1-2">
            <el-row :gutter="10">
              <el-col :span="12">
                <div class="grid-content"><vue-slider v-model="tRange" :min="500" :max="900" :interval="10" /></div>
              </el-col>
              <el-col :span="6">
                <div class="grid-content"><input type="number" v-model="tRange[0]" :min="500" :max="900" /></div>
              </el-col>
              <el-col :span="6">
                <div class="grid-content"><input type="number" v-model="tRange[1]" :min="500" :max="900" /></div>
              </el-col>
            </el-row>
          </el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group>
          <span slot="title">H2O含量(%):</span>
          <el-menu-item index="1-3">
            <el-row :gutter="10">
              <el-col :span="12">
                <div class="grid-content"><vue-slider v-model="h2oRange" :min="0" :max="20" /></div>
              </el-col>
              <el-col :span="6">
                <div class="grid-content"><input type="number" v-model="h2oRange[0]" :min="0" :max="20" /></div>
              </el-col>
              <el-col :span="6">
                <div class="grid-content"><input type="number" v-model="h2oRange[1]" :min="0" :max="20" /></div>
              </el-col>
            </el-row>
          </el-menu-item>
        </el-menu-item-group>
      </el-submenu>
      <el-menu-item-group>
        <span slot="title">选择Cases:</span>
        <template>
          <el-table ref="multipleTable" :data="cases" tooltip-effect="dark" style="width: 100%" height="300"
            :hidden="isCollapse" @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="55">
            </el-table-column>
            <el-table-column fixed prop="case" label="Case" width="120" show-overflow-tooltip>
            </el-table-column>
            <el-table-column prop="p" label="静压">
            </el-table-column>
            <el-table-column prop="t" label="温度">
            </el-table-column>
            <el-table-column prop="h2o" label="H2O含量">
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
          <span slot="title">聚类参数</span>
        </template>
        <el-menu-item-group>
          <span slot="title">选择分量:</span>
          <el-menu-item index="2-1">
            <el-radio-group v-model="graphObj.selectedComponent">
              <el-radio-button label="p">静压 (p)</el-radio-button>
              <el-radio-button label="OH">OH</el-radio-button>
              <el-radio-button label="Mach">马赫数 (Mach)</el-radio-button>
            </el-radio-group>
          </el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group>
          <span slot="title">DBSCAN参数:</span>
          <el-menu-item index="2-2">
            <div>
              <label>最小样本数 (minSamples):</label>
              <el-slider v-model="graphObj.minSamples" show-input>
              </el-slider>
            </div>
            <div>
              <label>邻域半径 (eps):</label>
              <el-slider v-model="graphObj.eps" show-input></el-slider>
            </div>
          </el-menu-item>
        </el-menu-item-group>
      </el-submenu>
      <el-menu-item index="3" style="text-align: center;">
        <el-button type="primary" @click="showGraph">显示图</el-button>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<style>
.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 400px;
  min-height: 400px;
}

.el-row {
  margin-bottom: 20px;

  &:last-child {
    margin-bottom: 0;
  }
}

.el-col {
  border-radius: 4px;
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
        minSamples: 5, // DBSCAN minSamples
        eps: 0.5, // DBSCAN eps
      },
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
      // Create a deep copy of the object using JSON methods
      const graphObjCopy = JSON.parse(JSON.stringify(this.graphObj));
      
      // Send the copy to the parent component
      this.$emit('show-graph', graphObjCopy);
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