"""Engine cho AI Chatbot hỏi đáp về hoạt động CLB.

- `build_prompt` ghép câu hỏi + context (RAG) + lịch sử hội thoại thành prompt.
- `answer` gọi AI provider đã cấu hình, nếu chưa có thì dùng engine mock
  offline (`mock_answer`) trả lời trực tiếp từ context -> demo không cần API key.
- `stream_answer` phát câu trả lời theo từng đoạn (streaming) cho widget chat.
"""
import json
import re
from typing import Any, Dict, Generator, List, Optional

from . import ai_service

CHAT_SYSTEM_PROMPT = (
    "Bạn là trợ lý AI của câu lạc bộ sinh viên. "
    "Chỉ trả lời dựa trên DỮ LIỆU CÂU LẠC BỘ được cung cấp trong phần NGỮ CẢNH. "
    "Tuyệt đối không bịa thêm hoạt động, thời gian hay địa điểm không có trong dữ liệu. "
    "Nếu dữ liệu không có thông tin, hãy nói rõ là chưa có thông tin và gợi ý liên hệ ban chủ nhiệm. "
    "Trả lời bằng tiếng Việt, ngắn gọn, thân thiện, định dạng Markdown "
    "(dùng dấu gạch đầu dòng, in đậm cho tên hoạt động và thời gian)."
)

MAX_HISTORY_TURNS = 6


def _brief_line(item: Dict[str, Any]) -> str:
    return (
        f"- **{item['title']}** | {item['start_text']} → {item['end_text']} | "
        f"📍 {item['location']} | Đăng ký: {item['registration_count']}, "
        f"Điểm danh: {item['attendee_count']}"
    )


def context_to_text(context: Dict[str, Any]) -> str:
    """Chuyển context (dict) thành khối văn bản dễ đọc cho AI."""
    lines: List[str] = []
    user = context.get("user", {})

    lines.append(f"THỜI ĐIỂM HIỆN TẠI: {context.get('now_text')}")
    lines.append(
        f"NGƯỜI DÙNG: {user.get('member_name') or user.get('username')} "
        f"— vai trò: {user.get('role_label')}"
        + (f", ban: {user.get('committee_name')}" if user.get("committee_name") else "")
    )

    def _section(title: str, items: List[Dict[str, Any]]) -> None:
        lines.append("")
        lines.append(f"{title} ({len(items)}):")
        if not items:
            lines.append("- (không có)")
        for item in items:
            lines.append(_brief_line(item))

    _section("HOẠT ĐỘNG HÔM NAY", context.get("today", []))
    _section("HOẠT ĐỘNG TRONG 7 NGÀY TỚI", context.get("this_week", []))
    _section("HOẠT ĐỘNG SẮP DIỄN RA", context.get("upcoming", []))
    _section("HOẠT ĐỘNG ĐÃ KẾT THÚC GẦN ĐÂY", context.get("recent", []))
    if context.get("matched_activities"):
        _section("HOẠT ĐỘNG KHỚP VỚI CÂU HỎI", context["matched_activities"])

    lines.append("")
    lines.append("ĐĂNG KÝ THAM GIA CỦA NGƯỜI DÙNG:")
    registrations = context.get("my_registrations", [])
    if not registrations:
        lines.append("- (chưa đăng ký hoạt động nào)")
    for reg in registrations:
        if reg.get("attendance_status") in {"PENDING_CHECKIN", "pending"}:
            attendance_state = "đã gửi minh chứng, chờ duyệt"
        elif reg.get("attendance_status") in {"REJECTED", "rejected"}:
            attendance_state = "minh chứng bị từ chối, cần gửi lại"
        else:
            attendance_state = "đã điểm danh" if reg["checked_in"] else "chưa điểm danh"
        lines.append(
            f"- {reg['activity_title']} | {reg['start_text']} | "
            f"điểm danh: {attendance_state}"
        )

    lines.append("")
    lines.append("LỊCH SỬ ĐIỂM DANH CỦA NGƯỜI DÙNG:")
    attendances = context.get("my_attendances", [])
    if not attendances:
        lines.append("- (chưa điểm danh hoạt động nào)")
    for row in attendances:
        lines.append(
            f"- {row['activity_title']} | {row.get('start_text', '')} | "
            f"trạng thái: {row.get('status_label', row['status'])}"
        )

    lines.append("")
    lines.append("NHIỆM VỤ ĐƯỢC GIAO CỦA NGƯỜI DÙNG:")
    tasks = context.get("my_tasks", [])
    if not tasks:
        lines.append("- (không có nhiệm vụ)")
    for task in tasks:
        lines.append(f"- {task['title']} | trạng thái: {task['status']}")

    lines.append("")
    lines.append(f"TỔNG SỐ HOẠT ĐỘNG TRONG HỆ THỐNG: {context.get('total_activities', 0)}")
    return "\n".join(lines)


