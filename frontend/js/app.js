// Club Management System - App Logic
let currentUser = null;
let currentRole = "thanh_vien";
let chatHistory = [];
let activitiesCache = [];
let proofImageObjectUrl = null;

const ROLE_LABELS = {
    chu_nhiem: "Chủ nhiệm",
    truong_ban: "Trưởng ban",
    thanh_vien: "Thành viên",
};

const ADMIN_OR_LEADER_ROLES = ["chu_nhiem", "truong_ban"];

function isAdminOrLeader() {
    return ADMIN_OR_LEADER_ROLES.includes(currentRole);
}

function isMember() {
    return currentRole === "thanh_vien";
}

document.addEventListener("DOMContentLoaded", () => { initApp(); });

function initApp() {
    const token = getToken();
    if (token) {
        const userData = parseTokenUser(token);
        if (userData) { currentUser = userData; currentRole = userData.role; showApp(); }
        else { clearToken(); }
    }
    document.getElementById("login-form").addEventListener("submit", handleLogin);
    document.getElementById("register-form").addEventListener("submit", handleRegister);
    document.querySelectorAll(".login-tab").forEach((tab) => {
        tab.addEventListener("click", () => {
            const tabName = tab.dataset.tab;
            document.querySelectorAll(".login-tab").forEach((t) => t.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById("login-form").style.display = tabName === "login" ? "flex" : "none";
            document.getElementById("register-form").style.display = tabName === "register" ? "flex" : "none";
        });
    });
    document.querySelectorAll(".social-btn").forEach((btn) => {
        btn.addEventListener("click", () => handleSocialLogin(btn.dataset.provider));
    });
    document.querySelectorAll(".nav-item").forEach((item) => {
        item.addEventListener("click", () => navigateTo(item.dataset.page));
    });
    document.getElementById("modal-close").addEventListener("click", closeModal);
    document.getElementById("modal-overlay").addEventListener("click", (e) => {
        if (e.target === e.currentTarget) closeModal();
    });
    initLogout();
    document.getElementById("btn-add-member").addEventListener("click", () => openMemberModal());
    document.getElementById("btn-add-committee").addEventListener("click", () => openCommitteeModal());
    document.getElementById("btn-add-activity").addEventListener("click", () => openActivityModal());
    document.getElementById("btn-add-task").addEventListener("click", () => openTaskModal());
    document.getElementById("member-search").addEventListener("input", debounce(loadMembers, 300));
    document.getElementById("task-status-filter").addEventListener("change", loadTasks);
    document.getElementById("activity-filter").addEventListener("change", loadActivities);
    document.getElementById("btn-load-attendance").addEventListener("click", loadAttendance);
    document.getElementById("btn-refresh-pending").addEventListener("click", loadPendingAttendance);
    document.getElementById("btn-export-attendance").addEventListener("click", exportAttendanceReport);
    document.getElementById("btn-ai-notification").addEventListener("click", aiNotification);
    document.getElementById("btn-ai-summary").addEventListener("click", aiSummary);
    document.getElementById("btn-ai-recommendations").addEventListener("click", loadAIActivityRecommendations);
    initChatWidget();
    handleOAuthRedirect();
    if (getToken()) { loadAllData(); }
}

function parseTokenUser(token) {
    try {
        const payload = token.split(".")[1];
        const decoded = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
        const stored = localStorage.getItem("user_info");
        return stored ? JSON.parse(stored) : { user_id: decoded.sub, role: decoded.role, username: "user" };
    } catch { return null; }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;
    const msgEl = document.getElementById("login-msg");
    if (!username || !password) { showErrorEl(msgEl, "Vui lòng nhập đầy đủ thông tin"); return; }
    try {
        const result = await AuthAPI.login(username, password);
        applySession(result);
        showApp(); loadAllData(); showToast("Đăng nhập thành công! 👋");
    } catch (err) { showErrorEl(msgEl, err.message); }
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById("reg-username").value.trim();
    const password = document.getElementById("reg-password").value;
    const email = document.getElementById("reg-email").value.trim() || null;
    // ---- Hồ sơ bắt buộc khi đăng ký (không cho để trống) ----
    const full_name = document.getElementById("reg-fullname").value.trim();
    const date_of_birth = document.getElementById("reg-dob").value; // YYYY-MM-DD
    const gender = document.getElementById("reg-gender").value;
    const class_name = document.getElementById("reg-class").value.trim();
    const department = document.getElementById("reg-department").value.trim();
    const msgEl = document.getElementById("login-msg");
    if (!username || !password) { showErrorEl(msgEl, "Vui lòng nhập đầy đủ thông tin"); return; }
    if (!full_name) { showErrorEl(msgEl, "Vui lòng nhập Họ và tên"); return; }
    if (!date_of_birth) { showErrorEl(msgEl, "Vui lòng chọn Ngày sinh (YYYY-MM-DD)"); return; }
    if (!gender) { showErrorEl(msgEl, "Vui lòng chọn Giới tính (Nam / Nữ / Khác)"); return; }
    if (!class_name) { showErrorEl(msgEl, "Vui lòng nhập Lớp"); return; }
    if (!department) { showErrorEl(msgEl, "Vui lòng nhập Khoa"); return; }
    try {
        // Không gửi vai trò: backend luôn tạo tài khoản với vai trò Thành viên
        await AuthAPI.register({
            username, password, email,
            full_name, date_of_birth, gender, class_name, department,
        });
        // FIX 1a: popup + redirect về Đăng nhập (không auto-login nữa)
        showToast("Đăng ký tài khoản thành công! 🎉");
        document.querySelector('.login-tab[data-tab="login"]').click();
        document.getElementById("login-username").value = username;
        const okEl = document.getElementById("login-msg");
        okEl.className = "form-msg success";
        okEl.textContent = "Đăng ký tài khoản thành công! Vui lòng đăng nhập.";
        document.getElementById("register-form").reset();
    } catch (err) { showErrorEl(msgEl, err.message); }
}

/** Lưu token + thông tin người dùng sau khi đăng nhập thành công. */
function applySession(result) {
    setToken(result.access_token);
    currentUser = {
        user_id: result.user_id,
        username: result.username,
        role: result.role,
        member_id: result.member_id,
    };
    currentRole = result.role;
    localStorage.setItem("user_info", JSON.stringify(currentUser));
}

// ---------- Social login (Google / Facebook / Discord) ----------
async function handleSocialLogin(provider) {
    const hint = document.getElementById("social-hint");
    hint.textContent = `Đang kết nối ${provider}…`;
    hint.className = "social-hint";

    // Nếu provider đã được cấu hình CLIENT_ID/SECRET -> chuyển hướng OAuth thật
    try {
        const info = await AuthAPI.socialLoginUrl(provider);
        if (info && info.authorize_url) {
            window.location.href = info.authorize_url;
            return;
        }
    } catch (err) {
        // Chưa cấu hình -> dùng chế độ demo offline bên dưới
    }

    try {
        const result = await AuthAPI.socialDemo(provider);
        applySession(result);
        hint.textContent = "";
        showApp(); loadAllData();
        const label = provider.charAt(0).toUpperCase() + provider.slice(1);
        showToast(
            result.is_new_user
                ? `Đã tạo tài khoản Thành viên qua ${label} 🎉`
                : `Chào mừng trở lại qua ${label}! 👋`
        );
    } catch (err) {
        hint.textContent = err.message;
        hint.className = "social-hint error";
    }
}

/** Nhận token/ lỗi do backend trả về qua query string sau khi OAuth callback. */
async function handleOAuthRedirect() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("oauth_token");
    const error = params.get("oauth_error");
    if (!token && !error) return;

    window.history.replaceState({}, document.title, window.location.pathname);
    const msgEl = document.getElementById("login-msg");

    if (error) {
        showErrorEl(msgEl, error);
        return;
    }

    setToken(token);
    try {
        const me = await AuthAPI.me();
        currentUser = me;
        currentRole = me.role;
        localStorage.setItem("user_info", JSON.stringify(me));
        showApp(); loadAllData();
        showToast("Đăng nhập mạng xã hội thành công! 🎉");
    } catch (err) {
        clearToken();
        showErrorEl(msgEl, err.message);
    }
}

function showErrorEl(el, message) {
    el.textContent = message;
    el.className = "form-msg error";
}

function showApp() {
    document.getElementById("login-page").style.display = "none";
    document.getElementById("app").style.display = "flex";
    document.getElementById("current-username").textContent = currentUser.username || "-";
    document.getElementById("current-role").textContent = formatRole(currentRole);
    document.querySelectorAll(".user-avatar").forEach((el) => {
        el.textContent = getInitials(currentUser.username || "U");
    });
    const heroUser = document.getElementById("hero-username");
    if (heroUser) heroUser.textContent = currentUser.username || "bạn";
    applyRoleBasedUI();
    navigateTo("dashboard");
}

/**
 * Phân quyền giao diện theo vai trò (role-based UI).
 * Mọi phần tử có [data-roles] chỉ hiển thị với các vai trò được liệt kê;
 * các phần tử không có thuộc tính này hiển thị cho mọi vai trò.
 */
function applyRoleBasedUI() {
    document.querySelectorAll("[data-roles]").forEach((el) => {
        const allowed = el.dataset.roles.split(/\s+/).filter(Boolean);
        el.style.display = allowed.includes(currentRole) ? "" : "none";
    });

    const memberDashboard = document.getElementById("member-dashboard");
    if (memberDashboard) memberDashboard.style.display = isMember() ? "block" : "none";

    const heroSub = document.getElementById("hero-sub");
    if (heroSub) {
        heroSub.textContent = isMember()
            ? "Xem hoạt động, đăng ký tham gia, điểm danh và hỏi trợ lý AI về lịch của bạn."
            : "Quản lý thành viên, hoạt động, điểm danh, nhiệm vụ & thống kê của CLB.";
    }

    const navActive = document.querySelector(".nav-item.active");
    if (navActive) {
        const allowed = (navActive.dataset.roles || "").split(/\s+/).filter(Boolean);
        if (allowed.length && !allowed.includes(currentRole)) navigateTo("dashboard");
    }
}

function formatRole(role) {
    return ROLE_LABELS[role] || role;
}

