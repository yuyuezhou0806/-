<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchTemplates, uploadTemplate } from '@/api/bidding'

const router = useRouter()
const templates = ref([])
const loading = ref(false)
const uploadDialog = ref({ visible: false, name: '', type: '招投标' })

const formatSize = (b) => {
  if (b < 1024) return `${b}B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)}KB`
  return `${(b / 1024 / 1024).toFixed(1)}MB`
}

const load = async () => {
  loading.value = true
  try {
    templates.value = await fetchTemplates()
  } finally {
    loading.value = false
  }
}

const openUpload = () => {
  uploadDialog.value = { visible: true, name: '', type: '招投标' }
}

const submitUpload = async () => {
  if (!uploadDialog.value.name.trim()) return ElMessage.warning('请输入范本名称')
  await uploadTemplate({ name: uploadDialog.value.name, type: uploadDialog.value.type })
  ElMessage.success('已上传')
  uploadDialog.value.visible = false
  load()
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="page-card">
      <div class="toolbar">
        <div>
          <el-button @click="router.push('/bidding/list')">返回</el-button>
          <el-button type="primary" :icon="'Upload'" @click="openUpload">上传范本</el-button>
        </div>
        <div class="muted">招投标范本和销售报价模板,分配任务时可直接套用</div>
      </div>

      <el-table v-loading="loading" :data="templates" stripe border>
        <el-table-column prop="name" label="范本名称" min-width="240">
          <template #default="{ row }">
            <el-icon><Document /></el-icon>
            <span style="margin-left: 6px">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120" align="center" />
        <el-table-column label="大小" width="120" align="center">
          <template #default="{ row }">{{ formatSize(row.size) }}</template>
        </el-table-column>
        <el-table-column prop="uploader" label="上传人" width="120" align="center" />
        <el-table-column prop="updatedAt" label="更新时间" width="180" />
        <el-table-column label="操作" width="160">
          <template #default>
            <el-button link type="primary">下载</el-button>
            <el-button link type="primary">引用</el-button>
            <el-button link type="danger">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="uploadDialog.visible" title="上传范本" width="420px">
      <el-form label-width="100px">
        <el-form-item label="范本名称">
          <el-input v-model="uploadDialog.name" placeholder="如:市政工程招标范本.docx" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="uploadDialog.type">
            <el-radio value="招投标">招投标</el-radio>
            <el-radio value="销售报价">销售报价</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="文件">
          <el-upload :auto-upload="false" :limit="1">
            <el-button>选择文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitUpload">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.muted { color: #909399; font-size: 12px; }
</style>