def build_prompt(question: str, context: Dict[str, Any], history: Optional[List[Dict]] = None) -> str:
    """Ghép lịch sử hội thoại + context + câu hỏi thành prompt hoàn chỉnh."""
    parts: List[str] = []

    if history:
        recent = history[-MAX_HISTORY_TURNS:]
        transcript = []
        for message in recent:
            role = "Người dùng" if message.get("role") == "user" else "Trợ lý"
            content = (message.get("content") or "").strip()
            if content:
                transcript.append(f"{role}: {content}")
        if transcript:
            parts.append("HỘI THOẠI TRƯỚC ĐÓ:\n" + "\n".join(transcript))

    parts.append("NGỮ CẢNH (DỮ LIỆU THẬT TỪ DATABASE):\n" + context_to_text(context))
    parts.append(f"CÂU HỎI CỦA NGƯỜI DÙNG: {question}")
    parts.append(
        "YÊU CẦU: trả lời trực tiếp câu hỏi bằng tiếng Việt, chỉ dùng dữ liệu ở trên, "
        "định dạng Markdown, ngắn gọn và thân thiện."
    )
    return "\n\n".join(parts)


# =========================================================
# Engine mock (offline) — trả lời trực tiếp từ context, không cần API key
# =========================================================

def _norm(text: str) -> str:
    from .context_builder import _normalize

    return _normalize(text)


def _as_mentioned(item: Dict[str, Any]) -> Dict[str, Any]:
    """Chuẩn hoá item thành dict có cả `title` và `activity_title`.

    `matched_activities` (từ context builder) dùng key `title`, còn
    `my_registrations` dùng key `activity_title` — hàm này hợp nhất hai dạng.
    """
    normalized = dict(item)
    title = normalized.get("title") or normalized.get("activity_title") or ""
    normalized["title"] = title
    normalized["activity_title"] = title
    normalized.setdefault("location", normalized.get("location") or "chưa cập nhật")
    normalized.setdefault("registration_count", 0)
    normalized.setdefault("attendee_count", 0)
    normalized.setdefault("check_in_window", "")
    return normalized


def _find_mentioned(context: Dict[str, Any], question: str) -> Optional[Dict[str, Any]]:
    """Tìm hoạt động được nhắc tới trong câu hỏi."""
    matched = context.get("matched_activities") or []
    if matched:
        return _as_mentioned(matched[0])
    norm_q = _norm(question)
    for reg in context.get("my_registrations", []):
        title = _norm(reg.get("activity_title", ""))
        if title and title[:12] in norm_q:
            return _as_mentioned(reg)
    return None


def _search_my_attendance(context: Dict[str, Any], question: str) -> Optional[Dict[str, Any]]:
    """Tìm bản ghi điểm danh của người dùng khớp với câu hỏi."""
    norm_q = _norm(question)
    for row in context.get("my_attendances", []):
        title = _norm(row.get("activity_title", ""))
        if title and (title in norm_q or title[:12] in norm_q):
            return row
    return None


def _activity_detail(item: Dict[str, Any]) -> str:
    lines = [
        f"### 📅 {item.get('title', '')}",
        "",
        f"- **Thời gian:** {item.get('start_text', '')} → {item.get('end_text', '')}",
        f"- **Địa điểm:** 📍 {item.get('location', 'chưa cập nhật')}",
        f"- **Đăng ký:** {item.get('registration_count', 0)} thành viên | "
        f"**Đã điểm danh:** {item.get('attendee_count', 0)}",
    ]
    if item.get("description"):
        lines.append(f"- **Mô tả:** {item['description']}")
    return "\n".join(lines)


def _list_block(title: str, items: List[Dict[str, Any]]) -> str:
    if not items:
        return f"**{title}:** hiện chưa có hoạt động nào."
    body = "\n".join(_brief_line(item) for item in items)
    return f"**{title}:**\n\n{body}"


