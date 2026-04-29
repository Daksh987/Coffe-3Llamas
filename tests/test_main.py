# tests/test_main.py
import pytest
import argparse
import json
import os
from unittest.mock import patch, MagicMock
from coffe.main import check_init, check_input_file, info


class TestCheckInputFile:
    def test_correctness_requires_solutions_suffix(self):
        with pytest.raises(ValueError):
            check_input_file("predictions.json", "correctness")

    def test_correctness_accepts_solutions_suffix(self):
        check_input_file("predictions_SOLUTIONS.json", "correctness")

    def test_time_requires_passed_solutions_suffix(self):
        with pytest.raises(ValueError):
            check_input_file("predictions.json", "time")

    def test_instr_count_requires_passed_solutions_suffix(self):
        with pytest.raises(ValueError):
            check_input_file("predictions.json", "instr_count")

    def test_time_accepts_passed_solutions_suffix(self):
        check_input_file("predictions_PASSED_SOLUTIONS.json", "time")

    def test_instr_count_accepts_passed_solutions_suffix(self):
        check_input_file("predictions_PASSED_SOLUTIONS.json", "instr_count")

    def test_compilable_rate_accepts_any_file(self):
        check_input_file("predictions.json", "compilable_rate")


class TestCheckInit:
    def test_raises_when_no_init_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="You must initialize Coffe first!"):
            check_init()

    def test_raises_when_config_corrupted(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        init_file = tmp_path / "coffe_init.json"
        init_file.write_text(json.dumps({"dataset": "/some/path"}))
        with pytest.raises(ValueError, match="corrupted"):
            check_init()

    def test_returns_paths_when_valid(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        data = {
            "dataset": "/some/dataset",
            "workdir": str(tmp_path),
            "perf_path": "/some/perf.json"
        }
        init_file = tmp_path / "coffe_init.json"
        init_file.write_text(json.dumps(data))
        dataset, workdir, perf = check_init()
        assert dataset == "/some/dataset"
        assert workdir == str(tmp_path)
        assert perf == "/some/perf.json"

    def test_exits_when_workdir_mismatch(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        data = {
            "dataset": "/some/dataset",
            "workdir": "/wrong/dir",
            "perf_path": "/some/perf.json"
        }
        init_file = tmp_path / "coffe_init.json"
        init_file.write_text(json.dumps(data))
        with pytest.raises(SystemExit):
            check_init()


class TestInfo:
    def test_info_prints_output(self, capsys):
        args = MagicMock()
        info(args)
        captured = capsys.readouterr()
        assert "Coffe" in captured.out
        assert "https://github.com/JohnnyPeng18/Coffe" in captured.out