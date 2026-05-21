<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createProject } from '@/api/project'

const router = useRouter()
const submitting = ref(false)
const formRef = ref(null)

const DEPARTMENT_OPTIONS = ['公路事业部', '水利事业部', '水运事业部', '市政事业部', '房建事业部', '检测事业部', '咨询事业部']

const form = reactive({
  contractCode: '',
  name: '',
  manager: '',
  department: '',
  amount: 0,
  startDate: '',
  endDate: '',
  remark: '',
})

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  manager: [{ required: true, message: '请输入项目经理', trigger: 'blur' }],
  department: [{ required: true, message: '请选择承办部门', trigger: 'change' }],
}

const submit = async () => {
  await formRef.value.validate()
  if (form.startDate && form.endDate && form.endDate < form.startDate) {
    return ElMessage.warning('结束日期不能早于开始日期')
  }
  submitting.value = true
  try {
    await createProject({ ...form })
    ElMessage.success('已立项')
    router.push('/project/list')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="header">
          <span>新建立项</span>
          <el-button text @click="router.push('/project/list')">返回列表</el-button>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-row :gutter="16">
          <el-col :md="12">
            <el-form-item label="关联合同编号">
              <el-input v-model="form.contractCode" placeholder="如 HT-2026-0001" />
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="项目名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入项目名称" />
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="项目经理" prop="manager">
              <el-input v-model="form.manager" placeholder="请输入项目经理姓名" />
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="承办部门" prop="department">
              <el-select v-model="form.department" placeholder="请选择部门" style="width: 100%">
                <el-option v-for="d in DEPARTMENT_OPTIONS" :key="d" :label="d" :value="d" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="立项金额">
              <el-input-number v-model="form.amount" :min="0" :precision="2" :step="10" style="width: 100%" />
              <span class="unit">万元</span>
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="项目周期">
              <el-date-picker
                v-model="form.startDate"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="开始日期"
                style="width: 45%"
              />
              <span style="margin: 0 8px">至</span>
              <el-date-picker
                v-model="form.endDate"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="结束日期"
                style="width: 45%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" maxlength="300" show-word-limit />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submit">提交立项</el-button>
          <el-button @click="router.push('/project/list')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; }
.unit { margin-left: 8px; color: #909399; }
</style>
