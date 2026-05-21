<script setup>
defineProps({
  module: { type: String, default: '模块' },
})
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="placeholder">
      <el-empty :description="`${module}模块` ">
        <template #image>
          <el-icon style="font-size: 60px; color: #c0c4cc"><Loading /></el-icon>
        </template>
        <div class="hint">
          <p>{{ module }}模块脚手架已就位,可继续按需求文档实现表单 / 列表 / 流程</p>
          <p style="margin-top: 8px; color: #909399; font-size: 12px">
            (本次先把「商机登记」模块走通,其他模块共用主框架和组件)
          </p>
        </div>
      </el-empty>
    </el-card>
  </div>
</template>

<style scoped>
.placeholder {
  min-height: calc(100vh - 88px - 32px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.hint {
  text-align: center;
  margin-top: 12px;
  color: #606266;
}
</style>
