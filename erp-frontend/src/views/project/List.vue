<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchProjects } from '@/api/project'

const router = useRouter()
const filters = reactive({ keyword: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const tableData = ref([])
const loading = ref(false)

const STATUS_TAG = { 立项中: 'warning', 已立项: 'success', 已驳回: 'danger' }

const load = async () => {
  loading.value = true
  try {
    const data = await fetchProjects({
      page: pagination.page, pageSize: pagination.pageSize, ...filters,
    })
    tableData.value = data.items
    pagination.total = data.total
  } finally {
    loading.value = false
  }
}

const search = () => { pagination.page = 1; load() }
const reset = () => { Object.assign(filters, { keyword: '', status: '' }); search() }

onMounted(load)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="page-card">
      <el-form :model="filters" inline @submit.prevent="search">
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="立项编号 / 项目名称" clearable style="width: 220px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="s in Object.keys(STATUS_TAG)" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="page-card" style="margin-top: 16px">
      <div class="toolbar">
        <el-button type="primary" :icon="'Plus'" @click="router.push('/project/create')">新建立项</el-button>
        <div class="muted">合同审批通过后自动生成立项任务,可手动新建</div>
      </div>

      <el-table v-loading="loading" :data="tableData" stripe border>
        <el-table-column prop="code" label="立项编号" width="150" fixed />
        <el-table-column prop="contractCode" label="关联合同" width="150" />
        <el-table-column prop="name" label="项目名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="manager" label="项目经理" width="100" align="center" />
        <el-table-column prop="department" label="承办部门" width="140" />
        <el-table-column label="立项金额" width="130" align="right">
          <template #default="{ row }">{{ row.amount?.toFixed(2) }} 万</template>
        </el-table-column>
        <el-table-column label="项目周期" width="220">
          <template #default="{ row }">{{ row.startDate }} ~ {{ row.endDate }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="STATUS_TAG[row.status]" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/project/detail/${row.id}`)">详情</el-button>
            <el-button link type="primary" :disabled="row.status === '已立项'">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pagination">
        <el-pagination
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="(p) => { pagination.page = p; load() }"
          @size-change="(s) => { pagination.pageSize = s; pagination.page = 1; load() }"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.muted { color: #909399; font-size: 12px; }
</style>
