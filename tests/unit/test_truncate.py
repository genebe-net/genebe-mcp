from genebe_mcp.truncate import take, truncate_text


def test_short_text_is_untouched():
    assert truncate_text("abc", 10) == ("abc", False)


def test_long_text_cut_on_line_boundary():
    text = "line one\nline two\nline three is long"
    out, truncated = truncate_text(text, 20)
    assert truncated
    assert out.startswith("line one\nline two")
    assert "three" not in out
    assert out.endswith("[... truncated ...]")


def test_take():
    assert take([1, 2, 3], 2) == ([1, 2], True)
    assert take([1], 2) == ([1], False)
