<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchDepartmentTask, submitDepartmentTask } from '@/api/department'

const route = useRoute()
const router = useRouter()
const detail = ref(null)
const loading = ref(false)
const submitting = ref(false)

const form = reactive({ coopFee: 0, materialFee: 0, remark: '' })
const STATUS_TAG = { 待领取: 'info', 执行中: 'warning', 已完成: 'success' }
const readonly = computed(() => detail.value?.status === '已完成')

const load = async () => {
  loading.value = true
  try {
    detail.value = await fetchDepartmentTask(route.params.id)
    form.coopFee = detail.value.coopFee || 0
    form.materialFee = detail.value.materialFee || 0
    form.remark = detail.value.remark || ''
  } finally {
    loading.value = false
  }
}

const submit = async () => {
  submitting.value = true
  try {
    await submitDepartmentTask(detail.value.id, { ...form })
    ElMessage.success('已提交')
    load()
  } finally {
    submitting.value = false
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
          <el-button @click="router.push('/department/list')">返回</el-button>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="任务编号">{{ detail.code }}</el-descriptions-item>
        <el-descriptions-item label="关联合同">{{ detail.contractCode }}</el-descriptions-item>
        <el-descriptions-item label="承办部门">{{ detail.department }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ detail.role }}</el-descriptions-item>
        <el-descriptions-item label="负责人">{{ detail.assignee }}</el-descriptions-item>
        <el-descriptions-item label="任务金额">{{ detail.amount?.toFixed(2) }} 万元</el-descriptions-item>
        <el-descriptions-item label="分配日期">{{ detail.assignDate }}</el-descriptions-item>
        <el-descriptions-item label="要求完成">{{ detail.requireDate }}</el-descriptions-item>
        <el-descriptions-item label="原备注" :span="3">{{ detail.remark || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">
        {{ readonly ? '已填写费用' : '填写配合费 / 材料费' }}
      </el-divider>

      <el-form :model="form" label-width="120px" :disabled="readonly">
        <el-row :gutter="16">
          <el-col :md="8">
            <el-form-item label="配合费">
              <el-input-number v-model="form.coopFee" :min="0" :precision="2" :step="0.5" style="width: 100%" />
              <span class="unit">万元</span>
            </el-form-item>
          </el-col>
          <el-col :md="8">
            <el-form-item label="材料费">
              <el-input-number v-model="form.materialFee" :min="0" :precision="2" :step="0.5" style="width: 100%" />
              <span class="unit">万元</span>
            </el-form-item>
          </el-col>
          <el-col :md="8">
            <el-form-item label="小计">
              <el-input :value="(form.coopFee + form.materialFee).toFixed(2) + ' 万元'" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="说明">
          <el-input v-model="form.remark" type="textarea" :rows="3" maxlength="300" show-word-limit
            placeholder="如有需要说明的内容,请填写" />
        </el-form-item>

        <el-form-item v-if="!readonly">
          <el-button type="primary" :loading="submitting" @click="submit">提交</el-button>
          <el-button @click="router.push('/department/list')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; }
.title { display: flex; align-items: center; gap: 8px; }
.title .name { font-size: 16px; font-weight: 600; color: #303133; }
.unit { margin-left: 8px; color: #909399; }
:deep(.el-divider__text) { font-size: 14px; color: #606266; font-weight: 600; }
</style>
