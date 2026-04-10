"""voice_transcriber 單元測試。

測試 Groq Whisper API 語音轉錄功能：
- 成功轉錄回傳文字
- API 錯誤 raise RuntimeError
- 缺少 API Key raise ValueError
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from kiro_agent.voice_transcriber import transcribe_voice


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_AUDIO = b"\x00\x01\x02\x03"  # 模擬音訊 bytes


# ---------------------------------------------------------------------------
# 成功轉錄
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcribe_voice_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """成功轉錄時回傳文字內容。"""
    monkeypatch.setenv("GROQ_API_KEY", "test-key-123")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"text": "你好，這是測試"}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("kiro_agent.voice_transcriber.httpx.AsyncClient", return_value=mock_client):
        result = await transcribe_voice(SAMPLE_AUDIO)

    assert result == "你好，這是測試"
    mock_client.post.assert_called_once()
    call_kwargs = mock_client.post.call_args
    assert "Bearer test-key-123" in str(call_kwargs)


# ---------------------------------------------------------------------------
# API 錯誤
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcribe_voice_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """API 回傳 HTTP 錯誤時 raise RuntimeError。"""
    monkeypatch.setenv("GROQ_API_KEY", "test-key-123")

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Rate limit exceeded"

    mock_request = MagicMock()
    http_error = httpx.HTTPStatusError(
        "rate limited",
        request=mock_request,
        response=mock_response,
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_response.raise_for_status = MagicMock(side_effect=http_error)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("kiro_agent.voice_transcriber.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(RuntimeError, match="HTTP 429"):
            await transcribe_voice(SAMPLE_AUDIO)


# ---------------------------------------------------------------------------
# 連線錯誤
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcribe_voice_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """API 連線失敗時 raise RuntimeError。"""
    monkeypatch.setenv("GROQ_API_KEY", "test-key-123")

    mock_request = MagicMock()
    conn_error = httpx.ConnectError("Connection refused", request=mock_request)

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=conn_error)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("kiro_agent.voice_transcriber.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(RuntimeError, match="連線失敗"):
            await transcribe_voice(SAMPLE_AUDIO)


# ---------------------------------------------------------------------------
# 缺少 API Key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcribe_voice_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """GROQ_API_KEY 未設定時 raise ValueError。"""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        await transcribe_voice(SAMPLE_AUDIO)


# ---------------------------------------------------------------------------
# 空白轉錄結果
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcribe_voice_empty_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """API 回傳空白文字時 raise RuntimeError。"""
    monkeypatch.setenv("GROQ_API_KEY", "test-key-123")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"text": "  "}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("kiro_agent.voice_transcriber.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(RuntimeError, match="空白轉錄結果"):
            await transcribe_voice(SAMPLE_AUDIO)
