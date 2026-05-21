<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createContract, fetchContractMeta } from '@/api/contract'
import { fetchOpportunities } from '@/api/opportunity'

const route = useRoute()
const router = useRouter()
const submitting = ref(false)
const meta = ref({ types: [], priceTypes: [], levels: [], divisions: [] })
const formRef = ref(null)

const STAFF_OPTIONS = ['张工', '李工', '王工', '赵工', '孙工', '周工', '吴工', '郑工', '冯工']
const MANAGER_OPTIONS = ['张工', '李工', '王工', '赵工', '孙工']

const oppOptions = ref([])
const oppLoading = ref(false)
const oppMap = ref({})

const form = reactive({
  name: '',
  oppId: null,
  oppCode: '',
  customer: '',
  archiveNumber: '',
  manager: '',
  level: '一般',
  contractType: '市政',
  priceType: '合同单价',
  discount: 1.0,
  revenue: 0,
  divisionAmounts: {},
  cost: { labor: 0, coop: 0, material: 0, other: 0 },
  coopMembers: [],
  materialMembers: [],
  hasArchiveContract: false,
  hasPaymentContract: false,
  payee: '',
  remark: '',
})

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  oppId: [{ required: true, message: '请选择关联商机', trigger: 'change' }],
  archiveNumber: [{ required: true, message: '请输入合同备案号', trigger: 'blur' }],
  manager: [{ required: true, message: '请选择项目经理', trigger: 'change' }],
  contractType: [{ required: true, message: '请选择合同类型', trigger: 'change' }],
  priceType: [{ required: true, message: '请选择计价类型', trigger: 'change' }],
}

const divisionsTotal = computed(() =>
  Object.values(form.divisionAmounts).reduce((s, v) => s + (Number(v) || 0), 0),
)
const costTotal = computed(() =>
  (Number(form.cost.labor) || 0) +
  (Number(form.cost.coop) || 0) +
  (Number(form.cost.material) || 0) +
  (Number(form.cost.other) || 0),
)
const grossProfit = computed(() => Number(form.revenue) - costTotal.value)

const approvalSteps = computed(() => {
  const steps = ['营销中心分配项目经理', '项目经理填写合同', '配合费/材料费成员填写', '营销中心审核']
  if (form.level === '重大') steps.push('总经理终审')
  return steps
})

const searchOpportunity = async (keyword) => {
  oppLoading.value = true
  try {
    const data = await fetchOpportunities({
      page: 1,
      pageSize: 20,
      keyword: keyword || '',
      status: '已闭合',
    })
    oppOptions.value = data.items
    data.items.forEach((it) => { oppMap.value[it.id] = it })
  } finally {
    oppLoading.value = false
  }
}

const onOpportunityChange = (id) => {
  const opp = oppMap.value[id]
  if (!opp) return
  form.oppCode = opp.code
  form.name = opp.name
  form.customer = opp.customer || ''
  if (opp.amount) {
    const first = meta.value.divisions[0]
    if (first) form.divisionAmounts[first] = Number(opp.amount)
  }
  if (opp.type) form.level = opp.type
  ElMessage.success(`已自动填充商机「${opp.code}」的基础信息`)
}

const init = async () => {
  meta.value = await fetchContractMeta()
  meta.value.divisions.forEach((d) => { form.divisionAmounts[d] = 0 })
  await searchOpportunity('')

  // 如果路由带 oppId 参数,自动选中并填充(支持从商机详情跳转过来)
  const presetOppId = Number(route.query.oppId)
  if (presetOppId) {
    if (!oppMap.value[presetOppId]) {
      const data = await fetchOpportunities({ page: 1, pageSize: 50 })
      data.items.forEach((it) => { oppMap.value[it.id] = it })
      oppOptions.value = data.items
    }
    if (oppMap.value[presetOppId]) {
      form.oppId = presetOppId
      onOpportunityChange(presetOppId)
    }
  }
}

const submit = async () => {
  await formRef.value.validate()
  if (form.hasPaymentContract && !form.payee.trim()) {
    return ElMessage.warning('上传了支付合同需要填写付款方')
  }
  submitting.value = true
  try {
    form.revenue = divisionsTotal.value
    await createContract({ ...form })
    ElMessage.success('合同已提交,流转中')
    router.push('/contract/list')
  } finally {
    submitting.value = false
  }
}

