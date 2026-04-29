# tests/test_evaluator.py
from unittest import result

import pytest
from coffe.evaluator import Metrics


class TestMetricsPassAtK:
    def setup_method(self):
        self.metrics = Metrics()

    def test_all_correct_returns_one(self):
        result = self.metrics.pass_at_k(10, [10], 1)
        assert result[0] == pytest.approx(1.0)

    def test_none_correct_returns_zero(self):
        result = self.metrics.pass_at_k(10, [0], 1)
        assert result[0] == pytest.approx(0.0)

    def test_partial_correct(self):
        result = self.metrics.pass_at_k(10, [5], 1)
        assert 0.0 < result[0] < 1.0

    def test_multiple_problems(self):
        result = self.metrics.pass_at_k(10, [10, 0, 5], 1)
        assert len(result) == 3
        assert result[0] == pytest.approx(1.0)
        assert result[1] == pytest.approx(0.0)


class TestMetricsCorrelation:
    def setup_method(self):
        self.metrics = Metrics()

    def test_perfect_positive_correlation(self):
        x = [1, 2, 3, 4, 5]
        y = [1, 2, 3, 4, 5]
        assert self.metrics.correlation(x, y) == pytest.approx(1.0)

    def test_perfect_negative_correlation(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 4, 3, 2, 1]
        assert self.metrics.correlation(x, y) == pytest.approx(-1.0)

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError):
            self.metrics.correlation([1, 2], [1, 2, 3])


class TestMetricsRSD:
    def setup_method(self):
        self.metrics = Metrics()

    def test_zero_std_returns_zero(self):
        assert self.metrics.rsd([1.0, 2.0], [0.0, 0.0]) == pytest.approx(0.0)

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError):
            self.metrics.rsd([1.0, 2.0], [0.1])

    def test_negative_values_raises(self):
        with pytest.raises(ValueError):
            self.metrics.rsd([-1.0], [0.1])

    def test_valid_rsd(self):
        result = self.metrics.rsd([100.0], [10.0])
        assert result == pytest.approx(0.1)


class TestMetricsCal:
    def setup_method(self):
        self.metrics = Metrics()

    def test_invalid_metric_raises(self):
        result = self.metrics.cal("nonexistent_metric", "somefile.json")
        assert result is None

    def test_speedup_wrong_data_type_raises(self):
        with pytest.raises(ValueError):
            self.metrics.cal("speedup", "a,b", data_type="wrong")

    def test_efficient_at_1_wrong_data_type_raises(self):
        with pytest.raises(ValueError):
            self.metrics.cal("efficient_at_1", "a,b", data_type="wrong")

    def test_rsd_wrong_data_type_raises(self):
        with pytest.raises(ValueError):
            self.metrics.cal("rsd", "somefile.json", data_type="wrong")