def _mock_attendance_reply(question, context, mentioned, display_name) -> str:
    if mentioned and mentioned.get("activity_title"):
        title = mentioned["activity_title"]
        row = _search_my_attendance(context, title)
        if row:
            if row["status"] in {"PENDING_CHECKIN", "pending"}:
                return (
                    f"⏳ **{display_name} đã gửi ảnh minh chứng** cho hoạt động "
                    f"**{row['activity_title']}** và đang **chờ duyệt điểm danh**."
                )
            if row["status"] in {"REJECTED", "rejected"}:
                return (
                    f"⚠️ Minh chứng điểm danh hoạt động **{row['activity_title']}** "
                    f"đã bị từ chối. Bạn cần tải ảnh mới và điểm danh lại."
                )
            if row["status"] not in {"ATTENDED", "present", "late"}:
                return (
                    f"📋 Hoạt động **{row['activity_title']}** có trạng thái điểm danh: "
                    f"**{row.get('status_label', row['status'])}**."
                )
            return (
                f"✅ **{display_name} đã điểm danh** hoạt động **{row['activity_title']}**.\n\n"
                f"- Trạng thái: **{row.get('status_label', row['status'])}**\n"
                f"- Thời gian điểm danh: {row.get('checked_at') or 'không rõ'}"
            )
        registration = next(
            (
                r
                for r in context.get("my_registrations", [])
                if _norm(r["activity_title"]) == _norm(title)
            ),
            None,
        )
        if registration:
            return (
                f"⏳ **{display_name} chưa điểm danh** hoạt động **{title}**.\n\n"
                "- Bạn **đã đăng ký** tham gia hoạt động này.\n"
                "- Hãy bấm nút **Điểm danh** trong chi tiết hoạt động khi sự kiện diễn ra."
            )
        return (
            f"ℹ️ Bạn **chưa đăng ký** hoạt động **{title}**, nên chưa có bản ghi điểm danh nào.\n\n"
            "Hãy vào chi tiết hoạt động và bấm **Đăng ký tham gia** trước nhé."
        )

    rows = context.get("my_attendances", [])
    if not rows:
        return (
            f"ℹ️ Hiện **{display_name} chưa điểm danh** hoạt động nào.\n\n"
            "Bạn hãy đăng ký tham gia hoạt động rồi điểm danh khi sự kiện diễn ra."
        )
    body = "\n".join(
        f"- **{r['activity_title']}** — trạng thái: `{r.get('status_label', r['status'])}`" for r in rows[:8]
    )
    return f"📋 **Lịch sử điểm danh của {display_name}:**\n\n{body}"


