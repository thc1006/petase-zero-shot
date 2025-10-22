#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integration tests for complete PETase prediction pipeline
TDD: Test-Driven Development approach
"""

import pytest
import sys
import os
import tempfile
import shutil
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pipelines.run_all import run_pipeline
from src.utils_seq import read_fasta


class TestPipelineIntegration:
    """Integration tests for full pipeline"""

    @pytest.fixture
    def test_config(self):
        """Fixture providing test configuration"""
        return {
            'use_plm': True,
            'use_gemme': False,
            'use_ddg_foldx': False,
            'use_ddg_rosetta': False,
            'use_deepddg': False,
            'use_disorder': False,
            'use_priors': True,
            'priors_yaml': 'data/priors/priors_petase_2024_2025.yaml',
            'weights': {
                'activity': {'plm_llr': 0.60, 'priors': 0.40},
                'stability': {'plm_perplexity': 0.50, 'priors': 0.50},
                'expression': {'solubility_proxy': 1.0},
            }
        }

    @pytest.fixture
    def test_fasta(self):
        """Fixture providing test FASTA path"""
        return 'tests/fixtures/test_sequences.fasta'

    @pytest.fixture
    def temp_outdir(self):
        """Fixture providing temporary output directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    def test_pipeline_runs_successfully(self, test_fasta, temp_outdir, test_config):
        """Test that pipeline runs without errors"""
        if not os.path.exists(test_fasta):
            pytest.skip("Test fixtures not available")

        # Run pipeline
        run_pipeline(test_fasta, temp_outdir, test_config)

        # Check outputs exist
        assert os.path.exists(os.path.join(temp_outdir, 'predictions.csv'))
        assert os.path.exists(os.path.join(temp_outdir, 'METHODS.md'))
        assert os.path.exists(os.path.join(temp_outdir, 'figures'))

    def test_predictions_csv_format(self, test_fasta, temp_outdir, test_config):
        """Test that predictions.csv has correct format"""
        if not os.path.exists(test_fasta):
            pytest.skip("Test fixtures not available")

        run_pipeline(test_fasta, temp_outdir, test_config)

        pred_path = os.path.join(temp_outdir, 'predictions.csv')
        df = pd.read_csv(pred_path)

        # Check columns
        expected_cols = {'seq_id', 'activity_score', 'stability_score', 'expression_score'}
        assert set(df.columns) == expected_cols

        # Check no NaN
        assert not df.isna().any().any()

        # Check range [0,1]
        for col in ['activity_score', 'stability_score', 'expression_score']:
            assert (df[col] >= 0).all()
            assert (df[col] <= 1).all()

    def test_methods_md_content(self, test_fasta, temp_outdir, test_config):
        """Test that METHODS.md contains priors description"""
        if not os.path.exists(test_fasta):
            pytest.skip("Test fixtures not available")

        run_pipeline(test_fasta, temp_outdir, test_config)

        methods_path = os.path.join(temp_outdir, 'METHODS.md')
        with open(methods_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should contain priors description
        assert 'Biochemical Priors' in content or 'priors' in content.lower()
        assert 'catalytic triad' in content.lower() or 'Ser160' in content

    def test_figures_generated(self, test_fasta, temp_outdir, test_config):
        """Test that histogram figures are generated"""
        if not os.path.exists(test_fasta):
            pytest.skip("Test fixtures not available")

        run_pipeline(test_fasta, temp_outdir, test_config)

        figures_dir = os.path.join(temp_outdir, 'figures')
        assert os.path.exists(figures_dir)

        # Check for expected figures
        expected_figures = [
            'activity_score_hist.png',
            'stability_score_hist.png',
            'expression_score_hist.png',
        ]

        for fig in expected_figures:
            fig_path = os.path.join(figures_dir, fig)
            assert os.path.exists(fig_path)
            assert os.path.getsize(fig_path) > 0  # Not empty

    def test_sequence_count_matches(self, test_fasta, temp_outdir, test_config):
        """Test that output has same number of sequences as input"""
        if not os.path.exists(test_fasta):
            pytest.skip("Test fixtures not available")

        seqs = read_fasta(test_fasta)
        run_pipeline(test_fasta, temp_outdir, test_config)

        pred_path = os.path.join(temp_outdir, 'predictions.csv')
        df = pd.read_csv(pred_path)

        assert len(df) == len(seqs)

    def test_sequence_ids_match(self, test_fasta, temp_outdir, test_config):
        """Test that sequence IDs are preserved"""
        if not os.path.exists(test_fasta):
            pytest.skip("Test fixtures not available")

        seqs = read_fasta(test_fasta)
        input_ids = [sid for sid, _ in seqs]

        run_pipeline(test_fasta, temp_outdir, test_config)

        pred_path = os.path.join(temp_outdir, 'predictions.csv')
        df = pd.read_csv(pred_path)

        assert set(df['seq_id']) == set(input_ids)

    def test_score_differentiation(self, test_fasta, temp_outdir, test_config):
        """Test that scores differentiate between sequences"""
        if not os.path.exists(test_fasta):
            pytest.skip("Test fixtures not available")

        seqs = read_fasta(test_fasta)
        if len(seqs) < 2:
            pytest.skip("Need at least 2 sequences for differentiation test")

        run_pipeline(test_fasta, temp_outdir, test_config)

        pred_path = os.path.join(temp_outdir, 'predictions.csv')
        df = pd.read_csv(pred_path)

        # Check that not all scores are identical
        # (At least one property should show variation)
        has_variation = False
        for col in ['activity_score', 'stability_score', 'expression_score']:
            if df[col].nunique() > 1:
                has_variation = True
                break

        assert has_variation, "Scores should differentiate between sequences"


class TestPipelineRobustness:
    """Test pipeline robustness to edge cases"""

    def test_single_sequence(self, temp_outdir):
        """Test pipeline with single sequence"""
        single_fasta = os.path.join(temp_outdir, 'single.fasta')
        with open(single_fasta, 'w') as f:
            f.write(">single\nMNFPRASRL\n")

        config = {
            'use_plm': True,
            'use_priors': True,
            'priors_yaml': 'data/priors/priors_petase_2024_2025.yaml',
        }

        # Should not crash
        run_pipeline(single_fasta, temp_outdir, config)

        pred_path = os.path.join(temp_outdir, 'predictions.csv')
        assert os.path.exists(pred_path)

    def test_graceful_channel_failure(self, test_fasta, temp_outdir):
        """Test that pipeline continues if optional channel fails"""
        if not os.path.exists(test_fasta):
            pytest.skip("Test fixtures not available")

        config = {
            'use_plm': True,
            'use_gemme': True,  # Will fail (stub)
            'use_priors': True,
            'priors_yaml': 'data/priors/priors_petase_2024_2025.yaml',
        }

        # Should complete despite GEMME failing
        run_pipeline(test_fasta, temp_outdir, config)

        pred_path = os.path.join(temp_outdir, 'predictions.csv')
        assert os.path.exists(pred_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
