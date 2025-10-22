#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for disorder prediction channel
TDD: Test-Driven Development approach

Tests both metapredict (if available) and heuristic fallback methods.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.features.disorder_iupred import (
    disorder_proxy_scores,
    _disorder_heuristic_single,
    _disorder_heuristic,
)


class TestDisorderProxy:
    """Test disorder proxy scoring"""

    @pytest.fixture
    def sample_sequences(self):
        """Fixture providing sample test sequences"""
        return [
            ("ordered", "WFYIVLCMNT" * 10),        # Order-promoting residues
            ("disordered", "PEKSQAGDR" * 10),      # Disorder-promoting residues
            ("mixed", "WFYPEKSQ" * 10),            # Mixed composition
            ("proline_rich", "PPPPGGGG" * 10),     # Proline/Glycine rich (disordered)
            ("hydrophobic", "VILMFW" * 10),        # Hydrophobic (ordered)
        ]

    @pytest.fixture
    def edge_case_sequences(self):
        """Fixture for edge cases"""
        return [
            ("empty", ""),
            ("very_short", "WFY"),
            ("very_long", "A" * 1000),
            ("single_aa", "P"),
        ]

    def test_returns_dict(self, sample_sequences):
        """Test that function returns a dictionary"""
        result = disorder_proxy_scores(sample_sequences, {})
        assert isinstance(result, dict)

    def test_all_sequences_scored(self, sample_sequences):
        """Test that all sequences receive scores"""
        result = disorder_proxy_scores(sample_sequences, {})
        assert len(result) == len(sample_sequences)
        for seq_id, _ in sample_sequences:
            assert seq_id in result

    def test_scores_are_numeric(self, sample_sequences):
        """Test that all scores are numeric (float)"""
        import math
        result = disorder_proxy_scores(sample_sequences, {})
        for score in result.values():
            assert isinstance(score, (int, float))
            assert not math.isnan(score)  # No NaN
            assert not math.isinf(score)  # No Inf

    def test_scores_in_valid_range(self, sample_sequences):
        """Test that scores are in [0, 1] range"""
        result = disorder_proxy_scores(sample_sequences, {})
        for score in result.values():
            assert 0.0 <= score <= 1.0, f"Score {score} out of range [0, 1]"

    def test_ordered_vs_disordered(self):
        """Test that ordered sequences get lower scores than disordered"""
        ordered_seq = [("ordered", "WFYIVLCMNT" * 10)]
        disordered_seq = [("disordered", "PEKSQAGDR" * 10)]

        result_ordered = disorder_proxy_scores(ordered_seq, {})
        result_disordered = disorder_proxy_scores(disordered_seq, {})

        # Ordered should have lower disorder score
        assert result_ordered["ordered"] < result_disordered["disordered"]

    def test_proline_rich_disordered(self):
        """Test that proline-rich sequences are scored as disordered"""
        proline_rich = [("proline", "PPPPGGGG" * 10)]
        hydrophobic = [("hydrophobic", "VILMFW" * 10)]

        result_proline = disorder_proxy_scores(proline_rich, {})
        result_hydrophobic = disorder_proxy_scores(hydrophobic, {})

        # Proline-rich should be more disordered
        assert result_proline["proline"] > result_hydrophobic["hydrophobic"]

    def test_empty_sequence_handling(self, edge_case_sequences):
        """Test handling of edge case: empty sequence"""
        empty_seqs = [("empty", "")]

        # Should not crash
        result = disorder_proxy_scores(empty_seqs, {})
        assert "empty" in result
        # Should return neutral score
        assert 0.0 <= result["empty"] <= 1.0

    def test_very_short_sequence(self):
        """Test very short sequences"""
        short_seqs = [("short", "WFY")]

        result = disorder_proxy_scores(short_seqs, {})
        assert "short" in result
        assert 0.0 <= result["short"] <= 1.0

    def test_very_long_sequence(self):
        """Test very long sequences (>1000 aa)"""
        long_seqs = [("long", "A" * 1000)]

        result = disorder_proxy_scores(long_seqs, {})
        assert "long" in result
        assert 0.0 <= result["long"] <= 1.0

    def test_config_parameter_handling(self, sample_sequences):
        """Test that cfg parameter is accepted (future-proofing)"""
        cfg = {"some_option": True}

        # Should not crash with config
        result = disorder_proxy_scores(sample_sequences, cfg)
        assert isinstance(result, dict)

    def test_heuristic_fallback_ordered(self):
        """Test heuristic method: ordered sequence"""
        ordered_seq = "WFYIVLCMNT" * 10
        score = _disorder_heuristic_single(ordered_seq)

        # Should be low disorder (< 0.5)
        assert score < 0.5

    def test_heuristic_fallback_disordered(self):
        """Test heuristic method: disordered sequence"""
        disordered_seq = "PEKSQAGDR" * 10
        score = _disorder_heuristic_single(disordered_seq)

        # Should be high disorder (> 0.5)
        assert score > 0.5

    def test_heuristic_empty_sequence(self):
        """Test heuristic method: empty sequence"""
        score = _disorder_heuristic_single("")

        # Should return neutral (0.5)
        assert score == 0.5

    def test_heuristic_batch_processing(self):
        """Test heuristic batch processing"""
        seqs = [
            ("ordered", "WFYIVL" * 10),
            ("disordered", "PEKSQA" * 10),
        ]

        result = _disorder_heuristic(seqs)

        assert len(result) == 2
        assert result["ordered"] < result["disordered"]

    def test_consistency_across_calls(self, sample_sequences):
        """Test that same input produces same output (deterministic)"""
        result1 = disorder_proxy_scores(sample_sequences, {})
        result2 = disorder_proxy_scores(sample_sequences, {})

        for seq_id in result1.keys():
            assert result1[seq_id] == result2[seq_id]

    def test_real_petase_sequences(self):
        """Test with real PETase-like sequences"""
        fixture_path = os.path.join(os.path.dirname(__file__),
                                   'fixtures', 'test_sequences.fasta')

        if os.path.exists(fixture_path):
            from src.utils_seq import read_fasta
            seqs = read_fasta(fixture_path)

            result = disorder_proxy_scores(seqs, {})

            # All should be scored
            assert len(result) == len(seqs)

            # Scores should be in valid range
            for score in result.values():
                assert 0.0 <= score <= 1.0

            # Most PETase variants should be relatively ordered
            # (enzymes are typically structured)
            scores = list(result.values())
            mean_score = sum(scores) / len(scores)
            assert mean_score < 0.6  # Expect mostly ordered


class TestMetapredictIntegration:
    """Test metapredict integration (if available)"""

    def test_metapredict_available(self):
        """Test if metapredict is available (informational)"""
        try:
            import metapredict
            print("\n[INFO] metapredict is available - using ML predictions")
            assert True
        except ImportError:
            print("\n[WARN] metapredict not installed - using heuristic fallback")
            pytest.skip("metapredict not available")

    def test_metapredict_produces_valid_scores(self):
        """Test metapredict produces scores in [0, 1] range"""
        try:
            import metapredict
        except ImportError:
            pytest.skip("metapredict not available")

        seqs = [("test", "WFYIVLCMNT" * 10)]
        result = disorder_proxy_scores(seqs, {})

        assert 0.0 <= result["test"] <= 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
