#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for ensemble aggregation logic
TDD: Test-Driven Development approach
"""

import pytest
import sys
import os
import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ensemble.aggregate import fuse_one, fuse_scores, robust_scale, _to_df


class TestEnsembleAggregation:
    """Test ensemble fusion logic"""

    @pytest.fixture
    def sample_sequences(self):
        """Fixture providing sample test sequences"""
        return [
            ("seq1", "AAA"),
            ("seq2", "BBB"),
            ("seq3", "CCC"),
        ]

    @pytest.fixture
    def sample_channels(self):
        """Fixture providing sample channel scores"""
        return {
            'channel1': {'seq1': 0.8, 'seq2': 0.5, 'seq3': 0.2},
            'channel2': {'seq1': 0.9, 'seq2': 0.6, 'seq3': 0.3},
            'channel3': {'seq1': 0.7, 'seq2': 0.4, 'seq3': 0.1},
        }

    def test_to_df_conversion(self, sample_sequences, sample_channels):
        """Test channel dict to DataFrame conversion"""
        df = _to_df(sample_sequences, sample_channels)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(sample_sequences)
        assert list(df.columns) == list(sample_channels.keys())

    def test_robust_scaling(self):
        """Test robust (median/MAD) scaling"""
        df = pd.DataFrame({
            'channel1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'channel2': [10.0, 20.0, 30.0, 40.0, 50.0],
        })

        scaled = robust_scale(df)

        # Check that median is ~0
        assert abs(scaled['channel1'].median()) < 0.1
        assert abs(scaled['channel2'].median()) < 0.1

        # Check that MAD is normalized
        mad1 = (scaled['channel1'] - scaled['channel1'].median()).abs().median()
        assert abs(mad1 - 1.0) < 0.1

    def test_fuse_one_basic(self, sample_sequences, sample_channels):
        """Test basic fusion of channels"""
        result = fuse_one(sample_sequences, sample_channels)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_sequences)

        # Check all values in [0,1]
        assert (result >= 0).all()
        assert (result <= 1).all()

    def test_fuse_one_with_weights(self, sample_sequences, sample_channels):
        """Test fusion with custom weights"""
        weights = {'channel1': 0.5, 'channel2': 0.3, 'channel3': 0.2}

        result = fuse_one(sample_sequences, sample_channels, weights=weights)

        assert len(result) == len(sample_sequences)
        assert (result >= 0).all()
        assert (result <= 1).all()

    def test_fuse_one_missing_channel(self, sample_sequences):
        """Test fusion with missing channel values"""
        channels_with_missing = {
            'channel1': {'seq1': 0.8, 'seq2': 0.5},  # seq3 missing
            'channel2': {'seq1': 0.9, 'seq2': 0.6, 'seq3': 0.3},
        }

        result = fuse_one(sample_sequences, channels_with_missing)

        # Should handle gracefully
        assert len(result) == len(sample_sequences)
        assert 'seq3' in result.index

    def test_fuse_one_empty_channels(self, sample_sequences):
        """Test fusion with no channels (fallback to zero)"""
        empty_channels = {}

        result = fuse_one(sample_sequences, empty_channels)

        # Should return zeros
        assert len(result) == len(sample_sequences)
        assert (result == 0.0).all()

    def test_fuse_scores_complete(self, sample_sequences):
        """Test complete score fusion for all properties"""
        scores = {
            'activity': {
                'plm': {'seq1': 0.8, 'seq2': 0.5, 'seq3': 0.2},
                'priors': {'seq1': 0.7, 'seq2': 0.4, 'seq3': 0.1},
            },
            'stability': {
                'ddg': {'seq1': 0.6, 'seq2': 0.3, 'seq3': 0.0},
                'priors': {'seq1': 0.5, 'seq2': 0.2, 'seq3': -0.1},
            },
            'expression': {
                'solubility': {'seq1': 0.9, 'seq2': 0.6, 'seq3': 0.3},
            }
        }

        config = {
            'weights': {
                'activity': {'plm': 0.6, 'priors': 0.4},
                'stability': {'ddg': 0.7, 'priors': 0.3},
                'expression': {'solubility': 1.0},
            }
        }

        result = fuse_scores(sample_sequences, scores, config)

        # Check structure
        assert isinstance(result, pd.DataFrame)
        assert 'seq_id' in result.columns
        assert 'activity_score' in result.columns
        assert 'stability_score' in result.columns
        assert 'expression_score' in result.columns

        # Check all values in [0,1]
        assert (result['activity_score'] >= 0).all()
        assert (result['activity_score'] <= 1).all()
        assert (result['stability_score'] >= 0).all()
        assert (result['stability_score'] <= 1).all()
        assert (result['expression_score'] >= 0).all()
        assert (result['expression_score'] <= 1).all()

    def test_rank_averaging(self, sample_sequences):
        """Test that rank averaging works correctly"""
        channels = {
            'channel1': {'seq1': 10.0, 'seq2': 5.0, 'seq3': 1.0},
            'channel2': {'seq1': 100.0, 'seq2': 50.0, 'seq3': 10.0},
        }

        # Despite different scales, rank order should be preserved
        result = fuse_one(sample_sequences, channels)

        # seq1 should be highest, seq3 lowest
        assert result.loc['seq1'] > result.loc['seq2']
        assert result.loc['seq2'] > result.loc['seq3']

    def test_single_sequence_edge_case(self):
        """Test edge case: only one sequence"""
        single_seq = [("only_one", "AAA")]
        channels = {'channel1': {'only_one': 0.5}}

        result = fuse_one(single_seq, channels)

        # Should not crash, should return normalized value
        assert len(result) == 1
        assert 0 <= result.iloc[0] <= 1


class TestEnsembleRobustness:
    """Test ensemble robustness to edge cases"""

    def test_nan_handling(self):
        """Test handling of NaN values"""
        seqs = [("seq1", "A"), ("seq2", "B")]
        channels = {
            'channel1': {'seq1': 0.5, 'seq2': np.nan},
        }

        # Should handle NaN gracefully
        result = fuse_one(seqs, channels)
        assert not result.isna().any()

    def test_inf_handling(self):
        """Test handling of infinite values"""
        seqs = [("seq1", "A"), ("seq2", "B")]
        channels = {
            'channel1': {'seq1': 0.5, 'seq2': np.inf},
        }

        # Should handle inf gracefully
        result = fuse_one(seqs, channels)
        assert not result.isin([np.inf, -np.inf]).any()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
