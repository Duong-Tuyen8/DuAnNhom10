"""API route cho AI Chatbot: `/api/chat`.

Luồng xử lý (RAG):
1. Nhận câu hỏi của người dùng + JWT.
2. `context_builder.build_context` truy vấn DB lấy danh sách hoạt động thực tế
   (hôm nay / tuần này / sắp diễn ra / đã kết thúc) và trạng thái của chính
   người dùng (đăng ký, điểm danh, nhiệm vụ).
3. `chat_service.answer` / `stream_answer` truyền context vào prompt cho AI.
4. Trả về câu trả lời (Markdown) hoặc stream qua SSE.
"""
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..ai import chat_service
from ..ai.context_builder import build_context
from ..database import get_db
from ..models import User
from ..schemas import ChatRequest, ChatResponse
from ..security import get_current_user

router = APIRouter(prefix="/api/chat", tags=["chatbot"])


@router.get("/suggestions")
def chat_suggestions():
    """Câu hỏi gợi ý hiển thị trong widget chat."""
    return {"suggestions": chat_service.SUGGESTIONS}


@router.get("/context")
def chat_context_preview(
    question: str = "Hôm nay có các hoạt động nào?",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xem trước dữ liệu (RAG) mà chatbot sẽ dùng để trả lời — hữu ích khi debug/demo."""
    context = build_context(db, current_user, question)
    return {
        "question": question,
        "provider": chat_service.ai_service.PROVIDER,
        "context": context,
    }


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hỏi đáp với trợ lý AI (trả về một lần, không streaming)."""
    question = (payload.message or "").strip()
    if not question:
        return ChatResponse(
            reply="Bạn hãy nhập câu hỏi nhé, ví dụ: _Hôm nay có hoạt động nào?_",
            provider=chat_service.ai_service.PROVIDER,
            context=None,
        )

    context = build_context(db, current_user, question)
    history = [msg.model_dump() for msg in payload.history] if payload.history else []
    reply = chat_service.answer(question, context, history)

    return ChatResponse(
        reply=reply,
        provider=chat_service.ai_service.PROVIDER,
        context={
            "today_count": len(context.get("today", [])),
            "week_count": len(context.get("this_week", [])),
            "upcoming_count": len(context.get("upcoming", [])),
            "matched_count": len(context.get("matched_activities", [])),
            "my_registrations": len(context.get("my_registrations", [])),
            "my_attendances": len(context.get("my_attendances", [])),
        },
    )


@router.post("/stream")
def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hỏi đáp với trợ lý AI, trả về theo dạng Server-Sent Events (streaming)."""
    question = (payload.message or "").strip()
    history = [msg.model_dump() for msg in payload.history] if payload.history else []
    context = build_context(db, current_user, question)

    def event_generator():
        meta = {
            "type": "meta",
            "provider": chat_service.ai_service.PROVIDER,
            "context": {
                "today_count": len(context.get("today", [])),
                "week_count": len(context.get("this_week", [])),
                "upcoming_count": len(context.get("upcoming", [])),
                "matched_count": len(context.get("matched_activities", [])),
            },
        }
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"

        try:
            for chunk in chat_service.stream_answer(question, context, history):
                yield f"data: {json.dumps({'type': 'delta', 'text': chunk}, ensure_ascii=False)}\n\n"
        except Exception as exc:  # pragma: no cover - phòng ngừa lỗi runtime
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )