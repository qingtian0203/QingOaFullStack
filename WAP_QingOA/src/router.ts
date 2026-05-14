import { createRouter, createWebHashHistory } from "vue-router";
import LeaveRequestForm from "./views/LeaveRequestForm.vue";
import WorkflowCenter from "./views/WorkflowCenter.vue";
import WorkflowDetail from "./views/WorkflowDetail.vue";

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", redirect: "/workflow?tab=todo" },
    { path: "/new/leave", component: LeaveRequestForm, meta: { title: "请假申请" } },
    { path: "/workflow", component: WorkflowCenter, meta: { title: "流程中心" } },
    { path: "/workflow/detail/:id", component: WorkflowDetail, meta: { title: "流程详情" } },
  ],
});
