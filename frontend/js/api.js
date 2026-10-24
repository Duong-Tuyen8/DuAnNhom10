// API Client for the Club Management System
const API_BASE = "http://localhost:8000";

// ---------- Helper ----------
function getToken() {
    return localStorage.getItem("token");
}

function setToken(token) {
    localStorage.setItem("token", token);
}

function clearToken() {
    localStorage.removeItem("token");
}

function getAuthHeaders() {
    const token = getToken();
    return {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
}

async function apiRequest(method, path, body = null) {
    const options = {
        method,
        headers: getAuthHeaders(),
    };
    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE}${path}`, options);

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const detail = errorData.detail || `Lỗi ${response.status}`;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }

    if (response.status === 204) {
        return null;
    }
    return response.json();
}

async function apiFormRequest(method, path, formData) {
    const token = getToken();
    const response = await fetch(`${API_BASE}${path}`, {
        method,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const detail = errorData.detail || `Lỗi ${response.status}`;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return response.json();
}

// ---------- Auth ----------
const AuthAPI = {
    login: (username, password) =>
        apiRequest("POST", "/auth/login", { username, password }),
    // Đăng ký bắt buộc đủ hồ sơ: username, password, email?,
    // full_name, date_of_birth (YYYY-MM-DD), gender (Nam/Nữ/Khác),
    // class_name, department — backend validation không cho để trống.
    register: (payload) =>
        apiRequest("POST", "/auth/register", payload),
    me: () => apiRequest("GET", "/auth/me"),

    // ---- Social login (Google / Facebook / Discord) ----
    socialProviders: () => apiRequest("GET", "/auth/oauth/providers"),
    socialLoginUrl: (provider) => apiRequest("GET", `/auth/oauth/${provider}/login`),
    // Chế độ demo offline: mô phỏng kết quả provider trả về (vẫn tạo vai trò Thành viên)
    socialDemo: (provider, email, name) =>
        apiRequest("POST", "/auth/oauth/demo", { provider, email, name }),
};

// ---------- Members ----------
const MembersAPI = {
    list: () => apiRequest("GET", "/members"),
    get: (id) => apiRequest("GET", `/members/${id}`),
    create: (data) => apiRequest("POST", "/members", data),
    update: (id, data) => apiRequest("PUT", `/members/${id}`, data),
    delete: (id) => apiRequest("DELETE", `/members/${id}`),
    history: (id) => apiRequest("GET", `/members/${id}/history`),
};

// ---------- Committees ----------
const CommitteesAPI = {
    list: () => apiRequest("GET", "/committees"),
    get: (id) => apiRequest("GET", `/committees/${id}`),
    create: (data) => apiRequest("POST", "/committees", data),
    update: (id, data) => apiRequest("PUT", `/committees/${id}`, data),
    delete: (id) => apiRequest("DELETE", `/committees/${id}`),
    members: (id) => apiRequest("GET", `/committees/${id}/members`),
};

// ---------- Activities ----------
const ActivitiesAPI = {
    list: () => apiRequest("GET", "/activities"),
    upcoming: (limit = 10) => apiRequest("GET", `/activities/upcoming?limit=${limit}`),
    get: (id) => apiRequest("GET", `/activities/${id}`),
    create: (data) => apiRequest("POST", "/activities", data),
    update: (id, data) => apiRequest("PUT", `/activities/${id}`, data),
    delete: (id) => apiRequest("DELETE", `/activities/${id}`),

    // ---- Đăng ký tham gia (Thành viên) ----
    register: (id) => apiRequest("POST", `/activities/${id}/register`),
    join: (id) => apiRequest("POST", `/api/activities/${id}/join`),
    unregister: (id) => apiRequest("DELETE", `/activities/${id}/register`),
    myStatus: (id) => apiRequest("GET", `/activities/${id}/registration-status`),
    participants: (id) => apiRequest("GET", `/api/activities/${id}/participants`),
    checkin: (id, photo, feedback = "") => {
        const formData = new FormData();
        formData.append("photo", photo);
        formData.append("feedback", feedback);
        return apiFormRequest("POST", `/api/activities/${id}/checkin`, formData);
    },
    verifyAttendance: (id, memberId, action, rejectReason = "") =>
        apiRequest("PATCH", `/api/activities/${id}/verify-attendance`, {
            member_id: memberId,
            action,
            reject_reason: rejectReason,
        }),

    // ---- Quản lý (Chủ nhiệm / Trưởng ban) ----
    registrations: (id) => apiRequest("GET", `/activities/${id}/registrations`),
    attendees: (id) => apiRequest("GET", `/activities/${id}/attendees`),
    attendeeExportUrl: (id) => `${API_BASE}/activities/${id}/attendees/export`,
    reportExportUrl: (activityId = null) =>
        `${API_BASE}/attendance/export${activityId ? `?activity_id=${activityId}` : ""}`,
};

// ---------- Attendance ----------
const AttendanceAPI = {
    list: (params = {}) => {
        const query = new URLSearchParams(
            Object.entries(params).filter(([, v]) => v)
        ).toString();
        return apiRequest("GET", `/attendance${query ? `?${query}` : ""}`);
    },
    // Lịch sử điểm danh của chính mình (Thành viên)
    mine: () => apiRequest("GET", "/attendance/me"),
    // Thành viên tự điểm danh khi hoạt động diễn ra
    checkIn: (activityId, photo, feedback = "") => {
        const formData = new FormData();
        formData.append("activity_id", activityId);
        formData.append("photo", photo);
        formData.append("feedback", feedback);
        return apiFormRequest("POST", "/attendance/check-in", formData);
    },
    create: (data) => apiRequest("POST", "/attendance", data),
    bulk: (activityId, memberIds, statuses) =>
        apiRequest("POST", "/attendance/bulk", {
            activity_id: activityId,
            member_ids: memberIds,
            statuses: statuses,
        }),
    update: (id, status, feedback) =>
        apiRequest(
            "PUT",
            `/attendance/${id}${status ? `?status=${status}` : ""}${feedback ? `&feedback=${encodeURIComponent(feedback)}` : ""}`
        ),
    pending: () => apiRequest("GET", "/api/attendance/pending"),
    verify: (id, status, rejectReason = "") =>
        apiRequest("PATCH", `/api/attendance/${id}/verify`, {
            status,
            reject_reason: rejectReason,
        }),
    delete: (id) => apiRequest("DELETE", `/attendance/${id}`),
};

// ---------- Tasks ----------
const TasksAPI = {
    list: (params = {}) => {
        const query = new URLSearchParams(
            Object.entries(params).filter(([, v]) => v)
        ).toString();
        return apiRequest("GET", `/tasks${query ? `?${query}` : ""}`);
    },
    create: (data) => apiRequest("POST", "/tasks", data),
    update: (id, data) => apiRequest("PUT", `/tasks/${id}`, data),
    delete: (id) => apiRequest("DELETE", `/tasks/${id}`),
};

// ---------- Notifications ----------
const NotificationsAPI = {
    list: () => apiRequest("GET", "/notifications"),
    create: (data) => apiRequest("POST", "/notifications", data),
    delete: (id) => apiRequest("DELETE", `/notifications/${id}`),
};

// ---------- AI ----------
const AIAPI = {
    notificationDraft: (activityOrInfo) =>
        apiRequest("POST", "/ai/notifications", typeof activityOrInfo === "number"
            ? { activity_id: activityOrInfo }
            : activityOrInfo),
    summary: (activityId) =>
        apiRequest("POST", "/ai/summaries", { activity_id: activityId }),
    recommendations: () => apiRequest("GET", "/ai/activity-recommendations?limit=5"),
};

// ---------- AI Chatbot ----------
const ChatAPI = {
    suggestions: () => apiRequest("GET", "/api/chat/suggestions"),
    ask: (message, history = []) =>
        apiRequest("POST", "/api/chat", { message, history }),

    /**
     * Hỏi đáp dạng streaming qua Server-Sent Events.
     * `onDelta(text)` được gọi mỗi khi nhận thêm nội dung;
     * `onMeta(info)` nhận thông tin context/ provider.
     */
    async stream(message, history, { onDelta, onMeta, onDone, onError } = {}) {
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({ message, history }),
        });

        if (!response.ok || !response.body) {
            onError?.(new Error(`Lỗi ${response.status}`));
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        try {
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                // SSE: mỗi event kết thúc bằng dòng trống
                let boundary = buffer.indexOf("\n\n");
                while (boundary !== -1) {
                    const rawEvent = buffer.slice(0, boundary);
                    buffer = buffer.slice(boundary + 2);
                    boundary = buffer.indexOf("\n\n");

                    const line = rawEvent.split("\n").find((l) => l.startsWith("data: "));
                    if (!line) continue;

                    const payload = JSON.parse(line.slice(6));
                    if (payload.type === "delta") onDelta?.(payload.text);
                    else if (payload.type === "meta") onMeta?.(payload);
                    else if (payload.type === "done") onDone?.();
                    else if (payload.type === "error") onError?.(new Error(payload.message));
                }
            }
        } catch (err) {
            onError?.(err);
        }
    },
};

// ---------- Statistics ----------
const StatsAPI = {
    overview: () => apiRequest("GET", "/stats/overview"),
    activities: () => apiRequest("GET", "/stats/activities"),
    topMembers: (limit = 10) => apiRequest("GET", `/stats/members/top?limit=${limit}`),
    memberParticipation: (memberId) =>
        apiRequest("GET", `/stats/members/participation?member_id=${memberId}`),
};