function getInitials(name) {
    if (!name) return "U";
    const parts = name.split(/[\s_.-]+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.substring(0, 2).toUpperCase();
}

function handleLogout() {
    clearToken();
    localStorage.removeItem("user_info");
    location.reload();
}

function navigateTo(page) {
    const target = document.getElementById(`page-${page}`);
    // Không cho Thành viên truy cập trang chỉ dành cho quản lý
    const allowed = (target?.dataset?.roles || "").split(/\s+/).filter(Boolean);
    if (target && allowed.length && !allowed.includes(currentRole)) {
        page = "dashboard";
    }

    document.querySelectorAll(".nav-item").forEach((i) => i.classList.remove("active"));
    const item = document.querySelector(`.nav-item[data-page="${page}"]`);
    if (item) item.classList.add("active");
    document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
    const pg = document.getElementById(`page-${page}`);
    if (pg) pg.classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (page === "my-activities") loadMyActivities();
    if (page === "attendance") loadPendingAttendance();
}

let toastTimer;
function showToast(message) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 3000);
}

let modalCallback = null;
function openModal(title, bodyHtml, callback) {
    document.getElementById("modal-title").textContent = title;
    document.getElementById("modal-body").innerHTML = bodyHtml;
    document.getElementById("modal-overlay").style.display = "flex";
    modalCallback = callback;
    setTimeout(() => {
        const saveBtn = document.getElementById("modal-body").querySelector("#member-save-btn, #committee-save-btn, #act-save-btn, #task-save-btn");
        if (saveBtn) saveBtn.addEventListener("click", executeModalCallback);
    }, 0);
}

// BUG FIX: modal trước đây đóng ngay cả khi callback async còn chạy
// (tạo hoạt động xong chưa re-fetch). Giờ đợi callback xong mới đóng,
// nếu callback ném lỗi thì giữ modal để người dùng sửa.
async function executeModalCallback() {
    if (!modalCallback) return;
    const cb = modalCallback;
    try {
        await cb();
        // Chỉ đóng khi không có toast lỗi vừa hiện? Đơn giản: đóng sau khi xong
        closeModal();
    } catch (err) {
        showToast(err?.message || "Có lỗi xảy ra");
    }
}

function closeModal() {
    document.getElementById("modal-overlay").style.display = "none";
    modalCallback = null;
    if (proofImageObjectUrl) URL.revokeObjectURL(proofImageObjectUrl);
    proofImageObjectUrl = null;
}

function debounce(fn, ms) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), ms);
    };
}

// ---------- Load All Data ----------
async function loadAllData() {
    try {
        // FIX 2c: luôn fetch activities cho mọi role (Chủ nhiệm + Thành viên).
        // Không để Promise.all fail một job làm mất cả danh sách hoạt động.
        const jobs = [loadDashboard(), loadNotifications()];
        if (isAdminOrLeader()) {
            jobs.push(
                loadMembers(), loadCommittees(), loadTasks(),
                loadAttendanceSelects(), loadStatsPage()
            );
        } else {
            jobs.push(loadMyActivities());
        }
        await Promise.allSettled(jobs);
        // FIX 2a/2b: hoạt động phải load RIÊNG và render ngay, không phụ thuộc
        // dashboard/thống kê. Đây là nguyên nhân "tạo xong nhưng list trống".
        await loadActivities();
    } catch (err) {
        console.error("Load data error:", err);
        showToast("Lỗi tải dữ liệu: " + err.message);
    }
}

// ---------- Dashboard ----------
async function loadDashboard() {
    try {
        const data = await StatsAPI.overview();
        document.getElementById("stat-members").textContent = data.total_members;
        document.getElementById("stat-committees").textContent = data.total_committees;
        document.getElementById("stat-activities").textContent = data.total_activities;
        document.getElementById("stat-tasks").textContent = data.total_tasks;
        document.getElementById("stat-tasks-done").textContent = data.tasks_done;
        document.getElementById("stat-attendance").textContent = data.total_attendance;
        if (isAdminOrLeader()) renderTopMembers(await StatsAPI.topMembers(10));
    } catch (err) { console.error("Dashboard error:", err); }
}

// ---------- Khu vực dành cho Thành viên ----------
// BUG FIX: trang "Hoạt động & Sự kiện" của Thành viên render từ activitiesCache
// (đã fetch GET /activities cho mọi role). Mảng rỗng → thông báo rõ ràng.
async function loadMyActivities() {
    if (!isMember()) return;
    try {
        // Đảm bảo cache đã có dữ liệu (trường hợp gọi trực tiếp)
        if (!activitiesCache || activitiesCache.length === 0) {
            try { activitiesCache = await ActivitiesAPI.list(); } catch { /* bỏ qua, dùng upcoming */ }
        }
        const upcoming = await ActivitiesAPI.upcoming(10);
        const upcomingList = document.getElementById("member-upcoming-list");
        upcomingList.innerHTML = upcoming.length
            ? upcoming.map((a) => `
                <div class="list-item">
                    <div class="list-item-main">
                        <div class="list-item-title">${escapeHtml(a.title)}</div>
                        <div class="list-item-subtitle">
                            📅 ${formatDateTime(a.start_time)} → ${formatDateTime(a.end_time)}<br>
                            📍 ${escapeHtml(a.location || "Chưa có địa điểm")}
                        </div>
                        <div class="card-meta" style="margin-top:8px">
                            ${registrationBadge(a)}
                            ${attendanceBadge(a)}
                            <span class="badge badge-primary">${a.registration_count} đăng ký</span>
                        </div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-outline btn-sm" onclick="openActivityDetail(${a.id})">Chi tiết</button>
                        ${memberActionButtons(a)}
                    </div>
                </div>`).join("")
            : `<div class="empty-state"><div class="icon">📅</div>Chưa có hoạt động nào sắp diễn ra</div>`;

        const mine = await AttendanceAPI.mine();
        const attendanceList = document.getElementById("member-attendance-list");
        attendanceList.innerHTML = mine.attendances.length
            ? mine.attendances.slice(0, 5).map((r) => `
                <div class="list-item">
                    <div class="list-item-main">
                        <div class="list-item-title">${escapeHtml(r.activity_title)}</div>
                        <div class="list-item-subtitle">${formatDateTime(r.checked_at)} • 📍 ${escapeHtml(r.location || "-")}</div>
                    </div>
                    <span class="badge ${statusBadgeClass(r.status)}">${escapeHtml(r.status_label)}</span>
                </div>`).join("")
            : `<div class="empty-state"><div class="icon">📋</div>Bạn chưa điểm danh hoạt động nào</div>`;

        // Danh sách đăng ký tham gia (trang "Hoạt động của tôi")
        const regList = document.getElementById("my-registrations-list");
        if (regList) {
            const registered = activitiesCache.filter((a) => a.is_registered);
            regList.innerHTML = registered.length
                ? registered.map((a) => `
                    <div class="list-item">
                        <div class="list-item-main">
                            <div class="list-item-title">${escapeHtml(a.title)}</div>
                            <div class="list-item-subtitle">
                                📅 ${formatDateTime(a.start_time)} → ${formatDateTime(a.end_time)}<br>
                                📍 ${escapeHtml(a.location || "Chưa có địa điểm")}
                            </div>
                            <div class="card-meta" style="margin-top:8px">
                                ${attendanceBadge(a)}
                            </div>
                        </div>
                        <div class="list-item-actions">
                            <button class="btn btn-outline btn-sm" onclick="openActivityDetail(${a.id})">Chi tiết</button>
                            ${memberActionButtons(a)}
                        </div>
                    </div>`).join("")
                : `<div class="empty-state"><div class="icon">📌</div>Bạn chưa đăng ký hoạt động nào</div>`;
        }

        const list = document.getElementById("my-attendance-list");
        if (list) {
            list.innerHTML = mine.attendances.length
                ? mine.attendances.map((r) => `
                    <div class="list-item">
                        <div class="list-item-main">
                            <div class="list-item-title">${escapeHtml(r.activity_title)}</div>
                            <div class="list-item-subtitle">${formatDateTime(r.checked_at)} • 📍 ${escapeHtml(r.location || "-")}
                            ${r.feedback ? `<br>💬 ${escapeHtml(r.feedback)}` : ""}</div>
                        </div>
                        <span class="badge ${statusBadgeClass(r.status)}">${escapeHtml(r.status_label)}</span>
                    </div>`).join("")
                : `<div class="empty-state"><div class="icon">📋</div>Bạn chưa điểm danh hoạt động nào</div>`;
        }
    } catch (err) { console.error("My activities error:", err); }
}

async function loadAIActivityRecommendations() {
    const container = document.getElementById("ai-recommendations-list");
    container.innerHTML = `<div class="empty-state">Đang tìm hoạt động phù hợp…</div>`;
    try {
        const result = await AIAPI.recommendations();
        const recommendations = result.recommendations || [];
        container.innerHTML = recommendations.length
            ? recommendations.map((activity) => `
                <div class="list-item">
                    <div class="list-item-main">
                        <div class="list-item-title">${escapeHtml(activity.title)}</div>
                        <div class="list-item-subtitle">
                            📅 ${formatDateTime(activity.start_time)} → ${formatDateTime(activity.end_time)}<br>
                            📍 ${escapeHtml(activity.location || "Chưa có địa điểm")}<br>
                            💡 ${escapeHtml(activity.reason)}
                        </div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-outline btn-sm" onclick="openActivityDetail(${activity.activity_id})">Chi tiết</button>
                        <button class="btn btn-primary btn-sm" onclick="registerActivity(${activity.activity_id})">✅ Tham gia</button>
                    </div>
                </div>`).join("")
            : `<div class="empty-state"><div class="icon">🤖</div>Hiện chưa có hoạt động sắp tới phù hợp để gợi ý</div>`;
    } catch (err) {
        container.innerHTML = `<div class="empty-state">Không tải được gợi ý hoạt động.</div>`;
        showToast(err.message);
    }
}

function registrationBadge(a) {
    if (!a.is_registered) return "";
    return `<span class="badge badge-success">✅ Đã tham gia</span>`;
}

function attendanceBadge(a) {
    if (!a.my_attendance_status) return "";
    return `<span class="badge ${statusBadgeClass(a.my_attendance_status)}">Điểm danh: ${escapeHtml(attendanceStatusLabel(a.my_attendance_status))}</span>`;
}

function statusBadgeClass(status) {
    if (["present", "late", "ATTENDED"].includes(status)) return "badge-success";
    if (["PENDING_CHECKIN", "pending"].includes(status)) return "badge-warning";
    if (status === "REGISTERED") return "badge-primary";
    return "badge-danger";
}

function attendanceStatusLabel(status) {
    return ({
        present: "Đã điểm danh",
        late: "Đã điểm danh",
        absent: "Vắng",
        REGISTERED: "Đã tham gia",
        PENDING_CHECKIN: "Chờ duyệt điểm danh",
        pending: "Chờ duyệt điểm danh",
        ATTENDED: "Đã điểm danh",
        REJECTED: "Bị từ chối điểm danh",
        rejected: "Bị từ chối điểm danh",
    })[status] || status;
}

