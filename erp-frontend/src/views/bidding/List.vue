<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchBiddings, updateBiddingResult } from '@/api/bidding'

const router = useRouter()

const filters = reactive({ keyword: '', status: '', bidType: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const tableData = ref([])
const loading = ref(false)

const STATUS_TAG = {
  制作中: 'warning',
  待提交: '',
  已提交: 'primary',
  已中标: 'success',
  未中标: 'info',
}

const load = async () => {
  loading.value = true
  try {
    const data = await fetchBiddings({
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
const reset = () => { Object.assign(filters, { keyword: '', status: '', bidType: '' }); search() }
const goDetail = (row) => router.push(`/bidding/detail/${row.id}`)
const goLibrary = () => router.push('/bidding/library')

const markResult = async (row, isWon) => {
  await updateBiddingResult(row.id, isWon)
  ElMessage.success(isWon ? '已标记中标' : '已标记未中标')
  load()
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="page-card">
      <el-form :model="filters" inline @submit.prevent="search">
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="编号 / 项目名称"
            clearable
            style="width: 220px"
            @keyup.enter="search"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.bidType" placeholder="全部" clearable style="width: 140px">
            <el-option label="招投标" value="招投标" />
            <el-option label="销售报价" value="销售报价" />
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
        <el-button type="primary" :icon="'Collection'" @click="goLibrary">范本库管理</el-button>
        <div class="muted">从已闭合的商机自动生成招投标任务,在详情页分配人员制作</div>
      </div>

      <el-table v-loading="loading" :data="tableData" stripe border>
        <el-table-column prop="code" label="招投标编号" width="150" fixed />
        <el-table-column prop="oppCode" label="关联商机" width="150" />
        <el-table-column prop="name" label="项目名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="bidType" label="类型" width="100" align="center" />
        <el-table-column label="是否答疑" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.needQuery ? 'warning' : 'info'" size="small">
              {{ row.needQuery ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="queryTime" label="答疑时间" width="160" />
        <el-table-column label="任务分配" width="180">
          <template #default="{ row }">
            <span v-if="row.assignees?.length">{{ row.assignees.join('、') }}</span>
            <el-tag v-else size="small" type="info">未分配</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="STATUS_TAG[row.status]" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row)">详情</el-button>
            <el-button
              link
              type="success"
              :disabled="!['制作中', '待提交', '已提交'].includes(row.status)"
              @click="markResult(row, true)"
            >
              中标
            </el-button>
            <el-button
              link
              type="danger"
              :disabled="!['制作中', '待提交', '已提交'].includes(row.status)"
              @click="markResult(row, false)"
            >
              未中标
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
