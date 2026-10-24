"""
AI Engine for the Club Management System.

Supports multiple providers:
- OpenAI (gpt-4o-mini)
- Google Gemini
- Hugging Face
- Ollama (local)
- Built-in rule-based fallback (no API key required)

Set AI_PROVIDER and AI_API_KEY environment variables to use a real model.
If not set, the system uses a smart template/rule-based engine so the app
still works fully offline for demos and testing.
"""
import os
import json
import re
from typing import List, Dict, Any

PROVIDER = os.getenv("AI_PROVIDER", "mock").lower()  # openai / gemini / ollama / mock
API_KEY = os.getenv("AI_API_KEY", "")
BASE_URL = os.getenv("AI_BASE_URL", "")

SYSTEM_PROMPT = (
    "Bạn là trợ lý quản lý câu lạc bộ sinh viên. "
    "Viết ngắn gọn, thân thiện, không tự thêm thông tin chưa có."
)


def _call_openai(system: str, user: str) -> str:
    import httpx

    url = BASE_URL or "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": os.getenv("AI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,
    }
    resp = httpx.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_gemini(system: str, user: str) -> str:
    import httpx

    url = BASE_URL or f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    params = {"key": API_KEY}
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": user}]}],
    }
    resp = httpx.post(url, params=params, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_ollama(system: str, user: str) -> str:
    import httpx

    url = BASE_URL or "http://localhost:11434/api/chat"
    payload = {
        "model": os.getenv("AI_MODEL", "llama3.2"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }
    resp = httpx.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _call_huggingface(system: str, user: str) -> str:
    import httpx

    url = BASE_URL or "https://router.huggingface.co/hf-inference/models/mistralai/Mistral-7B-Instruct-v0.3/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": os.getenv("AI_MODEL", "mistralai/Mistral-7B-Instruct-v0.3"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 800,
    }
    resp = httpx.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def generate_text(user_prompt: str, max_tokens: int = 800, system: str = None) -> str:
    """Send a prompt to the configured AI provider. Falls back to mock if no key.

    `system` cho phép ghi đè SYSTEM_PROMPT mặc định (dùng cho AI Chatbot).
    """
    system_prompt = system or SYSTEM_PROMPT
    if PROVIDER == "openai" and API_KEY:
        return _call_openai(system_prompt, user_prompt)
    if PROVIDER == "gemini" and API_KEY:
        return _call_gemini(system_prompt, user_prompt)
    if PROVIDER == "ollama":
        try:
            return _call_ollama(system_prompt, user_prompt)
        except Exception:
            pass
    if PROVIDER == "huggingface" and API_KEY:
        return _call_huggingface(system_prompt, user_prompt)

    # ---- Mock fallback engine (rule/template-based) ----
    return _mock_generate(user_prompt)


# =========================================================
# Mock / template AI engine (works offline, deterministic)
# =========================================================

def _mock_generate(user_prompt: str) -> str:
    prompt_lower = user_prompt.lower()

    if "sinh thông báo" in prompt_lower or "thông báo hoạt động" in prompt_lower:
        return _mock_notification(user_prompt)

    if "tóm tắt" in prompt_lower or "tổng kết" in prompt_lower:
        return _mock_summary(user_prompt)

    return "Cảm ơn bạn đã gửi yêu cầu. Tôi đã nhận được thông tin và sẽ hỗ trợ bạn."


def _extract_field(text: str, label: str) -> str:
    """Extract value after 'Label:' from a structured prompt."""
    patterns = [
        rf"{label}:\s*([^\n]+)",
        rf"{label}\s*[:=-]\s*([^\n]+)",
        rf"\"{label}\":\s*\"([^\"]+)\"",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def _extract_block(text: str, label: str) -> str:
    pattern = rf"{label}:\s*\[(.*?)\]"
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""


def _clean_mock(text: str) -> str:
    return re.sub(r"\s*\|\s*", ", ", text).strip(", ")


def _mock_notification(prompt: str) -> str:
    title = _extract_field(prompt, "Tên hoạt động") or _extract_field(prompt, "Title") or "Sự kiện CLB"
    time = _extract_field(prompt, "Thời gian") or _extract_field(prompt, "Time") or "theo lịch trình"
    location = _extract_field(prompt, "Địa điểm") or _extract_field(prompt, "Location") or "tại cơ sở CLB"
    desc = _extract_field(prompt, "Mô tả") or _extract_field(prompt, "Description") or ""

    msg = (
        f"📢 THÔNG BÁO HOẠT ĐỘNG\n\n"
        f"Xin chào các bạn thành viên CLB!\n\n"
        f"Chúng ta sắp có hoạt động **{title}** diễn ra vào {time} tại {location}.\n"
    )
    if desc:
        msg += f"\nNội dung: {desc}\n"
    msg += (
        "\nRất mong các bạn sắp xếp thời gian tham gia đầy đủ và đúng giờ!\n"
        "Hãy xác nhận tham gia với trưởng ban của mình nhé.\n\n"
        "— Ban chủ nhiệm CLB"
    )
    return msg


def _mock_summary(prompt: str) -> str:
    title = _extract_field(prompt, "Tên hoạt động") or _extract_field(prompt, "Title") or "hoạt động"
    registrations = _extract_field(prompt, "Số người đăng ký") or "chưa cập nhật"
    attendees = _extract_field(prompt, "Số người đã điểm danh được duyệt") or "chưa cập nhật"
    notes_block = _extract_block(prompt, "Ghi chú") or _extract_field(prompt, "Ghi chú")
    feedback_block = _extract_block(prompt, "Phản hồi") or _extract_field(prompt, "Phản hồi")

    notes = _clean_mock(notes_block) or "Không có ghi chú chi tiết"
    feedback = _clean_mock(feedback_block)
    positive_feedback = feedback or "Chưa có phản hồi để xác định điểm tích cực"
    lower_feedback = feedback.lower()
    issue_markers = ("chậm", "thiếu", "khó", "chưa tốt", "cần cải thiện", "bất tiện", "lỗi")
    improvement = feedback if any(marker in lower_feedback for marker in issue_markers) else (
        "Chưa có vấn đề cụ thể được nêu trong phản hồi; cần thu thập thêm ý kiến"
    )

    msg = (
        f"📋 TÓM TẮT HOẠT ĐỘNG: {title}\n\n"
        f"1. Tổng quan: {registrations} thành viên đăng ký, {attendees} thành viên đã điểm danh được duyệt.\n"
        f"2. Điểm tích cực: {positive_feedback}.\n"
        f"3. Vấn đề cần cải thiện: {improvement}. Ghi chú ban tổ chức: {notes}.\n"
        f"4. Đánh giá chung: Có dữ liệu ghi chú/phản hồi để tham khảo; cần đối chiếu thêm với mục tiêu "
        f"ban đầu để kết luận đầy đủ về mức độ thành công.\n"
        f"— Bản tóm tắt tự động từ AI"
    )
    return msg


# =========================================================
# High-level AI functions used by routers
# =========================================================

def build_notification_prompt(activity_info: Dict[str, Any], role: str = "thanh_vien") -> str:
    return (
        "Sinh thông báo hoạt động cho thành viên câu lạc bộ.\n"
        f"Tên hoạt động: {activity_info.get('title', '')}\n"
        f"Mô tả: {activity_info.get('description', '')}\n"
        f"Thời gian: {activity_info.get('start_time', '')} đến {activity_info.get('end_time', '')}\n"
        f"Địa điểm: {activity_info.get('location', '')}\n"
        f"Đối tượng: {role}\n"
        "Yêu cầu: viết thông báo ngắn gọn, thân thiện, đủ thông tin."
    )


def build_summary_prompt(
    activity_info: Dict[str, Any],
    notes: str,
    feedbacks: List[str],
    attendee_count: int,
    registrations_count: int = 0,
) -> str:
    fb_text = " | ".join(feedbacks) if feedbacks else "Chưa có phản hồi"
    return (
        "Tóm tắt kết quả hoạt động từ ghi chú và phản hồi.\n"
        f"Tên hoạt động: {activity_info.get('title', '')}\n"
        f"Mô tả: {activity_info.get('description', '')}\n"
        f"Số người đăng ký: {registrations_count}\n"
        f"Số người đã điểm danh được duyệt: {attendee_count}\n"
        f"Ghi chú: [{notes}]\n"
        f"Phản hồi: [{fb_text}]\n"
        "Yêu cầu: trình bày rõ 4 mục: tổng quan (nêu số đăng ký và số đã điểm danh), "
        "điểm tích cực, vấn đề cần cải thiện, đánh giá chung mức độ thành công. "
        "Chỉ kết luận dựa trên dữ liệu được cung cấp; nêu rõ khi thiếu dữ liệu."
    )