def mock_answer(question: str, context: Dict[str, Any]) -> str:
    """Trợ lý offline: trả lời hoàn toàn dựa trên context (RAG) lấy từ DB."""
    norm_q = _norm(question)
    user = context.get("user", {})
    display_name = user.get("member_name") or user.get("username") or "bạn"

    wants_attendance = any(k in norm_q for k in ["diem danh", "check in", "checkin"])
    wants_registration = "dang ky" in norm_q
    wants_tasks = "nhiem vu" in norm_q
    wants_today = "hom nay" in norm_q or "toi nay" in norm_q
    wants_week = "tuan" in norm_q
    wants_location = any(
        k in norm_q for k in ["o dau", "dia diem", "may gio", "khi nao", "thoi gian"]
    )
    mentioned = _find_mentioned(context, question)

    # 1) Hỏi về điểm danh của chính mình
    if wants_attendance:
        return _mock_attendance_reply(question, context, mentioned, display_name)

    # 2) Hỏi về đăng ký
    if wants_registration:
        regs = context.get("my_registrations", [])
        if not regs:
            return (
                f"ℹ️ **{display_name} chưa đăng ký** hoạt động nào.\n\n"
                "Xem danh sách hoạt động ở trang **Hoạt động** và bấm **Đăng ký tham gia** nhé."
            )
        body = "\n".join(
            f"- **{r['activity_title']}** | {r['start_text']} | "
            f"{'đã điểm danh ✅' if r['checked_in'] else 'chưa điểm danh'}"
            for r in regs
        )
        return f"📝 **Hoạt động {display_name} đã đăng ký:**\n\n{body}"

    # 3) Hỏi nhiệm vụ
    if wants_tasks:
        tasks = context.get("my_tasks", [])
        if not tasks:
            return f"ℹ️ Hiện **{display_name} chưa có nhiệm vụ** nào được giao."
        body = "\n".join(
            f"- **{t['title']}** — `{t['status']}` (ưu tiên: {t['priority']})" for t in tasks
        )
        return f"✅ **Nhiệm vụ của {display_name}:**\n\n{body}"

    # 4) Hỏi chi tiết một hoạt động cụ thể
    if mentioned and mentioned.get("activity_title") and (
        wants_location or "title" not in mentioned
    ):
        if wants_location or not context.get("today"):
            return "Đây là thông tin chi tiết hoạt động bạn hỏi:\n\n" + _activity_detail(mentioned)

    # 5) Hôm nay có hoạt động nào?
    if wants_today:
        return (
            f"📆 **Hoạt động hôm nay ({context.get('today_text')})**\n\n"
            + _list_block("Danh sách", context.get("today", []))
        )

    # 6) Tuần này có sự kiện gì?
    if wants_week:
        return (
            "🗓️ **Hoạt động trong 7 ngày tới**\n\n"
            + _list_block("Hôm nay", context.get("today", []))
            + "\n\n"
            + _list_block("Các ngày tiếp theo", context.get("this_week", []))
        )

    # 7) Hỏi chung về địa điểm / thời gian
    if wants_location:
        upcoming = context.get("upcoming", [])
        if not upcoming:
            return "ℹ️ Hiện chưa có hoạt động nào sắp diễn ra."
        return (
            "📍 **Thời gian & địa điểm các hoạt động sắp diễn ra:**\n\n"
            + "\n".join(
                f"- **{item['title']}** — {item['start_text']} tại 📍 {item['location']}"
                for item in upcoming[:5]
            )
        )

    # 8) Mặc định: tổng quan
    today = context.get("today", [])
    upcoming = context.get("upcoming", [])
    lines = [f"Xin chào **{display_name}** 👋", ""]
    if today:
        lines.append(_list_block("Hoạt động hôm nay", today))
    else:
        lines.append(
            f"Hôm nay ({context.get('today_text')}) chưa có hoạt động nào được lên lịch."
        )
    if upcoming:
        lines.append("")
        lines.append(_list_block("Hoạt động sắp diễn ra", upcoming[:5]))
    lines.append("")
    lines.append(
        "Bạn có thể hỏi mình: *Hôm nay có hoạt động nào?*, *Tuần này có sự kiện gì?*, "
        "*Hoạt động X diễn ra ở đâu, mấy giờ?*, *Tôi đã điểm danh hoạt động Y chưa?*"
    )
    return "\n".join(lines)


# =========================================================
# API cấp cao cho router
# =========================================================

def _configured_provider() -> bool:
    provider = ai_service.PROVIDER
    if provider == "mock":
        return False
    if provider == "ollama":
        return True
    return bool(ai_service.API_KEY)


def answer(question: str, context: Dict[str, Any], history: Optional[List[Dict]] = None) -> str:
    """Trả lời câu hỏi: dùng AI provider nếu đã cấu hình, ngược lại dùng mock."""
    if not _configured_provider():
        return mock_answer(question, context)

    prompt = build_prompt(question, context, history)
    try:
        text = ai_service.generate_text(prompt, system=CHAT_SYSTEM_PROMPT)
        if text and text.strip():
            return text.strip()
    except Exception:
        pass
    # Fallback: provider lỗi thì vẫn trả lời được nhờ engine offline
    return mock_answer(question, context)


def stream_answer(
    question: str,
    context: Dict[str, Any],
    history: Optional[List[Dict]] = None,
    chunk_size: int = 16,
) -> Generator[str, None, None]:
    """Phát câu trả lời theo từng đoạn nhỏ (streaming) cho widget chat.

    Với provider thật, đây là mô phỏng streaming ở tầng ứng dụng (chia nhỏ văn
    bản đã sinh); frontend vẫn nhận được hiệu ứng gõ chữ từng bước.
    """
    text = answer(question, context, history)

    buffer = ""
    for piece in re.split(r"(\s+)", text):
        buffer += piece
        while len(buffer) >= chunk_size:
            yield buffer[:chunk_size]
            buffer = buffer[chunk_size:]
    if buffer:
        yield buffer


SUGGESTIONS = [
    "Hôm nay có các hoạt động nào?",
    "Tuần này có sự kiện gì không?",
    "Tôi đã điểm danh hoạt động nào rồi?",
    "Tôi đã đăng ký hoạt động nào?",
    "Các hoạt động sắp diễn ra ở đâu, mấy giờ?",
    "Tôi có nhiệm vụ gì cần làm?",
]