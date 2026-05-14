<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getUserInfo, LeavePayload, postJson, request, UserInfo, WorkflowAction, WorkflowInstance, WorkflowTask } from "../api";
import { setPageTitle } from "../pageTitle";

const route = useRoute();
const router = useRouter();
const loading = ref(true);
const error = ref("");
const detail = ref<WorkflowInstance | null>(null);
const currentUser = ref<UserInfo | null>(null);
const note = ref("");
const submitting = ref(false);
const resubmitType = ref("annual");
const resubmitStart = ref("");
const resubmitEnd = ref("");
const resubmitReason = ref("");

const activeTask = computed<WorkflowTask | null>(() => {
  return detail.value?.timeline?.find((item) => item.status === "todo") || null;
});

const leave = computed<LeavePayload | null>(() => {
  if (detail.value?.biz_type !== "leave_request") return null;
  return (detail.value.business || null) as LeavePayload | null;
});

const actions = computed(() => detail.value?.available_actions || []);
const approveAction = computed(() => findAction("approve"));
const rejectAction = computed(() => findAction("reject"));
const returnAction = computed(() => findAction("return"));
const resubmitAction = computed(() => findAction("resubmit"));
const cancelAction = computed(() => findAction("cancel"));
const isApplicant = computed(() => detail.value?.applicant_id === currentUser.value?.user_id);

onMounted(load);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [detailData, userData] = await Promise.all([requestDetail(), getUserInfo()]);
    detail.value = detailData;
    currentUser.value = userData;
    setPageTitle(detailData.title || "流程详情");
    hydrateResubmitForm();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "流程详情加载失败";
  } finally {
    loading.value = false;
  }
}

async function requestDetail() {
  return request<WorkflowInstance>(`/api/workflow/instances/${route.params.id}`);
}

function hydrateResubmitForm() {
  if (!leave.value) return;
  resubmitType.value = leave.value.leave_type;
  resubmitStart.value = leave.value.start_date;
  resubmitEnd.value = leave.value.end_date;
  resubmitReason.value = leave.value.reason;
}

function findAction(action: string): WorkflowAction | null {
  return actions.value.find((item) => item.action === action) || null;
}

async function handleWorkflowAction(action: WorkflowAction | null, body: Record<string, unknown> = {}) {
  if (!action) return;
  submitting.value = true;
  error.value = "";
  try {
    await postJson(action.api, body);
    note.value = "";
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "处理失败";
  } finally {
    submitting.value = false;
  }
}

async function handleReview(action: WorkflowAction | null) {
  await handleWorkflowAction(action, { note: note.value.trim() });
}

async function handleResubmit() {
  if (!resubmitAction.value) return;
  await handleWorkflowAction(resubmitAction.value, {
    leave_type: resubmitType.value,
    start_date: resubmitStart.value,
    end_date: resubmitEnd.value,
    reason: resubmitReason.value.trim(),
  });
}

async function urge() {
  if (!detail.value) return;
  submitting.value = true;
  error.value = "";
  try {
    await postJson(`/api/workflow/instances/${detail.value.id}/urge`);
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "催办失败";
  } finally {
    submitting.value = false;
  }
}

function nodeLabel(nodeKey: string | null) {
  if (nodeKey === "manager_review") return "直属上级审批";
  if (nodeKey === "hr_review") return "HR 审批";
  if (nodeKey === "returned") return "退回修改";
  return nodeKey || "流程节点";
}

function taskStatusLabel(status: string) {
  return {
    todo: "待处理",
    completed: "已通过",
    rejected: "已驳回",
    returned: "已退回",
    cancelled: "已取消",
  }[status] || status;
}

function instanceStatusLabel(status: string) {
  return {
    running: "进行中",
    returned: "已退回",
    completed: "已完成",
    rejected: "已驳回",
    cancelled: "已取消",
  }[status] || status;
}
</script>

