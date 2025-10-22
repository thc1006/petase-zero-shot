"""
Download ProteinGym DMS benchmark data for correlation analysis.

ProteinGym provides Deep Mutational Scanning (DMS) assays with experimental
fitness measurements for protein variants. We'll use this to:
1. Validate our zero-shot predictions
2. Tune ensemble weights for optimal Spearman correlation
3. Identify PETase-relevant assays if available

Dataset: ProteinGym v1 (DMS substitutions)
Source: Hugging Face datasets (OATML-Markslab/ProteinGym_v1)
"""

import os
import pandas as pd
from datasets import load_dataset


def download_proteingym():
    """
    Download ProteinGym DMS substitutions dataset.

    Returns:
        Dataset object with DMS assays
    """
    print("[INFO] Downloading ProteinGym DMS substitutions...")

    # Load from Hugging Face
    dataset = load_dataset("OATML-Markslab/ProteinGym_v1", name="DMS_substitutions")

    print(f"[INFO] Dataset loaded: {dataset}")
    print(f"[INFO] Keys: {list(dataset.keys())}")

    return dataset


def explore_dataset(dataset):
    """
    Explore ProteinGym dataset structure and content.

    Args:
        dataset: Hugging Face dataset object
    """
    print("\n[INFO] Exploring dataset structure...")

    # Get first split (usually 'train' or 'test')
    split_name = list(dataset.keys())[0]
    data = dataset[split_name]

    print(f"\n[INFO] Split '{split_name}' has {len(data)} entries")
    print(f"[INFO] Column names: {data.column_names}")

    # Show first few examples
    print("\n[INFO] First 3 examples:")
    for i in range(min(3, len(data))):
        print(f"\nExample {i+1}:")
        for key, value in data[i].items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {value[:100]}...")
            else:
                print(f"  {key}: {value}")

    return data


def search_petase_assays(data):
    """
    Search for PETase-related assays in ProteinGym.

    Args:
        data: ProteinGym dataset split
    """
    print("\n[INFO] Searching for PETase/cutinase-related assays...")

    # Convert to pandas for easier searching
    df = data.to_pandas()

    # Search keywords
    keywords = ['petase', 'pet', 'cutinase', 'ideonella', 'thermobifida', 'plastic']

    found_assays = []
    for keyword in keywords:
        # Search in protein name, DMS_id, or other text fields
        for col in df.columns:
            if df[col].dtype == 'object':  # String columns
                matches = df[df[col].astype(str).str.contains(keyword, case=False, na=False)]
                if not matches.empty:
                    found_assays.extend(matches.to_dict('records'))
                    print(f"[FOUND] '{keyword}' in column '{col}': {len(matches)} assays")

    if found_assays:
        print(f"\n[SUCCESS] Found {len(found_assays)} PETase-related assays!")
        for i, assay in enumerate(found_assays[:5]):
            print(f"\nAssay {i+1}:")
            print(f"  ID: {assay.get('DMS_id', 'N/A')}")
            print(f"  Protein: {assay.get('UniProt_ID', 'N/A')}")
            print(f"  Description: {str(assay.get('DMS_phenotype', ''))[:100]}")
    else:
        print("[INFO] No direct PETase assays found (expected - PETase is niche)")
        print("[INFO] Will use general protein stability/activity assays for validation")

    return df


def save_summary(data, outdir='data/proteingym'):
    """
    Save ProteinGym dataset summary for analysis.

    Args:
        data: ProteinGym dataset split
        outdir: Output directory
    """
    os.makedirs(outdir, exist_ok=True)

    df = data.to_pandas()

    # Save summary statistics
    summary_path = os.path.join(outdir, 'proteingym_summary.csv')
    summary = pd.DataFrame({
        'total_assays': [len(df)],
        'total_columns': [len(df.columns)],
        'columns': [', '.join(df.columns)],
    })
    summary.to_csv(summary_path, index=False)
    print(f"\n[OK] Saved summary to {summary_path}")

    # Save first 100 rows as sample
    sample_path = os.path.join(outdir, 'proteingym_sample.csv')
    df.head(100).to_csv(sample_path, index=False)
    print(f"[OK] Saved sample (100 rows) to {sample_path}")

    # Save full dataset
    full_path = os.path.join(outdir, 'proteingym_dms_full.parquet')
    df.to_parquet(full_path, index=False)
    print(f"[OK] Saved full dataset to {full_path}")

    return df


if __name__ == "__main__":
    print("="*70)
    print(" ProteinGym DMS Benchmark Download")
    print("="*70)

    # Download dataset
    dataset = download_proteingym()

    # Explore structure
    data = explore_dataset(dataset)

    # Search for PETase assays
    df = search_petase_assays(data)

    # Save to disk
    save_summary(data)

    print("\n[COMPLETE] ProteinGym download finished!")
    print("\nNext steps:")
    print("1. Select representative DMS assays for benchmarking")
    print("2. Run pipeline on ProteinGym sequences")
    print("3. Calculate Spearman correlations with experimental data")
    print("4. Tune ensemble weights to maximize correlation")
