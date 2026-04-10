"""語音轉錄模組 — 透過 Groq Whisper API 將語音轉為文字。

使用 httpx 非同步呼叫 Groq Whisper API（whisper-large-v3），
將音訊 bytes 轉錄為文字。API Key 從環境變數 GROQ_API_KEY 讀取。
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3"


async def transcribe_voice(audio_bytes: bytes) -> str:
    """透過 Groq Whisper API 轉錄語音，回傳文字。

    Parameters
    ----------
    audio_bytes:
        音訊檔案的原始 bytes（支援 ogg/mp3/wav 等格式）。

    Returns
    -------
    str
        轉錄後的文字內容。

    Raises
    ------
    ValueError
        若環境變數 ``GROQ_API_KEY`` 未設定。
    RuntimeError
        若 Groq API 呼叫失敗（HTTP 錯誤或回應格式異常）。
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY 環境變數未設定，無法進行語音轉錄"
        )

    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"file": ("voice.ogg", audio_bytes, "audio/ogg")}
    data = {"model": GROQ_MODEL}

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                GROQ_API_URL,
                headers=headers,
                files=files,
                data=data,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Groq Whisper API 回傳錯誤: %d %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise RuntimeError(
                f"Groq Whisper API 錯誤 (HTTP {exc.response.status_code}): "
                f"{exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Groq Whisper API 連線失敗: %s", exc)
            raise RuntimeError(
                f"Groq Whisper API 連線失敗: {exc}"
            ) from exc

    result = response.json()
    text = result.get("text", "").strip()
    if not text:
        raise RuntimeError(
            "Groq Whisper API 回傳空白轉錄結果"
        )
    return text
