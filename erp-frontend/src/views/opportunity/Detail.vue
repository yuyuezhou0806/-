<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  closeOpportunity,
  fetchDepartments,
  fetchOpportunity,
  transferOpportunity,
} from '@/api/opportunity'
import { typeMap, statusMap } from './constants'

const route = useRoute()
const router = useRouter()

const detail = ref(null)
const loading = ref(false)
const departments = ref([])

const transferDialog = ref({ visible: false, selected: [] })

const deptNames = computed(() => {
  if (!detail.value?.transferDepts?.length) return '-'
  return detail.value.transferDepts
    .map((id) => departments.value.find((d) => d.id === id)?.name || id)
    .join('、')
})

const load = async () => {
  loading.value = true
  try {
    const [data, depts] = await Promise.all([
      fetchOpportunity(route.params.id),
      departments.value.length ? Promise.resolve(departments.value) : fetchDepartments(),
    ])
    detail.value = data
    departments.value = depts
  } finally {
    loading.value = false
  }
}

const handleClose = async () => {
  await ElMessageBox.confirm(
    `确认关闭商机「${detail.value.name}」?`,
    '关闭商机',
    { type: 'warning' },
  )
  await closeOpportunity(detail.value.id)
  ElMessage.success('已关闭')
  load()
}

const openTransfer = () => {
  transferDialog.value = { visible: true, selected: [] }
}

const submitTransfer = async () => {
  if (!transferDialog.value.selected.length) {
    ElMessage.warning('请选择至少一个部门')
    return
  }
  await transferOpportunity(detail.value.id, transferDialog.value.selected)
  ElMessage.success('已流转')
  transferDialog.value.visible = false
  load()
}

onMounted(load)
</script>

<template>
  <div class="page-container" v-loading="loading">
    <el-card v-if="detail" shadow="never" class="page-card">
      <template #header>
        <div class="card-header">
          <div class="title">
            <span class="name">{{ detail.name }}</span>
            <el-tag :type="typeMap[detail.type]?.tag" size="small">{{ detail.type }}</el-tag>
            <el-tag :type="statusMap[detail.status]?.tag" size="small">
              {{ detail.status }}
            </el-tag>
          </div>
          <div>
            <el-button @click="router.push('/opportunity/list')">返回</el-button>
            <el-button @click="router.push(`/opportunity/edit/${detail.id}`)">编辑</el-button>
            <el-button
              type="success"
              :disabled="detail.status !== '已闭合'"
              @click="router.push(`/contract/create?oppId=${detail.id}`)"
            >
              发起合同
            </el-button>
            <el-button
              type="primary"
              :disabled="detail.status !== '进行中'"
              @click="openTransfer"
            >
              流转
            </el-button>
            <el-button
              type="danger"
              plain
              :disabled="['已关闭', '已流转'].includes(detail.status)"
              @click="handleClose"
            >
              关闭
            </el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="商机编号">{{ detail.code }}</el-descriptions-item>
        <el-descriptions-item label="项目来源">{{ detail.source }}</el-descriptions-item>
        <el-descriptions-item label="招投标类型">{{ detail.bidType }}</el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ detail.customer }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{ detail.contact || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ detail.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="预估金额">
          {{ detail.amount?.toFixed(2) }} 万元
        </el-descriptions-item>
        <el-descriptions-item label="是否需要招投标">
          {{ detail.needBid ? '是' : '否' }}
        </el-descriptions-item>
        <el-descriptions-item label="流转部门">{{ deptNames }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ detail.createdBy }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detail.createdAt }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ detail.updatedAt }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="3">
          {{ detail.remark || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="section">
        <h4>附件</h4>
        <el-empty v-if="!detail.attachments?.length" description="暂无附件" :image-size="60" />
        <ul v-else class="attach-list">
          <li v-for="(f, idx) in detail.attachments" :key="idx">
            <el-icon><Document /></el-icon>
            {{ f.name }}
          </li>
        </ul>
      </div>

      <div class="section">
        <h4>流转记录</h4>
        <el-timeline>
          <el-timeline-item :timestamp="detail.createdAt" type="primary">
            创建商机 · {{ detail.createdBy }}
          </el-timeline-item>
          <el-timeline-item
            v-if="detail.status === '已流转'"
            :timestamp="detail.updatedAt"
            type="success"
          >
            流转到部门:{{ deptNames }}
          </el-timeline-item>
          <el-timeline-item
            v-if="detail.status === '已关闭'"
            :timestamp="detail.updatedAt"
            type="danger"
          >
            商机已关闭
          </el-timeline-item>
          <el-timeline-item
            v-if="detail.status === '已闭合'"
            :timestamp="detail.updatedAt"
            type="success"
          >
            商机已闭合,等待后续流程
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>

    <el-dialog v-model="transferDialog.visible" title="流转到部门" width="480px">
      <el-checkbox-group v-model="transferDialog.selected">
        <div class="dept-grid">
          <el-checkbox
            v-for="d in departments"
            :key="d.id"
            :value="d.id"
            :label="d.id"
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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.title .name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.section {
  margin-top: 24px;
}
.section h4 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #606266;
  border-left: 3px solid #409eff;
  padding-left: 8px;
}
.attach-list {
  padding-left: 0;
  list-style: none;
}
.attach-list li {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 0;
  color: #409eff;
  cursor: pointer;
}
.dept-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 16px;
}
</style>
