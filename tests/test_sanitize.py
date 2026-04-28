import pytest
from coffe.sanitize import (
    syntax_check,
    sanitize,
    to_four_space_indents,
    remove_unindented_lines,
    CodeVisitor,
    CodeProcessor,
    CommentRemover,
)


# ──────────────────────────────────────────────
# syntax_check
# ──────────────────────────────────────────────

class TestSyntaxCheck:
    def test_valid_code_returns_true(self):
        assert syntax_check("x = 1 + 2") is True

    def test_valid_function_returns_true(self):
        code = "def foo(x):\n    return x + 1"
        assert syntax_check(code) is True

    def test_invalid_syntax_returns_false(self):
        assert syntax_check("def foo(:\n    pass") is False

    def test_empty_string_returns_true(self):
        assert syntax_check("") is True

    def test_unclosed_paren_returns_false(self):
        assert syntax_check("print('hello'") is False


# ──────────────────────────────────────────────
# to_four_space_indents
# ──────────────────────────────────────────────

class TestToFourSpaceIndents:
    def test_three_space_indent_becomes_four(self):
        code = "def foo():\n   return 1"
        result = to_four_space_indents(code)
        assert result == "def foo():\n    return 1\n"

    def test_four_space_indent_unchanged(self):
        code = "def foo():\n    return 1"
        result = to_four_space_indents(code)
        assert "    return 1" in result

    def test_no_indent_unchanged(self):
        code = "x = 1"
        result = to_four_space_indents(code)
        assert "x = 1" in result


# ──────────────────────────────────────────────
# remove_unindented_lines
# ──────────────────────────────────────────────

class TestRemoveUnindentedLines:
    def test_removes_unindented_line_after_def(self):
        code = "def foo(x):\n    return x\nunindented_line = 1"
        result = remove_unindented_lines(
            code,
            protect_before="def foo(",
            execeptions=["def ", "import "],
            trim_tails=["if", "print"],
        )
        assert "unindented_line" not in result

    def test_keeps_def_lines(self):
        code = "def foo(x):\n    return x\ndef bar():\n    pass"
        result = remove_unindented_lines(
            code,
            protect_before="def foo(",
            execeptions=["def ", "import "],
            trim_tails=["if", "print"],
        )
        assert "def bar" in result

    def test_trim_tail_cuts_off_if(self):
        code = "def foo(x):\n    return x\nif __name__:\n    foo()"
        result = remove_unindented_lines(
            code,
            protect_before="def foo(",
            execeptions=["def ", "import "],
            trim_tails=["if", "print"],
        )
        assert "if __name__" not in result


# ──────────────────────────────────────────────
# CodeVisitor
# ──────────────────────────────────────────────

class TestCodeVisitor:
    def test_detects_function(self):
        code = "def foo():\n    return 1"
        visitor = CodeVisitor(code)
        visitor.run()
        assert "foo" in visitor.funcs

    def test_detects_class(self):
        code = "class MyClass:\n    def method(self):\n        pass"
        visitor = CodeVisitor(code)
        visitor.run()
        assert "MyClass" in visitor.classes

    def test_detects_input_call(self):
        code = "x = input()"
        visitor = CodeVisitor(code)
        visitor.run()
        assert visitor.has_input is True

    def test_no_input_call(self):
        code = "x = 1 + 2"
        visitor = CodeVisitor(code)
        visitor.run()
        assert visitor.has_input is False

    def test_only_func_true_when_only_functions(self):
        code = "def foo():\n    return 1\ndef bar():\n    return 2"
        visitor = CodeVisitor(code)
        visitor.run()
        assert visitor.only_func is True

    def test_only_func_false_when_mixed(self):
        code = "x = 1\ndef foo():\n    return 1"
        visitor = CodeVisitor(code)
        visitor.run()
        assert visitor.only_func is False

    def test_all_func_in_class(self):
        code = "class MyClass:\n    def method(self):\n        pass"
        visitor = CodeVisitor(code)
        visitor.run()
        assert visitor.all_func_in_class is True


# ──────────────────────────────────────────────
# CommentRemover
# ──────────────────────────────────────────────

class TestCommentRemover:
    def test_removes_imports(self):
        code = "import os\ndef foo():\n    return 1"
        remover = CommentRemover(code)
        result = remover.run()
        assert "import os" not in result

    def test_removes_docstring(self):
        code = 'def foo():\n    """This is a docstring."""\n    return 1'
        remover = CommentRemover(code)
        result = remover.run()
        assert "docstring" not in result

    def test_keeps_function_body(self):
        code = "def foo():\n    return 1"
        remover = CommentRemover(code)
        result = remover.run()
        assert "return 1" in result


# ──────────────────────────────────────────────
# sanitize
# ──────────────────────────────────────────────

class TestSanitize:
    def test_basic_function_extraction(self):
        code = "def add(a, b):\n    return a + b"
        result = sanitize(code, entry_point="add")
        assert "def add" in result

    def test_strips_markdown_code_fences(self):
        code = "```python\ndef add(a, b):\n    return a + b\n```"
        result = sanitize(code, entry_point="add")
        assert "```" not in result

    def test_handles_windows_line_endings(self):
        code = "def add(a, b):\r\n    return a + b"
        result = sanitize(code, entry_point="add")
        assert "\r\n" not in result

    def test_replaces_escaped_underscores(self):
        code = "def add\\_up(a, b):\n    return a + b"
        result = sanitize(code, entry_point="add_up")
        assert "\\_" not in result

    def test_empty_code_returns_empty(self):
        result = sanitize("", entry_point="foo")
        assert result == ""

    def test_global_code_with_markdown(self):
        code = "```python\nx = 1\nprint(x)\n```"
        result = sanitize(code, entry_point="foo", global_code=True)
        assert "```" not in result
        assert "x = 1" in result

    def test_eof_truncation(self):
        code = "def foo(x):\n    return x\nSTOP\nextra_line = 1"
        result = sanitize(code, entry_point="foo", eofs=["STOP"])
        assert "extra_line" not in result