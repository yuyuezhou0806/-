<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  createOpportunity,
  fetchOpportunity,
  updateOpportunity,
} from '@/api/opportunity'
import {
  SOURCE_OPTIONS,
  TYPE_OPTIONS,
  BID_TYPE_OPTIONS,
} from './constants'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  name: '',
  source: '自主',
  type: '一般',
  needBid: true,
  bidType: '招投标',
  customer: '',
  contact: '',
  phone: '',
  amount: null,
  remark: '',
  attachments: [],
})

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  source: [{ required: true, message: '请选择项目来源', trigger: 'change' }],
  type: [{ required: true, message: '请选择商机类型', trigger: 'change' }],
  bidType: [{ required: true, message: '请选择招投标类型', trigger: 'change' }],
  customer: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  phone: [
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '手机号格式不正确',
      trigger: 'blur',
    },
  ],
  amount: [
    {
      validator: (_, value, cb) => {
        if (value !== null && value !== undefined && value !== '' && value < 0) {
          cb(new Error('金额必须为正数'))
        } else cb()
      },
      trigger: 'blur',
    },
  ],
}

const onFileChange = (file) => {
  form.attachments.push({
    name: file.name,
    size: file.size,
    uid: file.uid,
  })
}

const onFileRemove = (file) => {
  form.attachments = form.attachments.filter((f) => f.uid !== file.uid)
}

const submit = async () => {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateOpportunity(route.params.id, form)
      ElMessage.success('已更新')
    } else {
      await createOpportunity(form)
      ElMessage.success('已创建')
    }
    router.push('/opportunity/list')
  } finally {
    submitting.value = false
  }
}

const cancel = () => router.push('/opportunity/list')

const uploadToGroup = () => {
  ElMessage.success('已请求上传到集团系统(演示)')
}

onMounted(async () => {
  if (isEdit.value) {
    const data = await fetchOpportunity(route.params.id)
    if (data) Object.assign(form, data)
  }
})
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑商机' : '新建商机' }}</span>
          <el-button text @click="cancel">返回列表</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        label-position="right"
      >
        <el-divider content-position="left">基本信息</el-divider>
        <el-row :gutter="16">
          <el-col :md="12">
            <el-form-item label="项目名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入项目名称" maxlength="80" show-word-limit />
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="客户名称" prop="customer">
              <el-input v-model="form.customer" placeholder="请输入客户单位名称" />
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="联系人">
              <el-input v-model="form.contact" placeholder="请输入联系人姓名" />
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="联系电话" prop="phone">
              <el-input v-model="form.phone" placeholder="请输入手机号" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">业务信息</el-divider>
        <el-row :gutter="16">
          <el-col :md="12">
            <el-form-item label="项目来源" prop="source">
              <el-radio-group v-model="form.source">
                <el-radio v-for="o in SOURCE_OPTIONS" :key="o.value" :value="o.value">
                  {{ o.label }}
                </el-radio>
              </el-radio-group>
              <el-button
                v-if="form.source === '自主'"
                size="small"
                type="primary"
                link
                style="margin-left: 12px"
                @click="uploadToGroup"
              >
                <el-icon><Upload /></el-icon>
                上传到集团系统
              </el-button>
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="商机类型" prop="type">
              <el-radio-group v-model="form.type">
                <el-radio-button
                  v-for="o in TYPE_OPTIONS"
                  :key="o.value"
                  :value="o.value"
                >
                  {{ o.label }}
                </el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="是否需要招投标">
              <el-switch v-model="form.needBid" />
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="招投标类型" prop="bidType">
              <el-select v-model="form.bidType" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="o in BID_TYPE_OPTIONS"
                  :key="o.value"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :md="12">
            <el-form-item label="预估金额" prop="amount">
              <el-input-number
                v-model="form.amount"
                :precision="2"
                :min="0"
                :step="10"
                style="width: 100%"
              />
              <span class="unit">万元</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">附加信息</el-divider>
        <el-form-item label="备注">
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="请输入备注信息"
          />
        </el-form-item>

        <el-form-item label="附件">
          <el-upload
            :auto-upload="false"
            :file-list="form.attachments"
            :on-change="onFileChange"
            :on-remove="onFileRemove"
            multiple
          >
            <el-button type="primary" plain>
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #tip>
              <div class="upload-tip">支持上传招标文件、图纸、合同范本等(演示环境不实际上传)</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submit">
            {{ isEdit ? '保存修改' : '提交' }}
          </el-button>
          <el-button @click="cancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.unit {
  margin-left: 8px;
  color: #909399;
}

.upload-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}

:deep(.el-divider__text) {
  font-size: 14px;
  color: #606266;
  font-weight: 600;
}
</style>
