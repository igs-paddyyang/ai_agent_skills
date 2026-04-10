"""split_message 函式的單元測試。"""

from __future__ import annotations

import pytest

from kiro_agent.channel_router import split_message


class TestSplitMessageBasic:
    """基本分割行為。"""

    def test_empty_string_returns_single_empty(self) -> None:
        assert split_message("") == [""]

    def test_short_string_single_chunk(self) -> None:
        text = "hello world"
        result = split_message(text)
        assert result == [text]

    def test_exactly_max_length_single_chunk(self) -> None:
        text = "a" * 4096
        result = split_message(text)
        assert result == [text]

    def test_over_max_length_multiple_chunks(self) -> None:
        text = "a" * 8192
        result = split_message(text)
        assert len(result) > 1
        assert all(len(c) <= 4096 for c in result)
        assert "".join(result) == text

    def test_custom_max_length(self) -> None:
        text = "abcdefghij"  # 10 chars
        result = split_message(text, max_length=4)
        assert all(len(c) <= 4 for c in result)
        assert "".join(result) == text


class TestSplitMessagePreferNewlines:
    """優先在換行符處分割。"""

    def test_splits_at_newline(self) -> None:
        line_a = "a" * 2000 + "\n"
        line_b = "b" * 2000 + "\n"
        line_c = "c" * 2000
        text = line_a + line_b + line_c  # 6001 chars total
        result = split_message(text)
        assert "".join(result) == text
        assert all(len(c) <= 4096 for c in result)
        # 第一段應在某個換行處結束
        assert result[0].endswith("\n")


class TestSplitMessagePreferSpaces:
    """無換行時在空格處分割。"""

    def test_splits_at_space(self) -> None:
        # 建立一段沒有換行但有空格的長文字
        word = "abcde "  # 6 chars
        repetitions = 4096 // len(word) + 100
        text = word * repetitions
        result = split_message(text)
        assert "".join(result) == text
        assert all(len(c) <= 4096 for c in result)


class TestSplitMessageHardCut:
    """無空格也無換行時強制在 max_length 處切割。"""

    def test_no_whitespace_hard_split(self) -> None:
        text = "x" * 10000
        result = split_message(text)
        assert "".join(result) == text
        assert all(len(c) <= 4096 for c in result)
        # 前面的段應該剛好 4096
        assert len(result[0]) == 4096


class TestSplitMessageConcatenation:
    """串接所有片段必須還原原始字串。"""

    def test_mixed_content_round_trip(self) -> None:
        # 混合換行、空格、長連續字元
        parts = [
            "short line\n",
            "a" * 3000 + " ",
            "b" * 5000,
            "\n",
            "c" * 100,
        ]
        text = "".join(parts)
        result = split_message(text)
        assert "".join(result) == text
        assert all(len(c) <= 4096 for c in result)


class TestSplitMessageEdgeCases:
    """邊界情況。"""

    def test_invalid_max_length_raises(self) -> None:
        with pytest.raises(ValueError):
            split_message("hello", max_length=0)

    def test_max_length_one(self) -> None:
        text = "abc"
        result = split_message(text, max_length=1)
        assert result == ["a", "b", "c"]
        assert "".join(result) == text
