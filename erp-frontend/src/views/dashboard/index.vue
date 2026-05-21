<script setup>
const stats = [
  { label: '本月新增商机', value: 23, color: '#409EFF', icon: 'Aim' },
  { label: '待跟进商机', value: 12, color: '#67C23A', icon: 'Bell' },
  { label: '招投标项目', value: 8, color: '#E6A23C', icon: 'Notification' },
  { label: '在签合同', value: 15, color: '#F56C6C', icon: 'Document' },
]

const recentList = [
  { code: 'SJ-2026-0038', name: '杭州市政道路改造检测', type: '重大', status: '进行中', time: '2026-05-13 10:24' },
  { code: 'SJ-2026-0037', name: '苏州工业园区房建评估', type: '中等', status: '已闭合', time: '2026-05-12 16:51' },
  { code: 'SJ-2026-0036', name: '宁波港水运咨询', type: '一般', status: '已流转', time: '2026-05-12 09:30' },
  { code: 'SJ-2026-0035', name: '无锡地铁三号线检测', type: '重大', status: '进行中', time: '2026-05-11 14:20' },
]

const typeTag = (t) => ({ 一般: '', 中等: 'warning', 重大: 'danger' }[t] || '')
const statusTag = (s) =>
  ({ 进行中: 'primary', 已闭合: 'success', 已流转: 'info', 已关闭: 'info' }[s] || '')
</script>

<template>
  <div class="page-container">
    <el-row :gutter="16">
      <el-col v-for="item in stats" :key="item.label" :xs="12" :md="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-body">
            <div class="stat-icon" :style="{ background: item.color }">
              <el-icon><component :is="item.icon" /></el-icon>
            </div>
            <div class="stat-text">
              <div class="stat-label">{{ item.label }}</div>
              <div class="stat-value">{{ item.value }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="block">
      <template #header>
        <div class="block-header">
          <span>最近商机</span>
          <el-button text type="primary" @click="$router.push('/opportunity/list')">
            查看更多
          </el-button>
        </div>
      </template>
      <el-table :data="recentList" stripe>
        <el-table-column prop="code" label="商机编号" width="160" />
        <el-table-column prop="name" label="项目名称" min-width="220" />
        <el-table-column label="商机类型" width="120">
          <template #default="{ row }">
            <el-tag :type="typeTag(row.type)" size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="time" label="更新时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.stat-card {
  margin-bottom: 16px;
}

.stat-body {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
}

.stat-label {
  color: #909399;
  font-size: 13px;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.block {
  margin-top: 8px;
}

.block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
