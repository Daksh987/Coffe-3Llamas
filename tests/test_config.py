import pytest
from coffe.config import benchmarks


class TestBenchmarksConfig:
    def test_benchmarks_is_dict(self):
        assert isinstance(benchmarks, dict)

    def test_expected_keys_present(self):
        expected = {"openai_humaneval", "mbpp", "codeparrot/apps", "deepmind/code_contests", "function", "file"}
        assert expected == set(benchmarks.keys())

    def test_all_benchmarks_have_path(self):
        for name, config in benchmarks.items():
            assert "path" in config, f"Benchmark '{name}' is missing 'path'"

    def test_humaneval_config(self):
        cfg = benchmarks["openai_humaneval"]
        assert cfg["code_keyword"] == "canonical_solution"
        assert cfg["testcase_keyword"] == "testcases"
        assert cfg["add_list"] is False
        assert cfg["path"] == "openai_humaneval"

    def test_mbpp_config(self):
        cfg = benchmarks["mbpp"]
        assert cfg["code_keyword"] == "code"
        assert cfg["testcase_keyword"] == "testcases"
        assert cfg["add_list"] is False
        assert cfg["path"] == "mbpp"

    def test_apps_config(self):
        cfg = benchmarks["codeparrot/apps"]
        assert cfg["code_keyword"] == "solutions"
        assert cfg["testcase_keyword"] == "input_output"
        assert cfg["add_list"] is True
        assert cfg["path"] == "codeparrot_apps"

    def test_code_contests_config(self):
        cfg = benchmarks["deepmind/code_contests"]
        assert cfg["code_keyword"] == "solutions"
        assert isinstance(cfg["testcase_keyword"], list)
        assert "private_tests" in cfg["testcase_keyword"]
        assert "generated_tests" in cfg["testcase_keyword"]
        assert cfg["add_list"] is True
        assert cfg["path"] == "deepmind_code_contests"

    def test_function_config(self):
        cfg = benchmarks["function"]
        assert cfg["path"] == "function"

    def test_file_config(self):
        cfg = benchmarks["file"]
        assert cfg["path"] == "file"

    def test_add_list_is_bool(self):
        for name, config in benchmarks.items():
            if "add_list" in config:
                assert isinstance(config["add_list"], bool), f"'add_list' in '{name}' should be bool"

    def test_paths_are_strings(self):
        for name, config in benchmarks.items():
            assert isinstance(config["path"], str), f"'path' in '{name}' should be a string"