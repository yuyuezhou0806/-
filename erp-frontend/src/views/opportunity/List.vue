<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchOpportunities,
  closeOpportunity,
  transferOpportunity,
  fetchDepartments,
} from '@/api/opportunity'
import {
  SOURCE_OPTIONS,
  TYPE_OPTIONS,
  STATUS_OPTIONS,
  typeMap,
  statusMap,
} from './constants'

const router = useRouter()

const filters = reactive({
  keyword: '',
  type: '',
  status: '',
  source: '',
})

const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const tableData = ref([])
const loading = ref(false)

const departments = ref([])
const transferDialog = reactive({
  visible: false,
  id: null,
  selected: [],
})

const load = async () => {
  loading.value = true
  try {
    const data = await fetchOpportunities({
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

const onSearch = () => {
  pagination.page = 1
  load()
}

const onReset = () => {
  Object.assign(filters, { keyword: '', type: '', status: '', source: '' })
  onSearch()
}

const onPageChange = (page) => {
  pagination.page = page
  load()
}

const onSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  load()
}

const goCreate = () => router.push('/opportunity/create')
const goEdit = (row) => router.push(`/opportunity/edit/${row.id}`)
const goDetail = (row) => router.push(`/opportunity/detail/${row.id}`)
const goCreateContract = (row) => router.push(`/contract/create?oppId=${row.id}`)

const handleClose = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认关闭商机「${row.name}」?关闭后不再流转。`,
      '关闭商机',
      { type: 'warning' },
    )
    await closeOpportunity(row.id)
    ElMessage.success('已关闭')
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.message || '操作失败')
  }
}

const openTransfer = async (row) => {
  if (!departments.value.length) {
    departments.value = await fetchDepartments()
  }
  transferDialog.id = row.id
  transferDialog.selected = []
  transferDialog.visible = true
}

const submitTransfer = async () => {
  if (!transferDialog.selected.length) {
    ElMessage.warning('请选择至少一个部门')
    return
  }
  await transferOpportunity(transferDialog.id, transferDialog.selected)
  ElMessage.success('已流转')
  transferDialog.visible = false
  load()
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="page-card">
      <el-form :model="filters" inline @submit.prevent="onSearch">
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="商机编号 / 项目名称"
            clearable
            style="width: 220px"
            @keyup.enter="onSearch"
          />
        </el-form-item>
        <el-form-item label="商机类型">
          <el-select v-model="filters.type" placeholder="全部" clearable style="width: 140px">
            <el-option
              v-for="o in TYPE_OPTIONS"
              :key="o.value"
              :label="o.label"
              :value="o.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="项目来源">
          <el-select v-model="filters.source" placeholder="全部" clearable style="width: 120px">
            <el-option
              v-for="o in SOURCE_OPTIONS"
              :key="o.value"
              :label="o.label"
              :value="o.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 140px">
            <el-option
              v-for="o in STATUS_OPTIONS"
              :key="o.value"
              :label="o.label"
              :value="o.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="'Search'" @click="onSearch">查询</el-button>
          <el-button @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="page-card" style="margin-top: 16px">
      <div class="toolbar">
        <div>
          <el-button type="primary" :icon="'Plus'" @click="goCreate">新建商机</el-button>
          <el-button :icon="'Iphone'">移动端填报</el-button>
        </div>
        <div class="muted">
          <el-icon><InfoFilled /></el-icon>
          连续 6 个月无后续流程的商机将自动关闭
        </div>
      </div>

      <el-table v-loading="loading" :data="tableData" stripe border>
        <el-table-column prop="code" label="商机编号" width="150" fixed />
        <el-table-column prop="name" label="项目名称" min-width="220" show-overflow-tooltip />
        <el-table-column label="商机类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="typeMap[row.type]?.tag" size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="80" align="center" />
        <el-table-column prop="bidType" label="招投标类型" width="120" align="center" />
        <el-table-column label="预估金额" width="130" align="right">
          <template #default="{ row }">{{ row.amount?.toFixed(2) }} 万</template>
        </el-table-column>
        <el-table-column prop="customer" label="客户" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.tag" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="更新时间" width="170" />
        <el-table-column label="操作" width="290" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row)">详情</el-button>
            <el-button link type="primary" @click="goEdit(row)">编辑</el-button>
            <el-button
              link
              type="success"
              :disabled="row.status !== '已闭合'"
              @click="goCreateContract(row)"
            >
              发起合同
            </el-button>
            <el-button
              link
              type="primary"
              :disabled="row.status !== '进行中'"
              @click="openTransfer(row)"
            >
              流转
            </el-button>
            <el-button
              link
              type="danger"
              :disabled="['已关闭', '已流转'].includes(row.status)"
              @click="handleClose(row)"
            >
              关闭
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
          @current-change="onPageChange"
          @size-change="onSizeChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="transferDialog.visible" title="流转到部门" width="480px">
      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        流转后,商机将分配到所选部门,可在部门项目中继续跟进。支持多选。
      </el-alert>
      <el-checkbox-group v-model="transferDialog.selected">
        <div class="dept-grid">
          <el-checkbox
            v-for="d in departments"
            :key="d.id"
            :label="d.id"
            :value="d.id"
            class="dept-item"
          >
            {{ d.name }}
          </el-checkbox>
        </div>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="transferDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitTransfer">确认流转</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.muted {
  color: #909399;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.dept-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 16px;
}

.dept-item {
  margin-right: 0;
}
</style>