<template>
  <main class="page">
    <header class="page-header">
      <button class="back-button" type="button" @click="router.back()">‹</button>
      <div>
        <p class="eyebrow">Workflow Detail</p>
        <h1>流程详情</h1>
      </div>
    </header>

    <section class="panel">
      <div v-if="loading" class="screen-center compact">
        <div class="spinner" />
        <p>同步流程详情</p>
      </div>
      <p v-else-if="error" class="error">{{ error }}</p>

      <template v-if="detail">
        <article class="detail-head" data-testid="workflow-detail-head">
          <p class="tag">{{ detail.biz_type === "leave_request" ? "请假申请" : "补卡申诉" }}</p>
          <h2>{{ detail.title }}</h2>
          <p>{{ detail.applicant_name }} · {{ detail.created_at }}</p>
          <span class="status">{{ instanceStatusLabel(detail.status) }}</span>
        </article>

        <section class="business-card" v-if="leave" data-testid="leave-detail-business">
          <h3>请假信息</h3>
          <dl>
            <dt>类型</dt>
            <dd>{{ leave.leave_type_label }}</dd>
            <dt>日期</dt>
            <dd>{{ leave.start_date }} 至 {{ leave.end_date }}</dd>
            <dt>天数</dt>
            <dd>{{ leave.days }} 天</dd>
            <dt>状态</dt>
            <dd>{{ leave.status_label }}</dd>
            <dt>原因</dt>
            <dd>{{ leave.reason }}</dd>
            <dt v-if="leave.return_reason">退回原因</dt>
            <dd v-if="leave.return_reason" data-testid="leave-return-reason">{{ leave.return_reason }}</dd>
          </dl>
        </section>

        <section class="business-card" v-else-if="detail.business">
          <h3>业务摘要</h3>
          <dl>
            <template v-for="(value, key) in detail.business" :key="key">
              <dt>{{ key }}</dt>
              <dd>{{ value }}</dd>
            </template>
          </dl>
        </section>

        <section class="timeline" data-testid="workflow-timeline">
          <h3>审批时间线</h3>
          <article v-for="item in detail.timeline" :key="item.id" class="timeline-item" :data-testid="`workflow-timeline-${item.node_key}`">
            <div class="dot" :class="{ done: item.status !== 'todo' }" />
            <div>
              <strong>{{ nodeLabel(item.node_key) }}</strong>
              <p>{{ item.assignee_name }} · {{ taskStatusLabel(item.status) }} · {{ item.updated_at || item.created_at }}</p>
              <p v-if="item.note" class="muted">备注：{{ item.note }}</p>
            </div>
          </article>
        </section>

        <section v-if="approveAction || rejectAction || returnAction" class="action-card" data-testid="workflow-review-actions">
          <h3>处理当前待办</h3>
          <p v-if="activeTask" class="muted">{{ nodeLabel(activeTask.node_key) }} · {{ activeTask.title }}</p>
          <textarea v-model="note" data-testid="workflow-review-note" placeholder="审批备注，可留空" rows="3" />
          <div class="action-row three">
            <button
              v-if="rejectAction"
              class="ghost-button danger"
              data-testid="workflow-action-reject"
              type="button"
              :disabled="submitting"
              @click="handleReview(rejectAction)"
            >
              驳回
            </button>
            <button
              v-if="returnAction"
              class="ghost-button"
              data-testid="workflow-action-return"
              type="button"
              :disabled="submitting"
              @click="handleReview(returnAction)"
            >
              退回修改
            </button>
            <button
              v-if="approveAction"
              class="primary-button"
              data-testid="workflow-action-approve"
              type="button"
              :disabled="submitting"
              @click="handleReview(approveAction)"
            >
              通过
            </button>
          </div>
        </section>

        <section v-if="resubmitAction && leave" class="action-card" data-testid="leave-resubmit-form">
          <h3>修改并重新提交</h3>
          <div class="form-grid">
            <label>
              <span>请假类型</span>
              <select v-model="resubmitType" data-testid="leave-resubmit-type">
                <option value="annual">年假</option>
                <option value="sick">病假</option>
                <option value="personal">事假</option>
              </select>
            </label>
            <div class="date-row">
              <label>
                <span>开始日期</span>
                <input v-model="resubmitStart" data-testid="leave-resubmit-start-date" type="date" />
              </label>
              <label>
                <span>结束日期</span>
                <input v-model="resubmitEnd" data-testid="leave-resubmit-end-date" type="date" />
              </label>
            </div>
            <label>
              <span>请假原因</span>
              <textarea v-model="resubmitReason" data-testid="leave-resubmit-reason" rows="3" />
            </label>
          </div>
          <button
            class="primary-button full-button"
            data-testid="leave-resubmit-button"
            type="button"
            :disabled="submitting"
            @click="handleResubmit"
          >
            重新提交
          </button>
        </section>

        <section v-if="cancelAction || (isApplicant && detail.status === 'running' && !approveAction)" class="action-card">
          <h3>流程操作</h3>
          <p class="muted">申请人可取消或催办当前处理人，便于流程中心 Tab 自动化断言。</p>
          <div class="action-row">
            <button
              v-if="cancelAction"
              class="ghost-button danger"
              data-testid="workflow-action-cancel"
              type="button"
              :disabled="submitting"
              @click="handleWorkflowAction(cancelAction)"
            >
              取消申请
            </button>
            <button
              v-if="isApplicant && detail.status === 'running'"
              class="primary-button"
              data-testid="workflow-action-urge"
              type="button"
              :disabled="submitting"
              @click="urge"
            >
              催办
            </button>
          </div>
        </section>
      </template>
    </section>
  </main>
</template>
