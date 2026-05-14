<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { BadgeSummary, request, WorkflowInstance, WorkflowTask, WorkflowTemplate } from "../api";

type TabKey = "new" | "todo" | "urged" | "processing" | "returned" | "completed";

const route = useRoute();
const router = useRouter();
const tabs: Array<{ key: TabKey; label: string; hint: string }> = [
  { key: "new", label: "新办", hint: "可发起的流程" },
  { key: "todo", label: "待办", hint: "需要我处理" },
  { key: "urged", label: "催办", hint: "被催促处理" },
  { key: "processing", label: "进行中", hint: "我发起的流程" },
  { key: "returned", label: "退回", hint: "v1.6C 空态预留" },
  { key: "completed", label: "已完成", hint: "闭环流程" },
];

const activeTab = ref<TabKey>(normalizeTab(route.query.tab));
const loading = ref(false);
const error = ref("");
const templates = ref<WorkflowTemplate[]>([]);
const tasks = ref<WorkflowTask[]>([]);
const instances = ref<WorkflowInstance[]>([]);
const badgeSummary = ref<BadgeSummary | null>(null);

const emptyText = computed(() => {
  if (activeTab.value === "returned") return "暂无退回申请";
  return "当前没有流程数据";
});

onMounted(load);

watch(
  () => route.query.tab,
  (value) => {
    activeTab.value = normalizeTab(value);
    load();
  }
);

function normalizeTab(value: unknown): TabKey {
  return tabs.some((tab) => tab.key === value) ? (value as TabKey) : "todo";
}

function switchTab(key: TabKey) {
  router.replace({ path: "/workflow", query: { tab: key } });
}

async function load() {
  error.value = "";
  loading.value = true;
  templates.value = [];
  tasks.value = [];
  instances.value = [];
  try {
    await loadBadgeSummary();
    if (activeTab.value === "new") {
      templates.value = (await request<{ templates: WorkflowTemplate[] }>("/api/workflow/templates")).templates;
    } else if (activeTab.value === "todo" || activeTab.value === "urged") {
      tasks.value = (
        await request<{ tasks: WorkflowTask[] }>(`/api/workflow/tasks?bucket=${activeTab.value}`)
      ).tasks;
    } else {
      instances.value = (
        await request<{ instances: WorkflowInstance[] }>(`/api/workflow/instances?bucket=${activeTab.value}`)
      ).instances;
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : "流程加载失败";
  } finally {
    loading.value = false;
  }
}

async function loadBadgeSummary() {
  try {
    badgeSummary.value = await request<BadgeSummary>("/api/badges/summary");
  } catch {
    badgeSummary.value = null;
  }
}

function openInstance(id: number) {
  router.push(`/workflow/detail/${id}`);
}

function openTemplate(item: WorkflowTemplate) {
  if (item.entry === "wap:#/new/leave") {
    router.push("/new/leave");
  }
}

function templateEntryLabel(item: WorkflowTemplate) {
  if (item.entry.startsWith("wap:")) return "WAP 发起";
  if (item.entry.startsWith("native:")) return "App 原生发起";
  return item.optional ? "预留入口" : "流程入口";
}

function tabCount(key: TabKey) {
  const workflow = badgeSummary.value?.workflow;
  if (!workflow) return 0;
  if (key === "todo") return workflow.todo;
  if (key === "urged") return workflow.urged;
  if (key === "processing") return workflow.processing;
  if (key === "returned") return workflow.returned;
  return 0;
}

function isAlertBadge(key: TabKey) {
  return key === "todo" || key === "urged" || key === "returned";
}
</script>

<template>
  <main class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Workflow Center</p>
        <h1>流程中心</h1>
      </div>
      <button class="ghost-button" type="button" @click="load">刷新</button>
    </header>

    <nav class="tabs" aria-label="流程状态">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="{ active: activeTab === tab.key }"
        :data-testid="`workflow-tab-${tab.key}`"
        type="button"
        @click="switchTab(tab.key)"
      >
        <strong>{{ tab.label }}</strong>
        <em
          v-if="tabCount(tab.key) > 0"
          class="tab-badge"
          :class="{ alert: isAlertBadge(tab.key) }"
        >
          {{ tabCount(tab.key) > 99 ? "99+" : tabCount(tab.key) }}
        </em>
        <span>{{ tab.hint }}</span>
      </button>
    </nav>

    <section class="panel">
      <div v-if="loading" class="screen-center compact">
        <div class="spinner" />
        <p>同步流程数据</p>
      </div>
      <p v-else-if="error" class="error">{{ error }}</p>

      <div v-else-if="activeTab === 'new'" class="list">
        <button
          v-for="item in templates"
          :key="item.id"
          class="card clickable"
          :class="{ disabled: !item.entry.startsWith('wap:') }"
          :data-testid="`workflow-new-${item.id}`"
          type="button"
          :disabled="!item.entry.startsWith('wap:')"
          @click="openTemplate(item)"
        >
          <div>
            <p class="tag">新办</p>
            <h2>{{ item.title }}</h2>
            <p>{{ item.description }}</p>
          </div>
          <span class="status">{{ templateEntryLabel(item) }}</span>
        </button>
      </div>

      <div v-else-if="activeTab === 'todo' || activeTab === 'urged'" class="list">
        <button
          v-for="item in tasks"
          :key="item.id"
          class="card clickable"
          :data-testid="`workflow-task-${item.id}`"
          type="button"
          @click="openInstance(item.instance_id)"
        >
          <div>
            <p class="tag">{{ item.node_key === "manager_review" ? "上级审批" : "HR 审批" }}</p>
            <h2>{{ item.title }}</h2>
            <p>{{ item.applicant_name }} · {{ item.created_at }}</p>
          </div>
          <span class="status" :class="{ warn: item.urged }">{{ item.urged ? "已催办" : "待处理" }}</span>
        </button>
      </div>

      <div v-else class="list">
        <button
          v-for="item in instances"
          :key="item.id"
          class="card clickable"
          :data-testid="`workflow-instance-${item.id}`"
          type="button"
          @click="openInstance(item.id)"
        >
          <div>
            <p class="tag">{{ item.biz_type }}</p>
            <h2>{{ item.title }}</h2>
            <p>{{ item.applicant_name }} · {{ item.updated_at }}</p>
          </div>
          <span class="status">{{ item.status }}</span>
        </button>
      </div>

      <div
        v-if="!loading && !error && activeTab === 'returned' && instances.length === 0"
        data-testid="workflow-empty-returned"
        class="empty"
      >
        暂无退回申请
      </div>
      <div
        v-else-if="!loading && !error && activeTab !== 'new' && tasks.length === 0 && instances.length === 0"
        class="empty"
      >
        {{ emptyText }}
      </div>
    </section>
  </main>
</template>
