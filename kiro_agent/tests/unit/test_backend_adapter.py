"""BackendAdapter 抽象層單元測試。"""

from __future__ import annotations

import pytest

from kiro_agent.backend_adapter import (
    BACKEND_REGISTRY,
    BackendAdapter,
    ClaudeCodeAdapter,
    CodexAdapter,
    GeminiCliAdapter,
    KiroCliAdapter,
    OpenCodeAdapter,
    TmuxBackendAdapter,
    get_adapter,
)
from kiro_agent.models import BackendError


class TestGetAdapter:
    """get_adapter() 工廠函式測試。"""

    def test_get_kiro_cli_adapter(self) -> None:
        adapter = get_adapter("kiro-cli")
        assert isinstance(adapter, KiroCliAdapter)
        assert isinstance(adapter, BackendAdapter)

    def test_get_claude_code_adapter(self) -> None:
        adapter = get_adapter("claude-code")
        assert isinstance(adapter, ClaudeCodeAdapter)

    def test_get_gemini_cli_adapter(self) -> None:
        adapter = get_adapter("gemini-cli")
        assert isinstance(adapter, GeminiCliAdapter)

    def test_get_codex_adapter(self) -> None:
        adapter = get_adapter("codex")
        assert isinstance(adapter, CodexAdapter)

    def test_get_opencode_adapter(self) -> None:
        adapter = get_adapter("opencode")
        assert isinstance(adapter, OpenCodeAdapter)

    def test_nonexistent_backend_raises_backend_error(self) -> None:
        with pytest.raises(BackendError) as exc_info:
            get_adapter("nonexistent")
        err = exc_info.value
        assert err.backend == "nonexistent"
        assert err.error_type == "not_found"
        # 錯誤訊息應包含可用的後端清單
        for name in BACKEND_REGISTRY:
            assert name in str(err)

    def test_empty_name_raises_backend_error(self) -> None:
        with pytest.raises(BackendError):
            get_adapter("")


class TestBackendRegistry:
    """BACKEND_REGISTRY 完整性測試。"""

    def test_registry_contains_all_expected_backends(self) -> None:
        expected = {"kiro-cli", "claude-code", "gemini-cli", "codex", "opencode"}
        assert set(BACKEND_REGISTRY.keys()) == expected

    def test_all_registered_backends_can_be_instantiated(self) -> None:
        for name, cls in BACKEND_REGISTRY.items():
            adapter = get_adapter(name)
            assert isinstance(adapter, cls), f"{name} 應為 {cls.__name__} 實例"
            assert isinstance(adapter, BackendAdapter), f"{name} 應繼承 BackendAdapter"

    def test_registry_values_are_backend_adapter_subclasses(self) -> None:
        for name, cls in BACKEND_REGISTRY.items():
            assert issubclass(cls, BackendAdapter), f"{cls.__name__} 應為 BackendAdapter 子類別"


class TestTmuxBackendAdapterInheritance:
    """驗證所有 Adapter 皆繼承 TmuxBackendAdapter。"""

    def test_all_adapters_inherit_tmux_base(self) -> None:
        for cls in [KiroCliAdapter, ClaudeCodeAdapter, GeminiCliAdapter, CodexAdapter, OpenCodeAdapter]:
            assert issubclass(cls, TmuxBackendAdapter), (
                f"{cls.__name__} 應繼承 TmuxBackendAdapter"
            )


class TestAdapterCliCommands:
    """驗證各 Adapter 的 CLI 命令與 backend_name 正確。"""

    @pytest.mark.parametrize(
        "backend_key, expected_cls, expected_cli, expected_name",
        [
            ("claude-code", ClaudeCodeAdapter, "claude", "claude-code"),
            ("gemini-cli", GeminiCliAdapter, "gemini", "gemini-cli"),
            ("codex", CodexAdapter, "codex", "codex"),
            ("opencode", OpenCodeAdapter, "opencode", "opencode"),
            ("kiro-cli", KiroCliAdapter, "kiro-cli", "kiro-cli"),
        ],
    )
    def test_adapter_cli_command_and_backend_name(
        self,
        backend_key: str,
        expected_cls: type,
        expected_cli: str,
        expected_name: str,
    ) -> None:
        adapter = get_adapter(backend_key)
        assert isinstance(adapter, expected_cls)
        assert adapter.cli_command == expected_cli
        assert adapter.backend_name == expected_name

    def test_kiro_cli_has_supported_models(self) -> None:
        adapter = get_adapter("kiro-cli")
        assert isinstance(adapter, KiroCliAdapter)
        assert "auto" in adapter.supported_models
        assert len(adapter.supported_models) >= 4

    def test_non_kiro_adapters_have_no_steering_check(self) -> None:
        """非 kiro-cli 的 Adapter 不需要 steering 目錄檢查，
        start_session 直接使用 TmuxBackendAdapter 的實作。"""
        for key in ["claude-code", "gemini-cli", "codex", "opencode"]:
            adapter = get_adapter(key)
            # 確認 start_session 未被子類別覆寫（使用 TmuxBackendAdapter 的版本）
            assert type(adapter).start_session is TmuxBackendAdapter.start_session
