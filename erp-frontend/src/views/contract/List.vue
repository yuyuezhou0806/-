<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { archiveContract, fetchContracts } from '@/api/contract'

const router = useRouter()
const filters = reactive({ keyword: '', status: '', level: '', archiveStatus: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const tableData = ref([])
const loading = ref(false)

const LEVEL_TAG = { 一般: '', 中等: 'warning', 重大: 'danger' }
const STATUS_TAG = { 未提交: 'info', 审批中: 'warning', 已完成: 'success' }
const ARCHIVE_TAG = { 未归档: 'info', 部分归档: 'warning', 已归档: 'success' }

const load = async () => {
  loading.value = true
  try {
    const data = await fetchContracts({
      page: pagination.page,
      pageSize: pagination.pageSize,
      ...filters,
    })
    tableData.value = data.items
    pagination.total = data.total
  } finally {
    loading.value = false
  }
}

const search = () => { pagination.page = 1; load() }
const reset = () => { Object.assign(filters, { keyword: '', status: '', level: '', archiveStatus: '' }); search() }

const archive = async (row) => {
  const next = row.archiveStatus === '未归档' ? '部分归档'
    : row.archiveStatus === '部分归档' ? '已归档' : '已归档'
  await archiveContract(row.id, next)
  ElMessage.success(`已更新归档状态:${next}`)
  load()
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="page-card">
      <el-form :model="filters" inline @submit.prevent="search">
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="合同编号 / 项目名称" clearable style="width: 220px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="合同等级">
          <el-select v-model="filters.level" placeholder="全部" clearable style="width: 120px">
            <el-option v-for="l in Object.keys(LEVEL_TAG)" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 120px">
            <el-option v-for="s in Object.keys(STATUS_TAG)" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="归档">
          <el-select v-model="filters.archiveStatus" placeholder="全部" clearable style="width: 120px">
            <el-option v-for="a in Object.keys(ARCHIVE_TAG)" :key="a" :label="a" :value="a" />
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
        <el-button type="primary" :icon="'Plus'" @click="router.push('/contract/create')">
          发起合同
        </el-button>
        <div class="muted">一般/中等走 4 级审批 · 重大需总经理终审</div>
      </div>

      <el-table v-loading="loading" :data="tableData" stripe border>
        <el-table-column prop="code" label="合同编号" width="150" fixed />
        <el-table-column prop="name" label="项目名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="manager" label="项目经理" width="100" align="center" />
        <el-table-column label="等级" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="LEVEL_TAG[row.level]" size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="收入预估" width="130" align="right">
          <template #default="{ row }">{{ row.revenue?.toFixed(2) }} 万</template>
        </el-table-column>
        <el-table-column label="成本预估" width="130" align="right">
          <template #default="{ row }">
            {{
              (
                (row.cost?.labor || 0) +
                (row.cost?.coop || 0) +
                (row.cost?.material || 0) +
                (row.cost?.other || 0)
              ).toFixed(2)
            }}

          </template>
        </el-table-column>
        <el-table-column label="备案合同" width="90" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.hasArchiveContract" style="color: #67c23a"><CircleCheckFilled /></el-icon>
            <el-icon v-else style="color: #c0c4cc"><RemoveFilled /></el-icon>
          </template>
        </el-table-column>
        <el-table-column label="支付合同" width="90" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.hasPaymentContract" style="color: #67c23a"><CircleCheckFilled /></el-icon>
            <el-icon v-else style="color: #c0c4cc"><RemoveFilled /></el-icon>
          </template>
        </el-table-column>
        <el-table-column label="归档" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="ARCHIVE_TAG[row.archiveStatus]" size="small">{{ row.archiveStatus }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="STATUS_TAG[row.status]" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/contract/detail/${row.id}`)">详情</el-button>
            <el-button link type="primary" :disabled="row.status === '已完成'">编辑</el-button>
            <el-button link type="primary" :disabled="row.archiveStatus === '已归档'" @click="archive(row)">
              归档
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
.muted { color: #909399; font-size: 12px; }
</style>
