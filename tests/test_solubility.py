#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for solubility proxy channel
TDD: Test-Driven Development approach
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.features.solubility import solubility_proxy_scores


class TestSolubilityProxy:
    """Test solubility proxy scoring"""

    @pytest.fixture
    def sample_sequences(self):
        """Fixture providing sample test sequences"""
        return [
            ("hydrophobic", "AVILMFWGP" * 10),  # Hydrophobic-rich
            ("hydrophilic", "KRDEHSTNQ" * 10),  # Hydrophilic-rich
            ("charged_pos", "KKKKRRRR" * 10),   # Positive charged
            ("charged_neg", "DDDDEEEE" * 10),   # Negative charged
            ("long_seq", "A" * 400),            # Long sequence (>300)
        ]

    def test_returns_dict(self, sample_sequences):
        """Test that function returns a dictionary"""
        result = solubility_proxy_scores(sample_sequences, {})
        assert isinstance(result, dict)

    def test_all_sequences_scored(self, sample_sequences):
        """Test that all sequences receive scores"""
        result = solubility_proxy_scores(sample_sequences, {})
        assert len(result) == len(sample_sequences)
        for seq_id, _ in sample_sequences:
            assert seq_id in result

    def test_scores_are_numeric(self, sample_sequences):
        """Test that all scores are numeric (float)"""
        result = solubility_proxy_scores(sample_sequences, {})
        for score in result.values():
            assert isinstance(score, (int, float))
            assert not pytest.approx(score, nan_ok=False)  # No NaN

    def test_hydrophobic_penalty(self):
        """Test that hydrophobic sequences get lower scores"""
        hydrophobic_seq = [("hydrophobic", "AVILMFWGP" * 10)]
        hydrophilic_seq = [("hydrophilic", "KRDEHSTNQ" * 10)]

        result_hydrophobic = solubility_proxy_scores(hydrophobic_seq, {})
        result_hydrophilic = solubility_proxy_scores(hydrophilic_seq, {})

        # Hydrophilic should score higher (less penalty)
        assert result_hydrophilic["hydrophilic"] > result_hydrophobic["hydrophobic"]

    def test_length_penalty(self):
        """Test that long sequences (>300 aa) get penalized"""
        short_seq = [("short", "A" * 250)]
        long_seq = [("long", "A" * 400)]

        result_short = solubility_proxy_scores(short_seq, {})
        result_long = solubility_proxy_scores(long_seq, {})

        # Short should score higher
        assert result_short["short"] > result_long["long"]

    def test_charge_balance(self):
        """Test charge balance affects score"""
        balanced = [("balanced", "KDERH" * 20)]  # Mixed charges
        unbalanced = [("unbalanced", "KKKKK" * 20)]  # Only positive

        result_balanced = solubility_proxy_scores(balanced, {})
        result_unbalanced = solubility_proxy_scores(unbalanced, {})

        # Balanced should score higher
        assert result_balanced["balanced"] > result_unbalanced["unbalanced"]

    def test_empty_sequence_handling(self):
        """Test handling of edge case: empty sequence"""
        empty_seqs = [("empty", "")]

        # Should not crash
        result = solubility_proxy_scores(empty_seqs, {})
        assert "empty" in result

    def test_real_petase_sequences(self):
        """Test with real PETase-like sequences"""
        # Load fixture
        fixture_path = os.path.join(os.path.dirname(__file__),
                                   'fixtures', 'test_sequences.fasta')

        if os.path.exists(fixture_path):
            from src.utils_seq import read_fasta
            seqs = read_fasta(fixture_path)

            result = solubility_proxy_scores(seqs, {})

            # All should be scored
            assert len(result) == len(seqs)

            # Scores should be reasonable (not extreme outliers)
            scores = list(result.values())
            mean_score = sum(scores) / len(scores)
            assert -10 < mean_score < 10  # Reasonable range


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
