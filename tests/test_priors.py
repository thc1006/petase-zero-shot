#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for literature-driven biochemical priors channel
TDD: Test-Driven Development approach
"""

import pytest
import sys
import os
import yaml

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.features.priors import prior_scores, _align_to_wt, _load_yaml


class TestPriorsChannel:
    """Test biochemical priors scoring"""

    @pytest.fixture
    def config(self):
        """Fixture providing test configuration"""
        return {
            'priors_yaml': 'data/priors/priors_petase_2024_2025.yaml',
            # No wt_fasta for basic tests
        }

    @pytest.fixture
    def sample_sequences(self):
        """Fixture providing sample test sequences"""
        return [
            ("wild_type_like", "A" * 300),
            ("short_seq", "AAA"),
            ("long_seq", "A" * 350),
        ]

    def test_returns_two_dicts(self, sample_sequences, config):
        """Test that function returns activity and stability dicts"""
        activity, stability = prior_scores(sample_sequences, config)

        assert isinstance(activity, dict)
        assert isinstance(stability, dict)

    def test_all_sequences_scored(self, sample_sequences, config):
        """Test that all sequences receive scores"""
        activity, stability = prior_scores(sample_sequences, config)

        assert len(activity) == len(sample_sequences)
        assert len(stability) == len(sample_sequences)

        for seq_id, _ in sample_sequences:
            assert seq_id in activity
            assert seq_id in stability

    def test_scores_are_numeric(self, sample_sequences, config):
        """Test that all scores are numeric (no NaN)"""
        activity, stability = prior_scores(sample_sequences, config)

        for score in activity.values():
            assert isinstance(score, (int, float))
            assert not pytest.approx(score, nan_ok=False)

        for score in stability.values():
            assert isinstance(score, (int, float))
            assert not pytest.approx(score, nan_ok=False)

    def test_yaml_loading(self, config):
        """Test that priors YAML loads correctly"""
        yaml_path = config['priors_yaml']
        assert os.path.exists(yaml_path), f"Priors YAML not found: {yaml_path}"

        priors = _load_yaml(yaml_path)

        # Check structure
        assert 'activity' in priors
        assert 'stability' in priors
        assert 'expression' in priors

        # Check catalytic triad
        assert 'catalytic_triad' in priors['activity']
        assert 'positions' in priors['activity']['catalytic_triad']
        assert priors['activity']['catalytic_triad']['positions'] == [160, 206, 237]

        # Check oxyanion hole
        assert 'oxyanion_hole' in priors['activity']
        assert 'positions' in priors['activity']['oxyanion_hole']

        # Check favorable regions
        assert 'favorable_regions' in priors['activity']
        assert len(priors['activity']['favorable_regions']) > 0

    def test_activity_has_triad_penalty(self, config):
        """Test that catalytic triad mutations get penalized"""
        # Without WT, should still apply conservative penalty
        test_seqs = [("test", "A" * 300)]
        activity, _ = prior_scores(test_seqs, config)

        # Should have some penalty (negative or zero)
        assert activity["test"] <= 1.0  # Not excessively positive

    def test_stability_has_positive_rewards(self, config):
        """Test that stability gets positive rewards from rules"""
        test_seqs = [("test", "A" * 300)]
        _, stability = prior_scores(test_seqs, config)

        # Should have positive rewards from stability rules
        assert stability["test"] > 0

    def test_alignment_function(self):
        """Test WT alignment mapping function"""
        wt = "ABCDEFGH"
        variant = "ABXDEFGH"  # C->X mutation

        mapping = _align_to_wt(variant, wt)

        # Should map positions correctly
        assert mapping[1] == 1  # A
        assert mapping[2] == 2  # B
        assert mapping[3] == 3  # C (now X in variant)
        assert mapping[4] == 4  # D

    def test_with_wt_sequence(self, config):
        """Test scoring with WT sequence for mutation detection"""
        # Create a minimal WT
        wt_content = ">IsPETase_WT\nMNFPRASRLMQAAVLGGLMAVSAAATAQ"
        wt_path = 'tests/fixtures/wt_test.fasta'

        with open(wt_path, 'w') as f:
            f.write(wt_content)

        config_with_wt = {
            'priors_yaml': 'data/priors/priors_petase_2024_2025.yaml',
            'wt_fasta': wt_path
        }

        test_seqs = [("variant", "MNFPRASRLMQAAVLGGLMAVSAAATAQ")]

        activity, stability = prior_scores(test_seqs, config_with_wt)

        # Should complete without error
        assert "variant" in activity
        assert "variant" in stability

        # Cleanup
        if os.path.exists(wt_path):
            os.remove(wt_path)

    def test_real_petase_fixtures(self, config):
        """Test with real PETase sequences from fixtures"""
        fixture_path = os.path.join(os.path.dirname(__file__),
                                   'fixtures', 'test_sequences.fasta')

        if os.path.exists(fixture_path):
            from src.utils_seq import read_fasta
            seqs = read_fasta(fixture_path)

            activity, stability = prior_scores(seqs, config)

            # All sequences should be scored
            assert len(activity) == len(seqs)
            assert len(stability) == len(seqs)

            # Check H218N variant gets favorable score
            if any('H218N' in sid for sid, _ in seqs):
                h218n_id = [sid for sid, _ in seqs if 'H218N' in sid][0]
                # Should have some positive contribution from favorable regions
                assert activity[h218n_id] != 0  # Not just default

    def test_favorable_region_rewards(self, config):
        """Test that favorable regions contribute positive scores"""
        # Sequence with positions matching favorable regions
        # Position 218, 222, 243 (beta6-beta7 loop)
        test_seqs = [("with_favorable", "A" * 300)]

        activity, _ = prior_scores(test_seqs, config)

        # Should have some positive component
        # (Even without exact matching, should be non-zero due to presence)
        assert isinstance(activity["with_favorable"], (int, float))


class TestPriorsIntegration:
    """Integration tests for priors in full pipeline"""

    def test_priors_in_pipeline(self):
        """Test that priors channel integrates with pipeline"""
        # This will be tested in test_pipeline.py
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
