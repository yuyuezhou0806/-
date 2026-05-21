<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchProject } from '@/api/project'

const route = useRoute()
const router = useRouter()
const detail = ref(null)
const loading = ref(false)

const STATUS_TAG = { 立项中: 'warning', 已立项: 'success', 已驳回: 'danger' }

const load = async () => {
  loading.value = true
  try {
    detail.value = await fetchProject(route.params.id)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page-container" v-loading="loading">
    <el-card v-if="detail" shadow="never" class="page-card">
      <template #header>
        <div class="header">
          <div class="title">
            <span class="name">{{ detail.name }}</span>
            <el-tag :type="STATUS_TAG[detail.status]" size="small">{{ detail.status }}</el-tag>
          </div>
          <el-button @click="router.push('/project/list')">返回</el-button>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="立项编号">{{ detail.code }}</el-descriptions-item>
        <el-descriptions-item label="关联合同">{{ detail.contractCode }}</el-descriptions-item>
        <el-descriptions-item label="项目经理">{{ detail.manager }}</el-descriptions-item>
        <el-descriptions-item label="承办部门">{{ detail.department }}</el-descriptions-item>
        <el-descriptions-item label="立项金额">{{ detail.amount?.toFixed(2) }} 万元</el-descriptions-item>
        <el-descriptions-item label="项目周期">{{ detail.startDate }} ~ {{ detail.endDate }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detail.createdAt }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="3">{{ detail.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; }
.title { display: flex; align-items: center; gap: 8px; }
.title .name { font-size: 16px; font-weight: 600; color: #303133; }
</style>
