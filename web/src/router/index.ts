import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "setup",
    component: () => import("@/views/SetupView.vue"),
  },
  {
    path: "/history",
    name: "history",
    component: () => import("@/views/HistoryView.vue"),
  },
  {
    path: "/sim/:simId",
    name: "sim",
    component: () => import("@/views/SimulationRunView.vue"),
    props: true,
  },
  {
    path: "/sim/:simId/report",
    name: "report",
    component: () => import("@/views/ReportView.vue"),
    props: true,
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: "/",
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