/** Nút hành động TRÊN THẺ hoạt động dành cho Thành viên.
 * Yêu cầu mới: nút "Tham gia" nổi bật; đã tham gia → nhãn "Đã tham gia"
 * (disable, KHÔNG cho hủy); điểm danh bắt buộc nộp ảnh minh chứng. */
function memberActionButtons(a) {
    if (!isMember()) return "";
    const buttons = [];
    // 1) Tham gia / Đã tham gia (disable, không hủy theo yêu cầu mới)
    if (!a.is_registered) {
        buttons.push(`<button class="btn btn-primary btn-sm btn-join" onclick="registerActivity(${a.id})">✅ Tham gia</button>`);
    } else {
        buttons.push(`<button class="btn btn-sm" disabled style="background:#dcfce7;color:#15803d;border:1px solid #bbf7d0;cursor:default">✔ Đã tham gia</button>`);
    }
    // 2) Chờ duyệt / đã duyệt / từ chối được hiển thị theo trạng thái thật.
    if (["PENDING_CHECKIN", "pending"].includes(a.my_attendance_status)) {
        buttons.push(`<button class="btn btn-sm" disabled style="background:#fef3c7;color:#92400e;cursor:default">⏳ Chờ duyệt</button>`);
    } else if (["ATTENDED", "present", "late"].includes(a.my_attendance_status)) {
        const t = a.my_checked_at ? ` ${formatDateTime(a.my_checked_at)}` : "";
        buttons.push(`<button class="btn btn-sm" disabled title="Đã điểm danh${t}" style="background:#dbeafe;color:#1d4ed8;border:1px solid #bfdbfe;cursor:default">✅ Đã điểm danh</button>`);
    } else if (a.is_registered && ["REJECTED", "rejected"].includes(a.my_attendance_status)) {
        buttons.push(a.can_check_in
            ? `<button class="btn btn-orange btn-sm" onclick="checkInActivity(${a.id})">📷 Điểm danh lại</button>`
            : `<button class="btn btn-sm" disabled title="${escapeHtml(a.reject_reason || "Ảnh bị từ chối")}" style="background:#fee2e2;color:#991b1b;cursor:default">↻ Điểm danh lại khi mở</button>`);
    } else if (a.is_registered && a.can_check_in) {
        buttons.push(`<button class="btn btn-orange btn-sm" onclick="checkInActivity(${a.id})">📍 Điểm danh</button>`);
    }
    // Yêu cầu mới: KHÔNG còn nút Hủy đăng ký trên thẻ (đã tham gia là ghi nhận).
    return buttons.join(" ");
}

function isActivityUpcoming(a) {
    return parseApiDate(a.end_time) >= new Date();
}

function renderTopMembers(members) {
    const container = document.getElementById("top-members-list");
    if (!members || members.length === 0) {
        container.innerHTML = `<div class="empty-state"><div class="icon">🏆</div>Chưa có dữ li</div>`;
        return;
    }
    container.innerHTML = members.map((m, i) => `
        <div class="list-item">
            <div class="list-item-main">
                <div class="list-item-title">${i + 1}. ${escapeHtml(m.full_name)}</div>
                <div class="list-item-subtitle">MSSV: ${escapeHtml(m.student_id)} | Điểm danh: ${m.attendance_count} | Nhiệm vụ xong: ${m.tasks_done}</div>
            </div>
            <span class="badge badge-primary">Đi điểm: ${m.score}</span>
        </div>`).join("");
}

// ---------- Members ----------
// Danh sách thành viên: chỉ Chủ nhiệm / Trưởng ban thấy (backend + data-roles
// đã chặn). Hiển thị: Họ tên, Ngày sinh, Giới tính, Lớp, Khoa, Ngày tham gia.
// Backend trả về đúng tên trường: date_of_birth, gender, class_name, department.
function formatDob(value) {
    if (!value) return "-";
    // Backend trả "YYYY-MM-DD" (date) hoặc ISO datetime — cắt phần ngày để
    // tránh lệch múi giờ khi new Date("YYYY-MM-DD") bị parse thành UTC.
    const s = String(value).slice(0, 10); // "YYYY-MM-DD"
    const parts = s.split("-");
    if (parts.length === 3) return `${parts[2]}/${parts[1]}/${parts[0]}`;
    try {
        const d = new Date(value);
        const day = String(d.getDate()).padStart(2, "0");
        const month = String(d.getMonth() + 1).padStart(2, "0");
        return `${day}/${month}/${d.getFullYear()}`;
    } catch { return value; }
}

