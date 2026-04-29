import pytest
import numpy as np
from coffe.code_execution import (
    is_floats,
    is_equal,
    trasform_tuples_into_lists,
    check_success,
    untrusted_check,
    untrusted_testcase_check,
    SUCCEED,
    FAILED,
    INF,
    _PASS,
    _FAIL,
)


class TestIsFloats:
    def test_float_returns_true(self):
        assert is_floats(1.0) is True

    def test_int_returns_false(self):
        assert is_floats(1) is False

    def test_list_of_floats_returns_true(self):
        assert is_floats([1.0, 2.0]) is True

    def test_list_of_ints_returns_false(self):
        assert is_floats([1, 2]) is False

    def test_numpy_float64_returns_true(self):
        assert is_floats(np.array([1.0], dtype=np.float64)) is True


class TestTransformTuples:
    def test_tuple_becomes_list(self):
        assert trasform_tuples_into_lists((1, 2, 3)) == [1, 2, 3]

    def test_nested_tuple(self):
        assert trasform_tuples_into_lists((1, (2, 3))) == [1, [2, 3]]

    def test_dict_values_transformed(self):
        assert trasform_tuples_into_lists({"a": (1, 2)}) == {"a": [1, 2]}

    def test_scalar_unchanged(self):
        assert trasform_tuples_into_lists(42) == 42


class TestIsEqual:
    def test_equal_ints(self):
        assert is_equal(1, 1) is True

    def test_unequal_ints(self):
        assert is_equal(1, 2) is False

    def test_equal_strings(self):
        assert is_equal("hello", "hello") is True

    def test_strings_whitespace_ignored(self):
        assert is_equal("hello world", "helloworld") is True

    def test_floats_auto_tolerance(self):
        assert is_equal(1.0, 1.0 + 1e-7) is True

    def test_tuple_vs_list_equal(self):
        assert is_equal((1, 2, 3), [1, 2, 3]) is True

    def test_unequal_lists(self):
        assert is_equal([1, 2], [1, 3]) is False


class TestCheckSuccess:
    def test_all_succeed_returns_true(self):
        results = [{"status": SUCCEED}, {"status": SUCCEED}]
        assert check_success(results) is True

    def test_one_failed_returns_false(self):
        results = [{"status": SUCCEED}, {"status": FAILED}]
        assert check_success(results) is False

    def test_missing_status_returns_false(self):
        results = [{"status": SUCCEED}, {}]
        assert check_success(results) is False

    def test_empty_results_returns_true(self):
        assert check_success([]) is True


class TestUntrustedTestcaseCheck:
    def test_valid_expression_passes(self):
        result = untrusted_testcase_check('{"input": [1, 2, 3], "output": [6]}')
        assert result == _PASS

    def test_invalid_expression_fails(self):
        result = untrusted_testcase_check("this is not valid python!!!")
        assert result == _FAIL

    def test_division_by_zero_fails(self):
        result = untrusted_testcase_check("1/0")
        assert result == _FAIL


class TestUntrustedCheck:
    def test_correct_function_passes(self):
        code = "def solution(a, b):\n    return a + b"
        testcases = [{"input": [1, 2], "output": [3]}]
        stat, results = untrusted_check(
            io=False,
            code=code,
            testcases=testcases,
            atol=0,
            ref_time=[1.0],
            check=True,
        )
        assert stat == _PASS

    def test_incorrect_function_fails(self):
        code = "def solution(a, b):\n    return a - b"
        testcases = [{"input": [1, 2], "output": [3]}]
        stat, results = untrusted_check(
            io=False,
            code=code,
            testcases=testcases,
            atol=0,
            ref_time=[1.0],
            check=True,
        )
        assert stat == _FAIL

    def test_syntax_error_code_fails(self):
        code = "def solution(a, b)\n    return a + b"
        testcases = [{"input": [1, 2], "output": [3]}]
        stat, results = untrusted_check(
            io=False,
            code=code,
            testcases=testcases,
            atol=0,
            ref_time=[1.0],
            check=True,
        )
        assert stat == _FAIL

    def test_multiple_testcases(self):
        code = "def solution(x):\n    return x * 2"
        testcases = [
            {"input": [2], "output": [4]},
            {"input": [3], "output": [6]},
            {"input": [0], "output": [0]},
        ]
        stat, results = untrusted_check(
            io=False,
            code=code,
            testcases=testcases,
            atol=0,
            ref_time=[1.0, 1.0, 1.0],
            check=True,
        )
        assert stat == _PASS