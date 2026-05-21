<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { assignBiddingTask, fetchBidding, updateBiddingResult } from '@/api/bidding'

const route = useRoute()
const router = useRouter()
const detail = ref(null)
const loading = ref(false)

const assignDialog = reactive({
  visible: false,
  tasks: [],
  assignees: '',
  assignDate: '',
  requireDate: '',
})

const STATUS_TAG = {
  制作中: 'warning', 待提交: '', 已提交: 'primary', 已中标: 'success', 未中标: 'info',
}

const load = async () => {
  loading.value = true
  try {
    detail.value = await fetchBidding(route.params.id)
  } finally {
    loading.value = false
  }
}

const openAssign = () => {
  Object.assign(assignDialog, {
    visible: true,
    tasks: detail.value.tasks?.slice() || [],
    assignees: detail.value.assignees?.join(',') || '',
    assignDate: detail.value.assignDate || '',
    requireDate: detail.value.requireDate || '',
  })
}

const submitAssign = async () => {
  if (!assignDialog.tasks.length) return ElMessage.warning('请选择任务内容')
  if (!assignDialog.assignees.trim()) return ElMessage.warning('请输入分配人员')
  await assignBiddingTask(detail.value.id, {
    tasks: assignDialog.tasks,
    assignees: assignDialog.assignees.split(/[,, ]+/).filter(Boolean),
    assignDate: assignDialog.assignDate,
    requireDate: assignDialog.requireDate,
  })
  ElMessage.success('已分配')
  assignDialog.visible = false
  load()
}

const setResult = async (isWon) => {
  await updateBiddingResult(detail.value.id, isWon)
  ElMessage.success(isWon ? '已标记中标' : '已标记未中标')
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
            <el-tag :type="STATUS_TAG[detail.status]" size="small">{{ detail.status }}</el-tag>
          </div>
          <div>
            <el-button @click="router.push('/bidding/list')">返回</el-button>
            <el-button type="primary" :icon="'UserFilled'" @click="openAssign">分配任务</el-button>
            <el-button type="success" :disabled="detail.isWon === true" @click="setResult(true)">标记中标</el-button>
            <el-button type="danger" plain :disabled="detail.isWon === false" @click="setResult(false)">标记未中标</el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="招投标编号">{{ detail.code }}</el-descriptions-item>
        <el-descriptions-item label="关联商机">{{ detail.oppCode }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ detail.bidType }}</el-descriptions-item>
        <el-descriptions-item label="是否需要答疑">
          <el-tag :type="detail.needQuery ? 'warning' : 'info'" size="small">
            {{ detail.needQuery ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="答疑时间">{{ detail.queryTime || '-' }}</el-descriptions-item>
        <el-descriptions-item label="截止时间">{{ detail.deadline || '-' }}</el-descriptions-item>
        <el-descriptions-item label="是否中标">
          <el-tag v-if="detail.isWon === true" type="success" size="small">已中标</el-tag>
          <el-tag v-else-if="detail.isWon === false" type="info" size="small">未中标</el-tag>
          <span v-else>待定</span>
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detail.remark || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="section">
        <h4>任务分配</h4>
        <el-descriptions :column="2" border v-if="detail.assignees?.length">
          <el-descriptions-item label="任务内容">
            <el-tag v-for="t in detail.tasks" :key="t" size="small" style="margin-right: 4px">{{ t }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="分配人员">{{ detail.assignees.join('、') }}</el-descriptions-item>
          <el-descriptions-item label="分配日期">{{ detail.assignDate }}</el-descriptions-item>
          <el-descriptions-item label="要求完成日期">{{ detail.requireDate }}</el-descriptions-item>
        </el-descriptions>
        <el-empty v-else description="尚未分配任务" :image-size="60" />
      </div>

      <div class="section">
        <h4>附件(招标文件 / 图纸)</h4>
        <el-empty description="演示环境暂无附件" :image-size="60" />
      </div>
    </el-card>

    <el-dialog v-model="assignDialog.visible" title="分配招投标任务" width="540px">
      <el-form label-width="120px">
        <el-form-item label="任务内容">
          <el-checkbox-group v-model="assignDialog.tasks">
            <el-checkbox value="技术方案" label="技术方案">技术方案</el-checkbox>
            <el-checkbox value="清单" label="清单">清单</el-checkbox>
            <el-checkbox value="技术标" label="技术标">技术标</el-checkbox>
            <el-checkbox value="其它" label="其它">其它</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="分配人员">
          <el-input v-model="assignDialog.assignees" placeholder="多个人员用逗号分隔" />
        </el-form-item>
        <el-form-item label="分配日期">
          <el-date-picker v-model="assignDialog.assignDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="要求完成日期">
          <el-date-picker v-model="assignDialog.requireDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitAssign">确认分配</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; }
.title { display: flex; align-items: center; gap: 8px; }
.title .name { font-size: 16px; font-weight: 600; color: #303133; }
.section { margin-top: 24px; }
.section h4 { margin: 0 0 12px; font-size: 14px; color: #606266; border-left: 3px solid #409eff; padding-left: 8px; }
</style>