async function loadMembers() {
    if (!isAdminOrLeader()) return;
    const searchEl = document.getElementById("member-search");
    const search = (searchEl?.value || "").trim();
    try {
        let members = await MembersAPI.list();
        // FIX 1b: thành viên mới đăng ký phải xuất hiện ngay — re-fetch là đủ
        // vì backend tự tạo Member khi register. Log để debug map trường.
        console.log("[members] API trả về:", members?.length, members?.[0]);
        if (search) {
            members = members.filter((m) =>
                (m.full_name || "").toLowerCase().includes(search.toLowerCase()) ||
                (m.class_name || "").toLowerCase().includes(search.toLowerCase()) ||
                (m.department || "").toLowerCase().includes(search.toLowerCase()));
        }
        const tbody = document.getElementById("members-table-body");
        if (!members || members.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Chưa có thành viên nào</td></tr>`;
            return;
        }
        tbody.innerHTML = members.map((m) => `
            <tr>
                <td><strong>${escapeHtml(m.full_name)}</strong></td>
                <td>${formatDob(m.date_of_birth)}</td>
                <td>${escapeHtml(m.gender || "-")}</td>
                <td>${escapeHtml(m.class_name || "-")}</td>
                <td>${escapeHtml(m.department || "-")}</td>
                <td>${formatDate(m.joined_date)}</td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="viewMemberHistory(${m.id})">Lịch sử</button>
                    ${currentRole !== "thanh_vien" ? `<button class="btn btn-primary btn-sm" onclick="editMember(${m.id})">Sửa</button>` : ""}
                </td>
            </tr>`).join("");
        // LƯU Ý BUG "-": map đúng date_of_birth/gender/class_name/department.
        // Nếu vẫn "-", 99% là DB cũ (member tạo trước khi thêm cột → NULL).
        // Cách sửa: chạy seed lại hoặc đăng ký tài khoản mới để test.
    } catch (err) { console.error("Members error:", err); }
}

async function viewMemberHistory(memberId) {
    try {
        const data = await StatsAPI.memberParticipation(memberId);
        const activitiesHtml = data.activities.length
            ? data.activities.map((a) => `
                <div class="list-item">
                    <div class="list-item-main">
                        <div class="list-item-title">${escapeHtml(a.activity_title)}</div>
                        <div class="list-item-subtitle">${formatDate(a.start_time)} | ${a.status}</div>
                        ${a.feedback ? `<div class="list-item-subtitle">💬 ${escapeHtml(a.feedback)}</div>` : ""}
                    </div>
                    <span class="badge ${a.status === "present" ? "badge-success" : a.status === "late" ? "badge-warning" : "badge-danger"}">${a.status}</span>
                </div>`).join("")
            : `<div class="empty-state"><div class="icon">📭</div>Thành viên chưa tham gia hoạt động nào</div>`;
        const tasksHtml = data.tasks.length
            ? data.tasks.map((t) => `
                <div class="list-item">
                    <div class="list-item-main">
                        <div class="list-item-title">${escapeHtml(t.title)}</div>
                        <div class="list-item-subtitle">Ưu tiên: ${t.priority}</div>
                    </div>
                    <span class="badge ${t.status === "done" ? "badge-success" : t.status === "in_progress" ? "badge-warning" : "badge-danger"}">${t.status}</span>
                </div>`).join("")
            : "Chưa có nhiệm vụ nào";
        openModal(`Lịch sử: ${data.full_name}`,
            `<h4 style="margin-bottom:10px">📋 Hoạt động đã tham gia (${data.total_activities})</h4>
            <div class="list-container" style="margin-bottom:16px">${activitiesHtml}</div>
            <h4 style="margin-bottom:10px">✅ Nhiệm vụ</h4>
            <div class="list-container">${tasksHtml}</div>`);
    } catch (err) { showToast(err.message); }
}

async function openMemberModal(memberId = null) {
    const committees = await CommitteesAPI.list();
    const committeeOptions = committees.map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join("");
    let memberData = { full_name: "", student_id: "", email: "", phone: "", date_of_birth: "", gender: "", class_name: "", department: "", committee_id: "", skills: "", free_time: "" };
    if (memberId) {
        try { memberData = await MembersAPI.get(memberId); } catch (err) { showToast(err.message); return; }
    }
    openModal(memberId ? "✏️ Sửa thành viên" : "➕ Thêm thành viên", `
        <div class="form-group"><label>Họ và tên</label><input id="member-fullname" value="${escapeHtml(memberData.full_name)}" required></div>
        <div class="form-group"><label>Mã số sinh viên</label><input id="member-studentid" value="${escapeHtml(memberData.student_id)}" required></div>
        <div class="form-group"><label>Email</label><input type="email" id="member-email" value="${escapeHtml(memberData.email)}" required></div>
        <div class="form-group"><label>Số điện thoại</label><input id="member-phone" value="${escapeHtml(memberData.phone || "")}"></div>
        <div class="form-row-2">
            <div class="form-group"><label>Ngày sinh</label><input type="date" id="member-dob" value="${memberData.date_of_birth || ""}"></div>
            <div class="form-group"><label>Giới tính</label><select id="member-gender">
                <option value="">-- Chọn --</option>
                <option value="Nam" ${memberData.gender === "Nam" ? "selected" : ""}>Nam</option>
                <option value="Nữ" ${memberData.gender === "Nữ" ? "selected" : ""}>Nữ</option>
                <option value="Khác" ${memberData.gender === "Khác" ? "selected" : ""}>Khác</option>
            </select></div>
        </div>
        <div class="form-row-2">
            <div class="form-group"><label>Lớp</label><input id="member-class" value="${escapeHtml(memberData.class_name || "")}" placeholder="VD: CNTT-K15A"></div>
            <div class="form-group"><label>Khoa</label><input id="member-department" value="${escapeHtml(memberData.department || "")}" placeholder="VD: Công nghệ thông tin"></div>
        </div>
        <div class="form-group"><label>Ban chuyên môn</label><select id="member-committee"><option value="">-- Chưa xếp --</option>${committeeOptions}</select></div>
        <div class="form-group"><label>Kỹ năng</label><input id="member-skills" value="${escapeHtml(memberData.skills || "")}" placeholder="Truyền thông, Content, Thiết kế"></div>
        <div class="form-group"><label>Lịch rảnh (vd: T2, T4)</label><input id="member-freetime" value="${escapeHtml(memberData.free_time || "")}"></div>
        <button class="btn btn-primary btn-block" id="member-save-btn">Lưu</button>`,
        async () => {
            const data = {
                full_name: document.getElementById("member-fullname").value.trim(),
                student_id: document.getElementById("member-studentid").value.trim(),
                email: document.getElementById("member-email").value.trim(),
                phone: document.getElementById("member-phone").value.trim(),
                date_of_birth: document.getElementById("member-dob").value || null,
                gender: document.getElementById("member-gender").value || null,
                class_name: document.getElementById("member-class").value.trim() || null,
                department: document.getElementById("member-department").value.trim() || null,
                committee_id: document.getElementById("member-committee").value ? parseInt(document.getElementById("member-committee").value) : null,
                skills: document.getElementById("member-skills").value.trim(),
                free_time: document.getElementById("member-freetime").value.trim(),
            };
            try {
                if (memberId) { await MembersAPI.update(memberId, data); showToast("Cập nhật thành viên ✅"); }
                else { await MembersAPI.create(data); showToast("Thêm thành viên ✅"); }
                loadMembers(); loadAllData();
            } catch (err) { showToast(err.message); }
        });
    if (memberId && memberData.committee_id) {
        setTimeout(() => { document.getElementById("member-committee").value = memberData.committee_id; }, 0);
    }
}

function editMember(memberId) { openMemberModal(memberId); }

// ---------- Committees ----------
async function loadCommittees() {
    try {
        const committees = await CommitteesAPI.list();
        const grid = document.getElementById("committees-grid");
        if (!committees || committees.length === 0) {
            grid.innerHTML = `<div class="empty-state"><div class="icon">🏛️</div>Chưa có ban nào</div>`;
            return;
        }
        grid.innerHTML = committees.map((c) => `
            <div class="card">
                <div class="card-title">🏛️ ${escapeHtml(c.name)}</div>
                <div class="card-desc">${escapeHtml(c.description || "Chưa có mô tả")}</div>
                <div class="card-meta"><span class="badge badge-primary">${c.member_count} thành viên</span></div>
                <button class="btn btn-outline btn-sm" onclick="viewCommitteeMembers(${c.id})">Xem thành viên</button>
            </div>`).join("");
    } catch (err) { console.error("Committees error:", err); }
}

async function viewCommitteeMembers(committeeId) {
    try {
        const members = await CommitteesAPI.members(committeeId);
        const listHtml = members.length
            ? members.map((m) => `
                <div class="list-item">
                    <div class="list-item-main">
                        <div class="list-item-title">${escapeHtml(m.full_name)}</div>
                        <div class="list-item-subtitle">${escapeHtml(m.student_id)} | ${escapeHtml(m.skills || "Chưa có kỹ năng")}</div>
                    </div>
                    <span class="badge badge-primary">${escapeHtml(m.free_time) || "..."}</span>
                </div>`).join("")
            : `<div class="empty-state"><div class="icon">👥</div>Chưa có thành viên</div>`;
        openModal(`Thành viên theo ban`, `<div class="list-container">${listHtml}</div>`);
    } catch (err) { showToast(err.message); }
}

function openCommitteeModal(committeeId = null) {
    if (currentRole !== "chu_nhiem") { showToast("Chỉ chủ nhiệm mới quản lý được ban"); return; }
    openModal(committeeId ? "✏️ Sửa ban" : "➕ Thêm ban", `
        <div class="form-group"><label>Tên ban</label><input id="committee-name" required></div>
        <div class="form-group"><label>Mô tả</label><textarea id="committee-desc" rows="3"></textarea></div>
        <button class="btn btn-primary btn-block" id="committee-save-btn">Lưu</button>`,
        async () => {
            const payload = {
                name: document.getElementById("committee-name").value.trim(),
                description: document.getElementById("committee-desc").value.trim(),
                leader_id: null,
            };
            try {
                if (committeeId) { await CommitteesAPI.update(committeeId, payload); }
                else { await CommitteesAPI.create(payload); }
                loadCommittees(); showToast("Lưu ban thành công ✅");
            } catch (err) { showToast(err.message); }
        });
}

// ---------- Activities ----------
// RBAC: Chủ nhiệm + Thành viên đều fetch GET /activities (backend cho mọi role).
// Sau khi tạo/sửa/xóa: await re-fetch để danh sách cập nhật ngay, không cần F5.
async function loadActivities() {
    try {
        activitiesCache = await ActivitiesAPI.list();
        renderActivities(activitiesCache);
        // Đồng bộ luôn khu vực "Hoạt động của tôi" của Thành viên
        if (isMember()) loadMyActivities();
    } catch (err) {
        console.error("Activities error:", err);
        const container = document.getElementById("activities-list");
        if (container) container.innerHTML = `<div class="empty-state"><div class="icon">⚠️</div>Không tải được danh sách hoạt động: ${escapeHtml(err.message)}</div>`;
    }
}

function renderActivities(activities) {
    const container = document.getElementById("activities-list");
    const filter = document.getElementById("activity-filter")?.value || "";
    let list = activities || [];

    if (filter === "upcoming") {
        list = list.filter((a) => isActivityUpcoming(a));
    } else if (filter === "today") {
        const today = vietnamDateKey(new Date());
        list = list.filter((a) => vietnamDateKey(parseApiDate(a.start_time)) === today);
    } else if (filter === "mine") {
        list = list.filter((a) => a.is_registered);
    }

    // BUG FIX: mảng rỗng thì hiện thông báo thay vì màn hình trắng
    if (!list || list.length === 0) {
        const msg = filter === "mine"
            ? "Bạn chưa đăng ký hoạt động nào"
            : "Hiện chưa có hoạt động nào";
        container.innerHTML = `<div class="empty-state"><div class="icon">📅</div>${msg}</div>`;
        return;
    }

    container.innerHTML = list.map((a) => `
        <div class="list-item">
            <div class="list-item-main">
                <div class="list-item-title">${escapeHtml(a.title)}</div>
                <div class="list-item-subtitle">
                    📅 ${formatDateTime(a.start_time)} → ${formatDateTime(a.end_time)}<br>
                    📍 ${escapeHtml(a.location || "Chưa có địa điểm")}
                </div>
                <div class="card-meta" style="margin-top:8px">
                    ${registrationBadge(a)}
                    ${attendanceBadge(a)}
                    <span class="badge badge-primary">${a.registration_count} đăng ký</span>
                    <span class="badge badge-primary">${a.attendee_count} điểm danh</span>
                </div>
            </div>
            <div class="list-item-actions">
                <button class="btn btn-outline btn-sm" onclick="openActivityDetail(${a.id})">Chi tiết</button>
                ${isAdminOrLeader() ? `<button class="btn btn-primary btn-sm" onclick="editActivity(${a.id})">Sửa</button>` : ""}
                ${currentRole === "chu_nhiem" ? `<button class="btn btn-danger btn-sm" onclick="deleteActivity(${a.id})">Xóa</button>` : ""}
                ${memberActionButtons(a)}
            </div>
        </div>`).join("");
}

/**
 * Mở modal chi tiết hoạt động (yêu cầu mới).
 * A. Thông tin chung: tên, thời gian, địa điểm, mô tả + trạng thái của tôi
 *    (Chưa tham gia / Đã tham gia / trạng thái duyệt điểm danh).
 * B. 3 tab: Đã điểm danh / Đã tham gia (chưa điểm danh) / Chưa tham gia,
 *    mỗi dòng: Họ tên, Lớp, Khoa, Trạng thái (+ giờ điểm danh/đăng ký).
 */
async function openActivityDetail(activityId) {
    let act;
    let parts = null;
    try {
        act = await ActivitiesAPI.get(activityId);
        if (isAdminOrLeader() || isMember()) {
            parts = await ActivitiesAPI.participants(activityId);
        }
    } catch (err) { showToast(err.message); return; }

    // A. Trạng thái của tôi
    const status = act.my_attendance_status;
    const myStatus = ["ATTENDED", "present", "late"].includes(status)
        ? "Đã điểm danh"
        : status === "PENDING_CHECKIN" || status === "pending"
            ? "Chờ duyệt điểm danh"
            : status === "REJECTED" || status === "rejected"
                ? "Bị từ chối điểm danh"
                : act.is_registered ? "Đã tham gia" : "Chưa tham gia";
    const myBadge = status
        ? `<span class="badge ${statusBadgeClass(status)}">${escapeHtml(myStatus)}${act.my_checked_at ? ` • ${formatDateTime(act.my_checked_at)}` : ""}</span>`
        : act.is_registered
            ? `<span class="badge badge-primary">✔ Đã tham gia</span>`
            : `<span class="badge badge-muted">⏳ Chưa tham gia</span>`;

    const header = `
        <div class="detail-block">
            <p><b>📅 Thời gian:</b> ${formatDateTime(act.start_time)} → ${formatDateTime(act.end_time)}</p>
            <p><b>📍 Địa điểm:</b> ${escapeHtml(act.location || "Chưa cập nhật")}</p>
            <p><b>👥 Đăng ký:</b> ${act.registration_count} thành viên •
               <b>✅ Điểm danh:</b> ${act.attendee_count} thành viên</p>
            ${act.description ? `<p><b>📝 Mô tả:</b> ${escapeHtml(act.description)}</p>` : ""}
            ${act.notes ? `<p><b>🗒️ Ghi chú:</b> ${escapeHtml(act.notes)}</p>` : ""}
        </div>`;

    let memberBlock = "";
    if (isMember()) {
        memberBlock = `
            <div class="detail-block">
                <h4>Trạng thái của bạn: ${myBadge}</h4>
                ${act.my_reject_reason ? `<p class="form-hint">Lý do từ chối: ${escapeHtml(act.my_reject_reason)}</p>` : ""}
                <div class="detail-actions">${memberActionButtons(act)}</div>
            </div>`;
    } else {
        memberBlock = adminActivityActions(activityId, act.end_time);
    }

    // B. Danh sách trạng thái chỉ dành cho Chủ nhiệm / Trưởng ban.
    let tabs = "";
    if (parts) {
        const row = (m, statusLabel, timeLabel) => `
            <tr>
                <td><strong>${escapeHtml(m.full_name)}</strong></td>
                <td>${escapeHtml(m.class_name || "-")}</td>
                <td>${escapeHtml(m.department || "-")}</td>
                <td>${statusLabel}</td>
                <td>${timeLabel}</td>
            </tr>`;
        const attendedRows = parts.attended.length ? parts.attended.map((m) =>
            row(m, `<span class="badge badge-success">Đã điểm danh</span>`,
                m.attended_at ? formatDateTime(m.attended_at) : "-")).join("")
            : `<tr><td colspan="5" class="empty-state">Chưa có ai điểm danh</td></tr>`;
        const registeredRows = parts.registered.length ? parts.registered.map((m) => {
            const label = ["PENDING_CHECKIN", "pending"].includes(m.status)
                ? "Chờ duyệt điểm danh"
                : ["REJECTED", "rejected"].includes(m.status)
                    ? "Bị từ chối điểm danh"
                    : "Đã tham gia";
            const reason = m.reject_reason ? `<br><small>${escapeHtml(m.reject_reason)}</small>` : "";
            return row(m, `<span class="badge ${statusBadgeClass(m.status)}">${label}</span>${reason}`,
                m.checked_in_at ? formatDateTime(m.checked_in_at) : (m.registered_at ? formatDateTime(m.registered_at) : "-"));
        }).join("")
            : `<tr><td colspan="5" class="empty-state">Không còn ai chờ điểm danh 🎉</td></tr>`;
        const notJoinedRows = parts.not_joined.length ? parts.not_joined.map((m) =>
            row(m, `<span class="badge badge-muted">Chưa tham gia</span>`, "-")).join("")
            : `<tr><td colspan="5" class="empty-state">Tất cả đã tham gia 🎉</td></tr>`;

        const reviewRows = parts.registered
            .filter((m) => m.status === "PENDING_CHECKIN" && m.proof_image_url)
            .map((m) => `
                <tr>
                    <td><strong>${escapeHtml(m.full_name)}</strong></td>
                    <td>${m.checked_in_at ? formatDateTime(m.checked_in_at) : "-"}</td>
                    <td><button class="btn btn-outline btn-sm" onclick="openProofImage('${encodeURIComponent(m.proof_image_url)}')">🖼 Xem ảnh</button></td>
                    <td>
                        <button class="btn btn-primary btn-sm" onclick="verifyAttendanceRecord(${m.attendance_id},'APPROVED',${activityId})">Duyệt</button>
                        <button class="btn btn-danger btn-sm" onclick="verifyAttendanceRecord(${m.attendance_id},'REJECTED',${activityId})">Từ chối</button>
                    </td>
                </tr>`).join("");
        const reviewBlock = isAdminOrLeader() ? `
            <div class="detail-block">
                <h4>🕒 Lượt điểm danh chờ duyệt (${parts.counts.pending_approval || 0})</h4>
                <div class="table-container">
                    <table>
                        <thead><tr><th>Thành viên</th><th>Thời gian gửi</th><th>Minh chứng</th><th>Thao tác</th></tr></thead>
                        <tbody>${reviewRows || `<tr><td colspan="4" class="empty-state">Không có lượt điểm danh chờ duyệt</td></tr>`}</tbody>
                    </table>
                </div>
            </div>` : "";

        tabs = `
            <div class="detail-block">
                <h4>📋 Trạng thái thành viên (${parts.counts.total} người)</h4>
                <div class="detail-actions" style="margin-bottom:8px">
                    <button class="btn btn-primary btn-sm" onclick="switchPartTab(${activityId},'attended')">✅ Đã điểm danh (${parts.counts.attended})</button>
                    <button class="btn btn-outline btn-sm" onclick="switchPartTab(${activityId},'registered')">✔ Đã tham gia (${parts.counts.registered})</button>
                    <button class="btn btn-outline btn-sm" onclick="switchPartTab(${activityId},'not_joined')">⏳ Chưa tham gia (${parts.counts.not_joined})</button>
                </div>
                <div class="table-container">
                    <table>
                        <thead><tr><th>Họ tên</th><th>Lớp</th><th>Khoa</th><th>Trạng thái</th><th>Thời gian</th></tr></thead>
                        <tbody id="part-tab-attended">${attendedRows}</tbody>
                        <tbody id="part-tab-registered" style="display:none">${registeredRows}</tbody>
                        <tbody id="part-tab-not_joined" style="display:none">${notJoinedRows}</tbody>
                    </table>
                </div>
            </div>`;
        tabs += reviewBlock;
    }

    openModal(`📅 ${act.title}`, header + memberBlock + tabs);
    return act;
}

/** Chuyển tab trong modal Chi tiết (3 trạng thái). */
function switchPartTab(activityId, tab) {
    ["attended", "registered", "not_joined"].forEach((t) => {
        const el = document.getElementById(`part-tab-${t}`);
        if (el) el.style.display = t === tab ? "" : "none";
    });
}

async function openProofImage(encodedUrl) {
    const imageUrl = decodeURIComponent(encodedUrl);
    if (proofImageObjectUrl) URL.revokeObjectURL(proofImageObjectUrl);
    proofImageObjectUrl = null;
    openModal("Ảnh minh chứng", `
        <div class="proof-lightbox">
            <p id="proof-image-loading">Đang tải ảnh minh chứng…</p>
            <img id="proof-image-large" alt="Ảnh minh chứng điểm danh" hidden>
        </div>`);
    try {
        const response = await fetch(`${API_BASE}${imageUrl}`, {
            headers: { Authorization: `Bearer ${getToken()}` },
        });
        if (!response.ok) throw new Error(`Không tải được ảnh minh chứng (HTTP ${response.status})`);
        proofImageObjectUrl = URL.createObjectURL(await response.blob());
        const image = document.getElementById("proof-image-large");
        image.src = proofImageObjectUrl;
        image.hidden = false;
        document.getElementById("proof-image-loading").remove();
    } catch (err) {
        showToast(err.message);
    }
}

async function verifyAttendanceRecord(attendanceId, status, activityId = null) {
    const enteredReason = status === "REJECTED"
        ? prompt("Lý do từ chối (không bắt buộc):")
        : "";
    if (enteredReason === null) return;
    const rejectReason = enteredReason || "";
    try {
        await AttendanceAPI.verify(attendanceId, status, rejectReason);
        showToast(status === "APPROVED" ? "Đã duyệt điểm danh" : "Đã từ chối điểm danh");
        await loadPendingAttendance();
        const selectedActivityId = document.getElementById("attendance-activity-select")?.value;
        if (selectedActivityId) await loadAttendance();
        await refreshActivityViews();
        if (activityId && document.getElementById("modal-overlay").style.display === "flex") {
            await openActivityDetail(activityId);
        }
    } catch (err) {
        showToast(err.message);
    }
}

/** Nút quản lý hiển thị trong chi tiết hoạt động (chỉ Chủ nhiệm / Trưởng ban). */
function adminActivityActions(activityId, endTime) {
    if (!isAdminOrLeader()) return "";
    const summaryButton = parseApiDate(endTime) < new Date()
        ? `<button class="btn btn-outline btn-sm" onclick="aiSummaryForActivity(${activityId})">🤖 AI tóm tắt báo cáo</button>`
        : "";
    return `
        <div class="detail-actions">
            <button class="btn btn-primary btn-sm" onclick="openAttendeeList(${activityId})">👥 Danh sách điểm danh</button>
            <button class="btn btn-outline btn-sm" onclick="editActivity(${activityId})">✏️ Sửa hoạt động</button>
            <button class="btn btn-outline btn-sm" onclick="exportAttendeesCsv(${activityId})">⬇️ Xuất CSV</button>
            ${summaryButton}
        </div>`;
}
// ---------- Đăng ký tham gia & tự điểm danh (Thành viên) ----------
// Re-fetch ngay sau Tham gia/Điểm danh để thẻ + modal cập nhật trạng thái.
async function registerActivity(activityId) {
    try {
        const result = await ActivitiesAPI.join(activityId);
        showToast(result.message || "Đăng ký tham gia thành công ✅");
        await refreshActivityViews();
        if (isMember() && document.getElementById("page-my-activities").classList.contains("active")) {
            await loadAIActivityRecommendations();
        }
        // Nếu modal Chi tiết đang mở → mở lại để cập nhật 3 tab + nút
        if (document.getElementById("modal-overlay").style.display === "flex") {
            await openActivityDetail(activityId);
        }
    } catch (err) { showToast(err.message); }
}

async function unregisterActivity(activityId) {
    if (!confirm("Hủy đăng ký tham gia hoạt động này?")) return;
    try {
        const result = await ActivitiesAPI.unregister(activityId);
        showToast(result.message || "Đã hủy đăng ký");
        refreshActivityViews();
    } catch (err) { showToast(err.message); }
}

async function checkInActivity(activityId) {
    let selectedPhoto = null;
    let previewUrl = null;
    openModal("Điểm danh hoạt động", `
        <div class="form-group">
            <label for="checkin-photo">Ảnh minh chứng <span class="required">*</span></label>
            <input id="checkin-photo" type="file" accept="image/jpeg,image/png,image/gif,image/webp" capture="environment" required>
            <small>Chọn ảnh hoặc chụp trực tiếp; dung lượng tối đa 5 MB.</small>
            <div id="checkin-preview-container" class="proof-preview-container" hidden>
                <img id="checkin-preview" class="proof-preview" alt="Xem trước ảnh minh chứng">
            </div>
        </div>
        <div class="form-group">
            <label for="checkin-feedback">Ghi chú (không bắt buộc)</label>
            <textarea id="checkin-feedback" rows="3" placeholder="Thêm thông tin cho ban tổ chức"></textarea>
        </div>
        <button id="act-save-btn" class="btn btn-primary" disabled>📍 Xác nhận điểm danh</button>
    `, async () => {
        if (!selectedPhoto) throw new Error("Vui lòng chọn ảnh minh chứng trước khi gửi");
        const feedback = document.getElementById("checkin-feedback").value;
        await ActivitiesAPI.checkin(activityId, selectedPhoto, feedback);
        if (previewUrl) URL.revokeObjectURL(previewUrl);
        showToast("Đã gửi điểm danh, đang chờ duyệt");
        await refreshActivityViews();
    });

    const input = document.getElementById("checkin-photo");
    const submitButton = document.getElementById("act-save-btn");
    input.addEventListener("change", () => {
        if (previewUrl) URL.revokeObjectURL(previewUrl);
        selectedPhoto = input.files && input.files[0] ? input.files[0] : null;
        const allowedTypes = ["image/jpeg", "image/png", "image/gif", "image/webp"];
        const isValidPhoto = selectedPhoto &&
            allowedTypes.includes(selectedPhoto.type) &&
            selectedPhoto.size <= 5 * 1024 * 1024;
        submitButton.disabled = !isValidPhoto;
        const container = document.getElementById("checkin-preview-container");
        if (isValidPhoto) {
            previewUrl = URL.createObjectURL(selectedPhoto);
            document.getElementById("checkin-preview").src = previewUrl;
            container.hidden = false;
        } else {
            document.getElementById("checkin-preview").removeAttribute("src");
            container.hidden = true;
            if (selectedPhoto) showToast("Chọn ảnh JPEG, PNG, GIF hoặc WebP, tối đa 5 MB");
        }
    });
}

/** Tải lại các khu vực hiển thị trạng thái đăng ký / điểm danh sau khi thay đổi. */
async function refreshActivityViews() {
    const activePage = document.querySelector(".page.active")?.id || "";
    if (activePage === "page-activities") await loadActivities();
    else if (activePage === "page-my-activities") await loadMyActivities();
    else { await loadActivities(); await loadMyActivities(); }
    if (isAdminOrLeader() && activePage === "page-attendance") loadAttendance();
}

// ---------- Danh sách điểm danh (Chủ nhiệm / Trưởng ban) ----------
/**
 * Hiển thị modal "Danh sách người dùng đã điểm danh" cho một hoạt động,
 * kèm danh sách đăng ký và nút xuất báo cáo CSV.
 */
async function openAttendeeList(activityId) {
    if (!isAdminOrLeader()) { showToast("Chỉ Chủ nhiệm hoặc Trưởng ban mới xem được danh sách điểm danh"); return; }
    try {
        const [attendees, registrations, activity] = await Promise.all([
            ActivitiesAPI.attendees(activityId),
            ActivitiesAPI.registrations(activityId),
            ActivitiesAPI.get(activityId),
        ]);

        const attendeeRows = attendees.attendees.length
            ? attendees.attendees.map((r, i) => `
                <tr>
                    <td>${i + 1}</td>
                    <td><strong>${escapeHtml(r.full_name)}</strong><br><small>${escapeHtml(r.student_id || "")}</small></td>
                    <td><span class="badge ${statusBadgeClass(r.status)}">${escapeHtml(r.status_label || r.status)}</span></td>
                    <td>${escapeHtml(r.feedback || "")}</td>
                    <td>${formatDateTime(r.checked_at)}</td>
                </tr>`).join("")
            : `<tr><td colspan="5" class="empty-state">Chưa có ai điểm danh</td></tr>`;

        const pending = registrations.registrations.filter((r) => !r.checked_in);
        const pendingHtml = pending.length
            ? pending.map((r) => `<li>${escapeHtml(r.member_name)} <small>(${escapeHtml(r.student_id || "")})</small></li>`).join("")
            : "<li>Không còn ai chưa điểm danh 🎉</li>";

        openModal(`✅ ${activity.title} — Danh sách điểm danh`, `
            <div class="detail-block">
                <p><b>👥 Đăng ký:</b> ${registrations.count} thành viên •
                   <b>✅ Đã điểm danh:</b> ${attendees.count} thành viên •
                   <b>⏳ Chưa điểm danh:</b> ${pending.length} thành viên</p>
                <div class="detail-actions">
                    <button class="btn btn-outline btn-sm" onclick="exportAttendeesCsv(${activityId})">⬇️ Xuất CSV điểm danh</button>
                </div>
            </div>

            <h4 style="margin:14px 0 6px">Danh sách người dùng đã điểm danh</h4>
            <div class="table-container">
                <table>
                    <thead>
                        <tr><th>#</th><th>Thành viên</th><th>Trạng thái</th><th>Phản hồi</th><th>Thời gian điểm danh</th></tr>
                    </thead>
                    <tbody>${attendeeRows}</tbody>
                </table>
            </div>

            <h4 style="margin:16px 0 6px">Thành viên đã đăng ký nhưng chưa điểm danh</h4>
            <ul class="detail-list">${pendingHtml}</ul>
        `);
    } catch (err) { showToast(err.message); }
}

async function openActivityModal(activityId = null) {
    let act = { title: "", description: "", location: "", start_time: "", end_time: "", notes: "" };
    if (activityId) {
        try { act = await ActivitiesAPI.get(activityId); } catch (err) { showToast(err.message); return; }
    }
    let savedActivityId = activityId;
    const buildPayload = () => {
        const startVal = document.getElementById("act-start").value;
        const endVal = document.getElementById("act-end").value;
        const title = document.getElementById("act-title").value.trim();
        if (!title) throw new Error("Vui lòng nhập tên hoạt động");
        if (!startVal || !endVal) throw new Error("Vui lòng nhập thời gian bắt đầu và kết thúc");
        return {
            title,
            description: document.getElementById("act-desc").value.trim(),
            location: document.getElementById("act-location").value.trim(),
            start_time: vietnamLocalToISOString(startVal),
            end_time: vietnamLocalToISOString(endVal),
            notes: document.getElementById("act-notes").value.trim(),
        };
    };
    const persistActivity = async () => {
        const payload = buildPayload();
        if (savedActivityId) {
            await ActivitiesAPI.update(savedActivityId, payload);
        } else {
            const created = await ActivitiesAPI.create(payload);
            savedActivityId = created.id;
        }
        return savedActivityId;
    };
    openModal(activityId ? "✏️ Sửa hoạt động" : "➕ Thêm hoạt động", `
        <div class="form-group"><label>Tên hoạt động</label><input id="act-title" value="${escapeHtml(act.title)}" required></div>
        <div class="form-group"><label>Mô tả</label><textarea id="act-desc" rows="3">${escapeHtml(act.description)}</textarea></div>
        <div class="form-group"><label>Địa điểm</label><input id="act-location" value="${escapeHtml(act.location || "")}"></div>
        <div class="form-group"><label>Bắt đầu</label><input type="datetime-local" id="act-start" value="${toDatetimeLocal(act.start_time)}"></div>
        <div class="form-group"><label>Kết thúc</label><input type="datetime-local" id="act-end" value="${toDatetimeLocal(act.end_time)}"></div>
        <div class="form-group"><label>Ghi chú</label><textarea id="act-notes" rows="3">${escapeHtml(act.notes)}</textarea></div>
        <div class="detail-actions" style="margin-bottom:12px">
            <button type="button" class="btn btn-outline" id="act-ai-notification-btn">🤖 AI tạo thông báo</button>
        </div>
        <div id="act-notification-draft" class="form-group" hidden>
            <label for="act-notification-title">Tiêu đề thông báo</label>
            <input id="act-notification-title">
            <label for="act-notification-content" style="margin-top:8px">Chỉnh sửa nội dung trước khi phát hành</label>
            <textarea id="act-notification-content" rows="8"></textarea>
            <button type="button" class="btn btn-outline btn-sm" id="act-notification-publish-btn" style="margin-top:8px">📣 Phát hành thông báo</button>
        </div>
        <button class="btn btn-primary btn-block" id="act-save-btn">Lưu</button>`,
        async () => {
            await persistActivity();
            showToast(activityId ? "Cập nhật hoạt động ✅" : "Tạo hoạt động ✅");
            await loadActivities();
            loadAttendanceSelects();
            loadStatsPage();
        });

    document.getElementById("act-ai-notification-btn").addEventListener("click", async () => {
        try {
            const payload = buildPayload();
            const result = await AIAPI.notificationDraft({
                ...payload,
                start_time: formatDateTime(payload.start_time),
                end_time: formatDateTime(payload.end_time),
            });
            document.getElementById("act-notification-title").value = result.notification.title;
            document.getElementById("act-notification-content").value = result.notification.content;
            document.getElementById("act-notification-draft").hidden = false;
            showToast("Đã tạo bản nháp; hãy biên tập trước khi phát hành");
        } catch (err) { showToast(err.message); }
    });
    document.getElementById("act-notification-publish-btn").addEventListener("click", async (event) => {
        const button = event.currentTarget;
        try {
            const title = document.getElementById("act-notification-title").value.trim();
            const content = document.getElementById("act-notification-content").value.trim();
            if (!title || !content) throw new Error("Tiêu đề và nội dung thông báo không được để trống");
            button.disabled = true;
            const relatedActivityId = await persistActivity();
            await NotificationsAPI.create({
                title,
                content,
                activity_id: relatedActivityId,
                is_ai_generated: true,
            });
            button.textContent = "✅ Đã phát hành";
            showToast("Đã phát hành thông báo đến thành viên");
            await loadNotifications();
            await loadActivities();
        } catch (err) {
            button.disabled = false;
            showToast(err.message);
        }
    });
}

function editActivity(id) { openActivityModal(id); }

async function deleteActivity(id) {
    if (!confirm("Xác nhận xóa hoạt động này?")) return;
    try {
        await ActivitiesAPI.delete(id);
        showToast("Đã xóa hoạt động");
        loadActivities(); loadAllData();
    } catch (err) { showToast(err.message); }
}

// ---------- Attendance ----------
/** Tải file CSV có xác thực (dùng cho nút "Xuất CSV" trong chi tiết hoạt động). */
async function downloadCsv(url, filename) {
    const response = await fetch(url, { headers: { Authorization: `Bearer ${getToken()}` } });
    if (!response.ok) throw new Error(`Lỗi ${response.status}`);
    const blob = await response.blob();
    const link = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = link;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(link);
}

async function exportAttendeesCsv(activityId) {
    try {
        showToast("Đang tạo báo cáo CSV…");
        await downloadCsv(
            `${API_BASE}/activities/${activityId}/attendees/export`,
            `diem_danh_hoat_dong_${activityId}.csv`
        );
        showToast("Đã xuất báo cáo CSV ✅");
    } catch (err) { showToast(err.message); }
}

async function exportAttendanceReport() {
    const activityId = document.getElementById("attendance-activity-select")?.value || "";
    // Endpoint yêu cầu quyền Chủ nhiệm / Trưởng ban; gửi token qua Authorization header
    // nên dùng fetch + blob thay vì mở link trực tiếp.
    try {
        showToast("Đang tạo báo cáo CSV…");
        const response = await fetch(
            `${API_BASE}/attendance/export${activityId ? `?activity_id=${activityId}` : ""}`,
            { headers: { Authorization: `Bearer ${getToken()}` } }
        );
        if (!response.ok) throw new Error(`Lỗi ${response.status}`);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = activityId ? `bao_cao_diem_danh_hoat_dong_${activityId}.csv` : "bao_cao_diem_danh.csv";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        showToast("Đã xuất báo cáo CSV ✅");
    } catch (err) { showToast(err.message); }
}

async function loadAttendanceSelects() {
    try {
        const activities = await ActivitiesAPI.list();
        const options = activities.map((a) => `<option value="${a.id}">${escapeHtml(a.title)}</option>`).join("");
        document.getElementById("attendance-activity-select").innerHTML = `<option value="">-- Chọn hoạt động --</option>` + options;
        document.getElementById("ai-notification-activity").innerHTML = options;
        document.getElementById("ai-summary-activity").innerHTML = options;
        await loadPendingAttendance();
    } catch (err) { console.error("Attendance selects error:", err); }
}

async function loadPendingAttendance() {
    const tbody = document.getElementById("pending-attendance-body");
    if (!tbody || !isAdminOrLeader()) return;
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Đang tải lượt chờ duyệt…</td></tr>`;
    try {
        const result = await AttendanceAPI.pending();
        const records = result.attendances || [];
        tbody.innerHTML = records.length
            ? records.map((record) => `
                <tr>
                    <td>${escapeHtml(record.activity_title || `Hoạt động #${record.activity_id}`)}</td>
                    <td>${escapeHtml(record.member_name || `Thành viên #${record.member_id}`)}<br><small>${escapeHtml(record.student_id || "")}</small></td>
                    <td>${escapeHtml(record.class_name || "-")}</td>
                    <td>${escapeHtml(record.department || "-")}</td>
                    <td>${formatDateTime(record.checked_at)}</td>
                    <td><button class="btn btn-outline btn-sm" onclick="openProofImage('${encodeURIComponent(record.proof_image_url || "")}')">🖼 Xem ảnh</button></td>
                    <td>
                        <button class="btn btn-primary btn-sm" onclick="verifyAttendanceRecord(${record.id},'APPROVED',${record.activity_id})">Duyệt</button>
                        <button class="btn btn-danger btn-sm" onclick="verifyAttendanceRecord(${record.id},'REJECTED',${record.activity_id})">Từ chối</button>
                    </td>
                </tr>`).join("")
            : `<tr><td colspan="7" class="empty-state">Không có minh chứng nào đang chờ duyệt 🎉</td></tr>`;
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Không tải được danh sách: ${escapeHtml(err.message)}</td></tr>`;
        showToast(err.message);
    }
}

async function loadAttendance() {
    const activityId = document.getElementById("attendance-activity-select").value;
    if (!activityId) { showToast("Vui lòng chọn hoạt động"); return; }
    try {
        const records = await AttendanceAPI.list({ activity_id: activityId });
        const tbody = document.getElementById("attendance-table-body");
        if (!records || records.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="empty-state">Chưa có điểm danh nào</td></tr>`;
            return;
        }
        tbody.innerHTML = records.map((r) => `
            <tr>
                <td>${escapeHtml(r.member_name || `Thành viên #${r.member_id}`)}</td>
                <td>${escapeHtml(r.student_id || "-")}</td>
                <td><span class="badge ${statusBadgeClass(r.status)}">${escapeHtml(attendanceStatusLabel(r.status))}</span></td>
                <td>${escapeHtml(r.feedback || "")}</td>
                <td>${formatDateTime(r.checked_at)}</td>
            </tr>`).join("");
    } catch (err) { showToast(err.message); }
}

// ---------- Tasks ----------
async function loadTasks() {
    const status = document.getElementById("task-status-filter").value;
    try {
        let members = [];
        try { members = await MembersAPI.list(); } catch {}
        const memberMap = {};
        members.forEach((m) => (memberMap[m.id] = m.full_name));
        const tasks = await TasksAPI.list({ status: status || undefined });
        const container = document.getElementById("tasks-list");
        if (!tasks || tasks.length === 0) {
            container.innerHTML = `<div class="empty-state"><div class="icon">✅</div>Không có nhiệm vụ nào</div>`;
            return;
        }
        container.innerHTML = tasks.map((t) => `
            <div class="list-item">
                <div class="list-item-main">
                    <div class="list-item-title">${escapeHtml(t.title)}</div>
                    <div class="list-item-subtitle">
                        ${escapeHtml(t.description || "")}<br>
                        👤 ${memberMap[t.assignee_id] || "Chưa giao"}
                    </div>
                    <div class="card-meta" style="margin-top:8px">
                        <span class="badge ${t.priority === "high" ? "badge-danger" : t.priority === "medium" ? "badge-warning" : "badge-success"}">${t.priority}</span>
                        ${t.due_date ? `<span class="badge badge-primary">Hạn: ${formatDate(t.due_date)}</span>` : ""}
                        <span class="badge ${t.status === "done" ? "badge-success" : t.status === "in_progress" ? "badge-warning" : "badge-danger"}">${t.status === "done" ? "Hoàn thành" : t.status === "in_progress" ? "Đang làm" : "Cần làm"}</span>
                    </div>
                </div>
                <div class="list-item-actions">
                    ${currentRole === "thanh_vien" ? `
                        <button class="btn btn-outline btn-sm" onclick="changeTaskStatus(${t.id}, 'in_progress')">Bắt đầu</button>
                        <button class="btn btn-primary btn-sm" onclick="changeTaskStatus(${t.id}, 'done')">Xong</button>
                    ` : `
                        <button class="btn btn-primary btn-sm" onclick="editTask(${t.id})">Sửa</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteTask(${t.id})">Xóa</button>
                    `}
                </div>
            </div>`).join("");
    } catch (err) { console.error("Tasks error:", err); }
}

async function changeTaskStatus(taskId, newStatus) {
    try {
        await TasksAPI.update(taskId, { status: newStatus });
        showToast("Cập up trạng thái nhiệm vụ ✅");
        loadTasks();
    } catch (err) { showToast(err.message); }
}

async function openTaskModal(taskId = null) {
    let members = [], activities = [];
    try { members = await MembersAPI.list(); activities = await ActivitiesAPI.list(); } catch {}
    const memberOptions = members.map((m) => `<option value="${m.id}">${escapeHtml(m.full_name)}</option>`).join("");
    const activityOptions = activities.map((a) => `<option value="${a.id}">${escapeHtml(a.title)}</option>`).join("");
    let task = { title: "", description: "", activity_id: "", assignee_id: "", priority: "medium", due_date: "", status: "todo" };
    if (taskId) {
        try {
            const tasks = await TasksAPI.list();
            task = tasks.find((t) => t.id === taskId) || task;
        } catch (err) { showToast(err.message); return; }
    }
    openModal(taskId ? "✏️ Sửa nhiệm vụ" : "➕ Thêm nhiệm vụ", `
        <div class="form-group"><label>Tiêu đề</label><input id="task-title" value="${escapeHtml(task.title)}" required></div>
        <div class="form-group"><label>Mô tả</label><textarea id="task-desc" rows="3">${escapeHtml(task.description)}</textarea></div>
        <div class="form-group"><label>Hoạt động</label><select id="task-activity"><option value="">-- Chọn --</option>${activityOptions}</select></div>
        <div class="form-group"><label>Người phụ trách</label><select id="task-assignee"><option value="">-- Chọn --</option>${memberOptions}</select></div>
        <div class="form-group"><label>Ưu tiên</label><select id="task-priority"><option value="low">Thấp</option><option value="medium">Trung bình</option><option value="high">Cao</option></select></div>
        <div class="form-group"><label>Hạn chót</label><input type="datetime-local" id="task-due" value="${task.due_date ? toDatetimeLocal(task.due_date) : ""}"></div>
        <button class="btn btn-primary btn-block" id="task-save-btn">Lưu</button>`,
        async () => {
            const payload = {
                title: document.getElementById("task-title").value.trim(),
                description: document.getElementById("task-desc").value.trim(),
                activity_id: document.getElementById("task-activity").value ? parseInt(document.getElementById("task-activity").value) : null,
                assignee_id: document.getElementById("task-assignee").value ? parseInt(document.getElementById("task-assignee").value) : null,
                priority: document.getElementById("task-priority").value,
                due_date: document.getElementById("task-due").value ? vietnamLocalToISOString(document.getElementById("task-due").value) : null,
            };
            try {
                if (taskId) { await TasksAPI.update(taskId, payload); showToast("Cập up nhiệm vụ ✅"); }
                else { await TasksAPI.create(payload); showToast("Tạo nhiệm vụ ✅"); }
                loadTasks(); loadAllData();
            } catch (err) { showToast(err.message); }
        });
    setTimeout(() => {
        if (task.activity_id) document.getElementById("task-activity").value = task.activity_id;
        if (task.assignee_id) document.getElementById("task-assignee").value = task.assignee_id;
    }, 0);
}

function editTask(id) { openTaskModal(id); }

async function deleteTask(id) {
    if (!confirm("Xóa nhiệm vụ này?")) return;
    try {
        await TasksAPI.delete(id);
        showToast("Đã xóa nhiệm vụ");
        loadTasks();
    } catch (err) { showToast(err.message); }
}

// ---------- Notifications ----------
async function loadNotifications() {
    try {
        const notifications = await NotificationsAPI.list();
        const container = document.getElementById("notifications-list");
        if (!notifications || notifications.length === 0) {
            container.innerHTML = `<div class="empty-state"><div class="icon">🔔</div>Chưa có thông báo</div>`;
            return;
        }
        container.innerHTML = notifications.map((n) => `
            <div class="list-item">
                <div class="list-item-main">
                    <div class="list-item-title">${n.is_ai_generated ? "🤖 " : ""}${escapeHtml(n.title)}</div>
                    <div class="list-item-subtitle" style="white-space:pre-wrap">${escapeHtml(n.content)}</div>
                    <div class="light-text" style="font-size:12px;margin-top:6px">${formatDateTime(n.created_at)}</div>
                </div>
                <div class="list-item-actions">
                    ${n.is_ai_generated ? `<span class="badge badge-primary">AI</span>` : ""}
                    ${currentRole === "chu_nhiem" ? `<button class="btn btn-danger btn-sm" onclick="deleteNotification(${n.id})">Xóa</button>` : ""}
                </div>
            </div>`).join("");
    } catch (err) { console.error("Notifications error:", err); }
}

async function deleteNotification(id) {
    try {
        await NotificationsAPI.delete(id);
        showToast("Đã xóa thông báo");
        loadNotifications();
    } catch (err) { showToast(err.message); }
}

// ---------- AI ----------
function showAIResult(content, prompt) {
    const panel = document.getElementById("ai-result-panel");
    const resultEl = document.getElementById("ai-result-content");
    let html = `<pre>${escapeHtml(content)}</pre>`;
    if (prompt) {
        html += `<h4 style="margin-top:16px">📝 Prompt đã gửi:</h4><pre style="font-size:12px;color:var(--gray)">${escapeHtml(prompt)}</pre>`;
    }
    resultEl.innerHTML = html;
    panel.style.display = "block";
}

async function aiNotification() {
    const activityId = document.getElementById("ai-notification-activity").value;
    if (!activityId) { showToast("Vui lòng chọn hoạt động"); return; }
    try {
        const result = await AIAPI.notificationDraft(parseInt(activityId));
        openAIDraftEditor(result.notification, parseInt(activityId));
        showToast("Đã tạo bản nháp; có thể chỉnh sửa trước khi phát hành");
    } catch (err) { showToast(err.message); }
}

function openAIDraftEditor(draft, activityId) {
    openModal("📢 Chỉnh sửa bản nháp thông báo", `
        <div class="form-group">
            <label for="ai-draft-title">Tiêu đề</label>
            <input id="ai-draft-title" value="${escapeHtml(draft.title)}">
        </div>
        <div class="form-group">
            <label for="ai-draft-content">Nội dung (có thể biên tập trước khi phát hành)</label>
            <textarea id="ai-draft-content" rows="12">${escapeHtml(draft.content)}</textarea>
        </div>
        <button type="button" class="btn btn-primary" id="ai-draft-publish">📣 Phát hành thông báo</button>`);
    document.getElementById("ai-draft-publish").addEventListener("click", async (event) => {
        const button = event.currentTarget;
        const title = document.getElementById("ai-draft-title").value.trim();
        const content = document.getElementById("ai-draft-content").value.trim();
        if (!title || !content) { showToast("Tiêu đề và nội dung thông báo không được để trống"); return; }
        button.disabled = true;
        try {
            await NotificationsAPI.create({ title, content, activity_id: activityId, is_ai_generated: true });
            showToast("Đã phát hành thông báo đến thành viên");
            await loadNotifications();
            closeModal();
        } catch (err) {
            button.disabled = false;
            showToast(err.message);
        }
    });
}

async function aiSummary() {
    const activityId = document.getElementById("ai-summary-activity").value;
    if (!activityId) { showToast("Vui lòng chọn hoạt động"); return; }
    try {
        const result = await AIAPI.summary(parseInt(activityId));
        showAIResult(
            `Số đăng ký: ${result.registration_count}\nSố đã điểm danh: ${result.attendee_count}\nSố phản hồi: ${result.feedback_count}\n\n${result.summary}`,
            result.prompt
        );
        showToast("AI đã tạo tóm tắt 🤖");
    } catch (err) { showToast(err.message); }
}

async function aiSummaryForActivity(activityId) {
    try {
        const result = await AIAPI.summary(activityId);
        openModal(`📋 Báo cáo AI: ${result.activity_title}`, `
            <div class="detail-block">
                <p><b>Đăng ký:</b> ${result.registration_count} • <b>Đã điểm danh:</b> ${result.attendee_count} • <b>Phản hồi:</b> ${result.feedback_count}</p>
            </div>
            <pre class="ai-result">${escapeHtml(result.summary)}</pre>`);
    } catch (err) { showToast(err.message); }
}

// ---------- Statistics ----------
async function loadStatsPage() {
    try {
        const overview = await StatsAPI.overview();
        document.getElementById("stats-total-members").textContent = overview.total_members;
        document.getElementById("stats-total-activities").textContent = overview.total_activities;
        document.getElementById("stats-total-attendance").textContent = overview.total_attendance;
        document.getElementById("stats-task-completion").textContent =
            overview.total_tasks > 0 ? Math.round((overview.tasks_done / overview.total_tasks) * 100) + "%" : "0%";

        const cl = document.getElementById("committee-stats-list");
        if (overview.committees.length > 0) {
            cl.innerHTML = overview.committees.map((c) => `
                <div class="list-item">
                    <div class="list-item-main"><div class="list-item-title">${escapeHtml(c.name)}</div></div>
                    <span class="badge badge-primary">${c.member_count} thành viên</span>
                </div>`).join("");
        } else {
            cl.innerHTML = `<div class="empty-state"><div class="icon">🏛️</div>Chưa có dữ li</div>`;
        }

        const actStats = await StatsAPI.activities();
        const tbody = document.getElementById("stats-activities-body");
        if (actStats.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="empty-state">Chưa có dữ li hoạt động</td></tr>`;
        } else {
            tbody.innerHTML = actStats.map((a) => `
                <tr>
                    <td><strong>${escapeHtml(a.title)}</strong></td>
                    <td>${formatDate(a.start_time)}</td>
                    <td>${a.attendance_count}</td>
                    <td>${a.participation_rate}%</td>
                </tr>`).join("");
        }
    } catch (err) { console.error("Stats error:", err); }
}

// ---------- AI Chatbot widget (floating, streaming + Markdown) ----------
function toggleChatWidget(force) {
    const panel = document.getElementById("chat-panel");
    const bubble = document.getElementById("chat-bubble");
    const show = typeof force === "boolean" ? force : panel.style.display === "none";
    panel.style.display = show ? "flex" : "none";
    if (bubble) bubble.style.display = show ? "none" : "";
    if (show) loadChatSuggestions();
}

function openChatWidget() { toggleChatWidget(true); }

function initChatWidget() {
    const form = document.getElementById("chat-form");
    form?.addEventListener("submit", (e) => {
        e.preventDefault();
        const input = document.getElementById("chat-input");
        sendChatMessage(input.value);
        input.value = "";
    });
    loadChatSuggestions();
}

async function loadChatSuggestions() {
    const box = document.getElementById("chat-suggestions");
    if (!box || box.dataset.loaded) return;
    try {
        const data = await ChatAPI.suggestions();
        box.innerHTML = data.suggestions
            .map((s) => `<button type="button" class="chat-chip">${escapeHtml(s)}</button>`)
            .join("");
        box.querySelectorAll(".chat-chip").forEach((chip) => {
            chip.addEventListener("click", () => sendChatMessage(chip.textContent));
        });
        box.dataset.loaded = "1";
    } catch { /* backend offline — widget vẫn dùng được khi đăng nhập lại */ }
}

/** Render Markdown an toàn: escape HTML trước, rồi hỗ trợ **đậm**, *nghiêng*, - list. */
function renderMarkdown(text) {
    let html = escapeHtml(text || "");
    html = html
        .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
        .replace(/(^|\n)[\-•]\s+(.+)/g, "$1• $2")
        .replace(/\n/g, "<br>");
    return html;
}

function appendChatMessage(role, content, { typing = false } = {}) {
    const list = document.getElementById("chat-messages");
    const wrapper = document.createElement("div");
    wrapper.className = `chat-msg ${role === "user" ? "chat-msg-user" : "chat-msg-bot"}`;
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble-msg" + (typing ? " typing" : "");
    bubble.innerHTML = role === "user" ? escapeHtml(content) : renderMarkdown(content);
    wrapper.appendChild(bubble);
    list.appendChild(wrapper);
    list.scrollTop = list.scrollHeight;
    return bubble;
}

let chatSending = false;
async function sendChatMessage(rawText) {
    const text = (rawText || "").trim();
    if (!text || chatSending) return;
    if (!getToken()) { showToast("Vui lòng đăng nhập để dùng trợ lý AI"); return; }

    chatSending = true;
    document.getElementById("chat-send").disabled = true;
    appendChatMessage("user", text);
    const botBubble = appendChatMessage("assistant", "…", { typing: true });
    const providerEl = document.getElementById("chat-provider");
    let fullText = "";

    // Lịch sử gửi kèm cho backend (giữ tối đa 6 lượt gần nhất)
    chatHistory.push({ role: "user", content: text });
    chatHistory = chatHistory.slice(-12);

    const finish = (ok) => {
        chatSending = false;
        document.getElementById("chat-send").disabled = false;
        botBubble.classList.remove("typing");
        if (ok) {
            chatHistory.push({ role: "assistant", content: fullText });
            chatHistory = chatHistory.slice(-12);
        }
    };

    try {
        await ChatAPI.stream(
            text,
            chatHistory.slice(0, -1),
            {
                onMeta: (meta) => {
                    if (providerEl && meta.provider) {
                        providerEl.textContent = `Nguồn dữ liệu thật • ${meta.provider}`;
                    }
                },
                onDelta: (chunk) => {
                    fullText += chunk;
                    botBubble.innerHTML = renderMarkdown(fullText);
                    const list = document.getElementById("chat-messages");
                    list.scrollTop = list.scrollHeight;
                },
                onDone: () => finish(true),
                onError: async () => {
                    // Fallback: gọi API không-streaming khi SSE lỗi
                    try {
                        const result = await ChatAPI.ask(text, chatHistory.slice(0, -1));
                        fullText = result.reply || "";
                        botBubble.innerHTML = renderMarkdown(fullText);
                        if (providerEl && result.provider) {
                            providerEl.textContent = `Nguồn dữ liệu thật • ${result.provider}`;
                        }
                        finish(true);
                    } catch (err) {
                        fullText = "";
                        botBubble.textContent = err.message;
                        finish(false);
                    }
                },
            }
        );
        // Trường hợp stream kết thúc mà không bắn onDone/onError (mạng ngắt)
        if (chatSending && fullText) finish(true);
    } catch (err) {
        botBubble.textContent = err.message;
        finish(false);
    }
}

// ---------- Init ----------
function initLogout() {
    document.getElementById("btn-logout").addEventListener("click", handleLogout);
}

// ---------- Utilities ----------
function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function formatDate(dateStr) {
    if (!dateStr) return "";
    const d = parseApiDate(dateStr);
    if (isNaN(d)) return "";
    return new Intl.DateTimeFormat("vi-VN", {
        timeZone: "Asia/Ho_Chi_Minh",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
    }).format(d);
}

function formatDateTime(dateStr) {
    if (!dateStr) return "";
    const d = parseApiDate(dateStr);
    if (isNaN(d)) return "";
    const parts = new Intl.DateTimeFormat("en-GB", {
        timeZone: "Asia/Ho_Chi_Minh",
        hour: "2-digit",
        minute: "2-digit",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hourCycle: "h23",
    }).formatToParts(d);
    const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return `${values.hour}:${values.minute} ${values.day}/${values.month}/${values.year}`;
}

function vietnamDateKey(date) {
    const parts = new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Ho_Chi_Minh",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
    }).formatToParts(date);
    const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return `${values.year}-${values.month}-${values.day}`;
}

function toDatetimeLocal(dateStr) {
    if (!dateStr) return "";
    const d = parseApiDate(dateStr);
    if (isNaN(d)) return "";
    const p = (n) => String(n).padStart(2, "0");
    const vietnamTime = new Date(d.getTime() + 7 * 60 * 60 * 1000);
    return `${vietnamTime.getUTCFullYear()}-${p(vietnamTime.getUTCMonth() + 1)}-${p(vietnamTime.getUTCDate())}T${p(vietnamTime.getUTCHours())}:${p(vietnamTime.getUTCMinutes())}`;
}

function parseApiDate(dateStr) {
    if (!dateStr) return new Date(NaN);
    const value = String(dateStr);
    const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value);
    return new Date(hasTimezone ? value : `${value}Z`);
}

function vietnamLocalToISOString(value) {
    const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(value);
    if (!match) throw new Error("Thời gian hoạt động không hợp lệ");
    const [, year, month, day, hour, minute] = match.map(Number);
    return new Date(Date.UTC(year, month - 1, day, hour - 7, minute)).toISOString();
}