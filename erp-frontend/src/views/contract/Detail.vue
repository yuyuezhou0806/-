<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { archiveContract, fetchContract } from '@/api/contract'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const detail = ref(null)
const loading = ref(false)

const LEVEL_TAG = { 一般: '', 中等: 'warning', 重大: 'danger' }
const STATUS_TAG = { 未提交: 'info', 审批中: 'warning', 已完成: 'success' }
const ARCHIVE_TAG = { 未归档: 'info', 部分归档: 'warning', 已归档: 'success' }

const costTotal = computed(() => {
  if (!detail.value?.cost) return 0
  const c = detail.value.cost
  return (c.labor || 0) + (c.coop || 0) + (c.material || 0) + (c.other || 0)
})

const grossProfit = computed(() => (detail.value?.revenue || 0) - costTotal.value)

const approvalSteps = computed(() => {
  if (!detail.value) return []
  const base = ['营销中心分配', '项目经理填写', '配合/材料人员填写', '营销中心审核']
  return detail.value.level === '重大' ? [...base, '总经理终审'] : base
})

const currentStep = computed(() => {
  if (!detail.value) return 0
  if (detail.value.status === '已完成') return approvalSteps.value.length
  return detail.value.approvals?.length || 0
})

const load = async () => {
  loading.value = true
  try {
    detail.value = await fetchContract(route.params.id)
  } finally {
    loading.value = false
  }
}

const archive = async () => {
  const next = detail.value.archiveStatus === '未归档' ? '部分归档' : '已归档'
  await archiveContract(detail.value.id, next)
  ElMessage.success(`已更新归档状态:${next}`)
  load()
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
            <el-tag :type="LEVEL_TAG[detail.level]" size="small">{{ detail.level }}</el-tag>
            <el-tag :type="STATUS_TAG[detail.status]" size="small">{{ detail.status }}</el-tag>
            <el-tag :type="ARCHIVE_TAG[detail.archiveStatus]" size="small">{{ detail.archiveStatus }}</el-tag>
          </div>
          <div>
            <el-button @click="router.push('/contract/list')">返回</el-button>
            <el-button
              type="primary"
              :disabled="detail.archiveStatus === '已归档'"
              @click="archive"
            >归档</el-button>
          </div>
        </div>
      </template>

      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step v-for="s in approvalSteps" :key="s" :title="s" />
      </el-steps>

      <el-divider content-position="left">合同信息</el-divider>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="合同编号">{{ detail.code }}</el-descriptions-item>
        <el-descriptions-item label="备案号">{{ detail.archiveNumber || '-' }}</el-descriptions-item>
        <el-descriptions-item label="关联商机">{{ detail.oppCode }}</el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ detail.customer || '-' }}</el-descriptions-item>
        <el-descriptions-item label="项目经理">{{ detail.manager }}</el-descriptions-item>
        <el-descriptions-item label="合同类型">{{ detail.contractType }}</el-descriptions-item>
        <el-descriptions-item label="计价类型">{{ detail.priceType }}</el-descriptions-item>
        <el-descriptions-item label="合同折扣">{{ (detail.discount * 100).toFixed(0) }}%</el-descriptions-item>
        <el-descriptions-item label="付款方">{{ detail.payee || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备案合同">
          <el-tag :type="detail.hasArchiveContract ? 'success' : 'info'" size="small">
            {{ detail.hasArchiveContract ? '已上传' : '未上传' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="支付合同">
          <el-tag :type="detail.hasPaymentContract ? 'success' : 'info'" size="small">
            {{ detail.hasPaymentContract ? '已上传' : '未上传' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">收入构成(各事业部金额,单位:万元)</el-divider>
      <el-table :data="[detail.divisionAmounts]" border size="small">
        <el-table-column
          v-for="(amount, division) in detail.divisionAmounts"
          :key="division"
          :label="division"
          :prop="division"
          align="right"
        >
          <template #default>{{ Number(amount).toFixed(2) }}</template>
        </el-table-column>
      </el-table>
      <div class="summary">
        <span>收入合计:</span>
        <strong class="green">{{ detail.revenue?.toFixed(2) }} 万元</strong>
      </div>

      <el-divider content-position="left">成本构成(单位:万元)</el-divider>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="劳务费">{{ detail.cost?.labor?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="配合费">{{ detail.cost?.coop?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="材料费">{{ detail.cost?.material?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="其它">{{ detail.cost?.other?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="配合人员" :span="2">
          {{ detail.coopMembers?.join('、') || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="材料人员" :span="2">
          {{ detail.materialMembers?.join('、') || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      <div class="summary">
        <span>成本合计:</span>
        <strong class="red">{{ costTotal.toFixed(2) }} 万元</strong>
        <span style="margin-left: 24px">毛利:</span>
        <strong :class="grossProfit >= 0 ? 'green' : 'red'">{{ grossProfit.toFixed(2) }} 万元</strong>
      </div>

      <el-divider content-position="left">审批记录</el-divider>
      <el-timeline v-if="detail.approvals?.length">
        <el-timeline-item
          v-for="(a, idx) in detail.approvals"
          :key="idx"
          :timestamp="a.time"
          :type="idx === detail.approvals.length - 1 ? 'primary' : 'success'"
        >
          <div class="approval">
            <strong>{{ a.role }}</strong> · {{ a.name }} —— {{ a.action }}
          </div>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="尚无审批记录" :image-size="60" />
    </el-card>
  </div>
</template>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; }
.title { display: flex; align-items: center; gap: 8px; }
.title .name { font-size: 16px; font-weight: 600; color: #303133; }
.summary {
  padding: 10px 16px;
  background: #f5f7fa;
  border-radius: 4px;
  margin: 12px 0 24px;
  font-size: 14px;
}
.green { color: #67c23a; }
.red { color: #f56c6c; }
.approval { font-size: 13px; color: #303133; }
:deep(.el-divider__text) { font-size: 14px; color: #606266; font-weight: 600; }
:deep(.el-steps) { padding: 16px 0; }
</style>
