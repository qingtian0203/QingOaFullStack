<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { createLeaveRequest } from "../api";

const router = useRouter();
const leaveType = ref("annual");
const startDate = ref(todayOffset(1));
const endDate = ref(todayOffset(1));
const reason = ref("");
const submitting = ref(false);
const error = ref("");

const days = computed(() => {
  const start = new Date(startDate.value);
  const end = new Date(endDate.value);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end < start) return 0;
  return Math.floor((end.getTime() - start.getTime()) / 86400000) + 1;
});

function todayOffset(offset: number) {
  const value = new Date();
  value.setDate(value.getDate() + offset);
  const month = `${value.getMonth() + 1}`.padStart(2, "0");
  const day = `${value.getDate()}`.padStart(2, "0");
  return `${value.getFullYear()}-${month}-${day}`;
}

async function submit() {
  error.value = "";
  if (days.value <= 0) {
    error.value = "结束日期不能早于开始日期";
    return;
  }
  if (reason.value.trim().length < 2) {
    error.value = "请填写请假原因";
    return;
  }
  submitting.value = true;
  try {
    const result = await createLeaveRequest({
      leave_type: leaveType.value,
      start_date: startDate.value,
      end_date: endDate.value,
      reason: reason.value.trim(),
    });
    router.replace(`/workflow/detail/${result.process_instance_id}`);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "请假提交失败";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <main class="page">
    <header class="page-header">
      <button class="back-button" type="button" @click="router.back()">‹</button>
      <div>
        <p class="eyebrow">New Request</p>
        <h1>请假申请</h1>
      </div>
    </header>

    <section class="panel leave-form-panel" data-testid="leave-create-form">
      <div class="form-grid">
        <label>
          <span>请假类型</span>
          <select v-model="leaveType" data-testid="leave-type-select">
            <option value="annual">年假</option>
            <option value="sick">病假</option>
            <option value="personal">事假</option>
          </select>
        </label>

        <div class="date-row">
          <label>
            <span>开始日期</span>
            <input v-model="startDate" data-testid="leave-start-date" type="date" />
          </label>
          <label>
            <span>结束日期</span>
            <input v-model="endDate" data-testid="leave-end-date" type="date" />
          </label>
        </div>

        <div class="days-card" data-testid="leave-days-preview">
          <strong>{{ days }}</strong>
          <span>天</span>
          <p>{{ days > 3 ? "超过 3 天，将进入 HR 二审" : "直属上级审批后即可完成" }}</p>
        </div>

        <label>
          <span>请假原因</span>
          <textarea v-model="reason" data-testid="leave-reason-input" placeholder="请说明请假原因" rows="4" />
        </label>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
      <button
        class="primary-button full-button"
        data-testid="leave-submit-button"
        type="button"
        :disabled="submitting"
        @click="submit"
      >
        {{ submitting ? "提交中" : "提交请假申请" }}
      </button>
    </section>
  </main>
</template>
