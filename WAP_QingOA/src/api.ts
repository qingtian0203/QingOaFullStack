export interface ApiResponse<T> {
  code: number;
  msg: string;
  data: T;
}

export interface LoginData {
  user_id: number;
  token: string;
  username: string;
  name: string;
}

export interface UserInfo {
  user_id: number;
  username: string;
  name: string;
  dept: string;
  role: string;
  avatar_url: string;
  has_punch_permission: boolean;
}

export interface WorkflowTemplate {
  id: string;
  biz_type: string;
  title: string;
  description: string;
  enabled: boolean;
  optional: boolean;
  entry: string;
}

export interface WorkflowTask {
  id: number;
  instance_id: number;
  biz_type: string;
  biz_id: number;
  title: string;
  instance_status: string;
  current_node: string | null;
  applicant_id: number;
  applicant_name: string;
  node_key: string;
  assignee_id: number;
  assignee_name: string;
  status: string;
  urged: boolean;
  action: string | null;
  note: string | null;
  created_at: string | null;
  updated_at: string | null;
  completed_at: string | null;
}

export interface WorkflowInstance {
  id: number;
  biz_type: string;
  biz_id: number;
  title: string;
  applicant_id: number;
  applicant_name: string;
  status: string;
  current_node: string | null;
  created_at: string | null;
  updated_at: string | null;
  timeline?: WorkflowTask[];
  business?: Record<string, unknown> | LeavePayload | null;
  available_actions?: WorkflowAction[];
}

export interface WorkflowAction {
  action: "approve" | "reject" | "return" | "resubmit" | "cancel" | string;
  label: string;
  method: "POST" | string;
  api: string;
  task_id?: number;
}

export interface BadgeSummary {
  im: {
    unread_total: number;
  };
  workflow: {
    todo: number;
    urged: number;
    processing: number;
    returned: number;
    actionable_total: number;
  };
  mine: {
    punch_appeal_review: number;
  };
}

export interface LeavePayload {
  id: number;
  user_id: number;
  username: string;
  applicant_name: string;
  process_instance_id: number;
  leave_type: string;
  leave_type_label: string;
  start_date: string;
  end_date: string;
  days: number;
  reason: string;
  status: string;
  status_label: string;
  manager_note: string | null;
  hr_note: string | null;
  return_reason: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface LeaveRequestBody {
  leave_type: string;
  start_date: string;
  end_date: string;
  reason: string;
}

declare global {
  interface Window {
    QingOA?: {
      getToken?: () => string | Promise<string>;
    };
  }
}

const TOKEN_KEY = "qingoa_token";

export async function resolveToken(): Promise<string> {
  try {
    const bridgeToken = await Promise.resolve(window.QingOA?.getToken?.());
    if (bridgeToken) return bridgeToken;
  } catch {
    // App Bridge 不存在或异常时走浏览器调试兜底。
  }
  return window.localStorage.getItem(TOKEN_KEY) || "";
}

export function saveToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

export async function login(username: string, password: string): Promise<LoginData> {
  const body = await rawRequest<LoginData>("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  saveToken(body.token);
  return body;
}

export async function getUserInfo(): Promise<UserInfo> {
  return request<UserInfo>("/api/auth/user-info");
}

export async function createLeaveRequest(body: LeaveRequestBody): Promise<LeavePayload> {
  return request<LeavePayload>("/api/leave/requests", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function postJson<T>(path: string, body: Record<string, unknown> = {}): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await resolveToken();
  if (!token) throw new Error("NO_TOKEN");
  return rawRequest<T>(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init.headers || {}),
    },
  });
}

async function rawRequest<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  const body = (await response.json()) as ApiResponse<T>;
  if (body.code === 1002) {
    clearToken();
    throw new Error("TOKEN_EXPIRED");
  }
  if (body.code !== 0) {
    throw new Error(body.msg || `请求失败：${body.code}`);
  }
  return body.data;
}