onMounted(init)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="header">
          <span>发起合同</span>
          <el-button text @click="router.push('/contract/list')">返回列表</el-button>
        </div>
      </template>

      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        <template #title>
          审批流程({{ form.level }}):
          <el-tag
            v-for="(step, idx) in approvalSteps"
            :key="step"
            :type="idx === 0 ? 'primary' : 'info'"
            size="small"
            style="margin-right: 6px"
            effect="plain"
          >
            {{ idx + 1 }}. {{ step }}
          </el-tag>
        </template>
      </el-alert>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-divider content-position="left">基本信息</el-divider>
        <el-row :gutter="16">
          <el-col :md="12">
            <el-form-item label="关联商机" prop="oppId">
              <el-select
                v-model="form.oppId"
                filterable
                remote
                clearable
                :remote-method="searchOpportunity"
                :loading="oppLoading"
                placeholder="输入商机编号或项目名称搜索"
                style="width: 100%"
                @change="onOpportunityChange"
              >
                <el-option
                  v-for="opp in oppOptions"
                  :key="opp.id"
                  :value="opp.id"
                  :label="`${opp.code}  ${opp.name}`"
                >
                  <div class="opp-option">
                    <span class="opp-code">{{ opp.code }}</span>
                    <span class="opp-name">{{ opp.name }}</span>
                    <el-tag size="small" :type="opp.type === '重大' ? 'danger' : opp.type === '中等' ? 'warning' : ''">
                      {{ opp.type }}
                    </el-tag>
                  </div>
                </el-option>
              </el-select>
              <div class="hint">选择已闭合的商机,系统会自动回填项目名称、客户、商机等级等信息</div>
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="备案号" prop="archiveNumber">
              <el-input v-model="form.archiveNumber" placeholder="请输入合同备案号" />
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="项目名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入项目名称" />
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="客户名称">
              <el-input v-model="form.customer" placeholder="选中商机后自动填充,可修改" />
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="项目经理" prop="manager">
              <el-select v-model="form.manager" placeholder="请选择项目经理" style="width: 100%">
                <el-option v-for="n in MANAGER_OPTIONS" :key="n" :label="n" :value="n" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="合同等级">
              <el-radio-group v-model="form.level">
                <el-radio-button v-for="l in meta.levels" :key="l" :value="l">{{ l }}</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">合同信息</el-divider>
        <el-row :gutter="16">
          <el-col :md="8">
            <el-form-item label="合同类型" prop="contractType">
              <el-select v-model="form.contractType" style="width: 100%">
                <el-option v-for="t in meta.types" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :md="8">
            <el-form-item label="计价类型" prop="priceType">
              <el-select v-model="form.priceType" style="width: 100%">
                <el-option v-for="p in meta.priceTypes" :key="p" :label="p" :value="p" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :md="8">
            <el-form-item label="合同折扣">
              <el-input-number
                v-model="form.discount"
                :min="0.5"
                :max="1.0"
                :step="0.01"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">
          收入预估(各事业部金额,单位:万元)
        </el-divider>
        <el-row :gutter="12">
          <el-col v-for="d in meta.divisions" :key="d" :xs="12" :md="6" :lg="4">
            <el-form-item :label="d" label-width="80px" style="margin-bottom: 12px">
              <el-input-number
                v-model="form.divisionAmounts[d]"
                :min="0"
                :precision="2"
                :step="1"
                size="default"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <div class="summary">
          <span>收入合计:</span>
          <strong class="green">{{ divisionsTotal.toFixed(2) }} 万元</strong>
        </div>

        <el-divider content-position="left">成本预估(单位:万元)</el-divider>
        <el-row :gutter="16">
          <el-col :md="8">
            <el-form-item label="劳务费">
              <el-input-number v-model="form.cost.labor" :min="0" :precision="2" style="width: 100%" />
              <span class="hint">由项目经理填写</span>
            </el-form-item>
          </el-col>
          <el-col :md="8">
            <el-form-item label="配合费">
              <el-input-number v-model="form.cost.coop" :min="0" :precision="2" style="width: 100%" />
              <span class="hint">最终由配合人员填写</span>
            </el-form-item>
          </el-col>
          <el-col :md="8">
            <el-form-item label="材料费">
              <el-input-number v-model="form.cost.material" :min="0" :precision="2" style="width: 100%" />
              <span class="hint">最终由材料人员填写</span>
            </el-form-item>
          </el-col>
          <el-col :md="8">
            <el-form-item label="其它">
              <el-input-number v-model="form.cost.other" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :md="8">
            <el-form-item label="配合人员">
              <el-select v-model="form.coopMembers" multiple filterable placeholder="可多选" style="width: 100%">
                <el-option v-for="n in STAFF_OPTIONS" :key="n" :label="n" :value="n" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :md="8">
            <el-form-item label="材料人员">
              <el-select v-model="form.materialMembers" multiple filterable placeholder="可多选" style="width: 100%">
                <el-option v-for="n in STAFF_OPTIONS" :key="n" :label="n" :value="n" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <div class="summary">
          <span>成本合计:</span>
          <strong class="red">{{ costTotal.toFixed(2) }} 万元</strong>
          <span style="margin-left: 24px">毛利:</span>
          <strong :class="grossProfit >= 0 ? 'green' : 'red'">
            {{ grossProfit.toFixed(2) }} 万元
          </strong>
        </div>

        <el-divider content-position="left">合同附件</el-divider>
        <el-row :gutter="16">
          <el-col :md="12">
            <el-form-item label="备案合同">
              <el-switch v-model="form.hasArchiveContract" active-text="已上传" inactive-text="未上传" />
              <el-button v-if="form.hasArchiveContract" size="small" link type="primary" style="margin-left: 12px">
                <el-icon><Upload /></el-icon>
                上传文件
              </el-button>
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="支付合同">
              <el-switch v-model="form.hasPaymentContract" active-text="已上传" inactive-text="未上传" />
              <el-button v-if="form.hasPaymentContract" size="small" link type="primary" style="margin-left: 12px">
                <el-icon><Upload /></el-icon>
                上传文件
              </el-button>
            </el-form-item>
          </el-col>
          <el-col v-if="form.hasPaymentContract" :md="12">
            <el-form-item label="付款方" required>
              <el-input v-model="form.payee" placeholder="支付合同的付款方" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="300" show-word-limit />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submit">
            提交审批
          </el-button>
          <el-button @click="router.push('/contract/list')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; }
.hint { margin-left: 0; color: #909399; font-size: 12px; }
.summary {
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 4px;
  margin: 12px 0 24px;
  font-size: 14px;
}
.green { color: #67c23a; }
.red { color: #f56c6c; }
.opp-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.opp-option .opp-code {
  color: #909399;
  font-family: monospace;
  font-size: 12px;
}
.opp-option .opp-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
:deep(.el-divider__text) { font-size: 14px; color: #606266; font-weight: 600; }
</style>
