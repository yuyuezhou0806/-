<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchDepartmentTasks } from '@/api/department'

const router = useRouter()
const filters = reactive({ keyword: '', status: '', department: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const tableData = ref([])
const loading = ref(false)

const DEPARTMENT_OPTIONS = ['公路事业部', '水利事业部', '市政事业部', '检测事业部']
const STATUS_TAG = { 待领取: 'info', 执行中: 'warning', 已完成: 'success' }

const load = async () => {
  loading.value = true
  try {
    const data = await fetchDepartmentTasks({
      page: pagination.page, pageSize: pagination.pageSize, ...filters,
    })
    tableData.value = data.items
    pagination.total = data.total
  } finally {
    loading.value = false
  }
}

const search = () => { pagination.page = 1; load() }
const reset = () => { Object.assign(filters, { keyword: '', status: '', department: '' }); search() }

onMounted(load)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="page-card">
      <el-form :model="filters" inline @submit.prevent="search">
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="任务编号 / 项目名称" clearable style="width: 220px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="filters.department" placeholder="全部" clearable style="width: 160px">
            <el-option v-for="d in DEPARTMENT_OPTIONS" :key="d" :label="d" :value="d" />
          </el-select>
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
        <div class="info">
          <el-icon><InfoFilled /></el-icon>
          这里显示从合同流转到本部门的任务,点击「详情」填写配合费 / 材料费
        </div>
      </div>

      <el-table v-loading="loading" :data="tableData" stripe border>
        <el-table-column prop="code" label="任务编号" width="150" fixed />
        <el-table-column prop="contractCode" label="关联合同" width="150" />
        <el-table-column prop="name" label="项目名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="department" label="部门" width="130" />
        <el-table-column prop="role" label="角色" width="120" align="center" />
        <el-table-column prop="assignee" label="负责人" width="100" align="center" />
        <el-table-column label="配合费" width="100" align="right">
          <template #default="{ row }">{{ row.coopFee?.toFixed(2) }} 万</template>
        </el-table-column>
        <el-table-column label="材料费" width="100" align="right">
          <template #default="{ row }">{{ row.materialFee?.toFixed(2) }} 万</template>
        </el-table-column>
        <el-table-column prop="requireDate" label="要求完成" width="120" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="STATUS_TAG[row.status]" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/department/detail/${row.id}`)">
              {{ row.status === '已完成' ? '查看' : '填写' }}
            </el-button>
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
.info { color: #909399; font-size: 12px; display: flex; align-items: center; gap: 4px; }
</style>
