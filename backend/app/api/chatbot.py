from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.api.predict import validate_and_save
from app.config import get_settings
from app.services.chatbot_service import (
    build_context,
    clear_conversation,
    latest_conversation_id,
    list_history,
    save_message,
)
from app.services.nutrition_ai import new_conversation_id, nutrition_ai_service
from app.services.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(default="", max_length=2000)
    conversationId: str | None = Field(default=None, max_length=36)


def _ensure_rate_limit(user_id: int) -> None:
    settings = get_settings()
    if not check_rate_limit(user_id, settings.chat_rate_limit_per_minute):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many chat requests. Please wait a moment and try again.",
        )


def _conversation_id(raw: str | None) -> str:
    value = (raw or "").strip()
    if not value:
        return new_conversation_id()
    try:
        uuid.UUID(value)
    except ValueError:
        if value.startswith("legacy-"):
            return value
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conversation id.")
    return value


def _run_chat(user: dict, message: str, conversation_id: str, image_path: Path | None) -> dict:
    text = (message or "").strip()
    if not text and image_path is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Send a message or a food photo.")
    if len(text) > 2000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message is too long.")

    food_context = None
    if image_path is not None:
        try:
            food_context = nutrition_ai_service.classify_food_image(image_path)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Food analysis failed. Please try another image.",
            ) from exc
        if not text:
            text = f"What can you tell me about this {food_context.get('display_name') or 'food'}?"

    display_user = text
    if food_context:
        display_user = f"{text}\n\n[Photo classified as {food_context['display_name']} · {food_context['confidence']:.0f}% confidence]"

    history = list_history(user["user_id"], limit=get_settings().ai_max_history_turns * 2, conversation_id=conversation_id)
    save_message(user["user_id"], "user", display_user, conversation_id)
    context = build_context(user)
    try:
        reply = nutrition_ai_service.generateNutritionResponse(text, context, history, food_context)
    except Exception:
        reply = "The nutrition assistant is unavailable right now. Please try again."
    saved = save_message(user["user_id"], "assistant", reply, conversation_id)
    return {
        "response": reply,
        "conversationId": conversation_id,
        "role": "assistant",
        "content": reply,
        "message_id": saved["message_id"],
        "food": food_context,
        "provider": None,
    }


@router.post("")
async def chat(request: Request, user: dict = Depends(get_current_user)):
    _ensure_rate_limit(user["user_id"])
    content_type = (request.headers.get("content-type") or "").lower()

    if "multipart/form-data" in content_type:
        form = await request.form()
        message = str(form.get("message") or form.get("query") or "")
        conversation_id = _conversation_id(str(form.get("conversationId") or "") or None)
        upload = form.get("image") or form.get("file")
        image_path = None
        if upload is not None and hasattr(upload, "filename") and getattr(upload, "filename"):
            image_path = validate_and_save(upload)  # type: ignore[arg-type]
        result = _run_chat(user, message, conversation_id, image_path)
        from app.ai.factory import get_nutrition_provider

        result["provider"] = get_nutrition_provider().name
        return result

    try:
        payload = ChatRequest.model_validate(await request.json())
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chat request.") from exc
    conversation_id = _conversation_id(payload.conversationId)
    result = _run_chat(user, payload.message, conversation_id, None)
    from app.ai.factory import get_nutrition_provider

    result["provider"] = get_nutrition_provider().name
    return result


@router.post("/stream")
async def chat_stream(request: Request, user: dict = Depends(get_current_user)):
    _ensure_rate_limit(user["user_id"])
    try:
        payload = ChatRequest.model_validate(await request.json())
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chat request.") from exc

    text = (payload.message or "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Send a message.")
    conversation_id = _conversation_id(payload.conversationId)
    history = list_history(
        user["user_id"],
        limit=get_settings().ai_max_history_turns * 2,
        conversation_id=conversation_id,
    )
    save_message(user["user_id"], "user", text, conversation_id)
    context = build_context(user)

    def event_stream():
        collected: list[str] = []
        try:
            for chunk in nutrition_ai_service.streamNutritionResponse(text, context, history):
                collected.append(chunk)
                yield f"data: {json.dumps({'token': chunk, 'conversationId': conversation_id})}\n\n"
            reply = "".join(collected)
            saved = save_message(user["user_id"], "assistant", reply, conversation_id)
            yield f"data: {json.dumps({'done': True, 'conversationId': conversation_id, 'message_id': saved['message_id'], 'response': reply})}\n\n"
        except Exception:
            fallback = "The nutrition assistant is unavailable right now. Please try again."
            save_message(user["user_id"], "assistant", fallback, conversation_id)
            yield f"data: {json.dumps({'error': fallback, 'conversationId': conversation_id, 'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/history")
def chat_history(
    limit: int = Query(default=40, ge=1, le=100),
    conversationId: str | None = None,
    user: dict = Depends(get_current_user),
):
    cid = conversationId or latest_conversation_id(user["user_id"])
    rows = list_history(user["user_id"], limit=limit, conversation_id=cid)
    return {"conversationId": cid, "messages": rows}


@router.delete("")
def delete_conversation(conversationId: str = Query(...), user: dict = Depends(get_current_user)):
    clear_conversation(user["user_id"], conversationId)
    return {"ok": True, "conversationId": conversationId}
