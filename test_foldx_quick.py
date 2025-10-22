#!/usr/bin/env python3
"""Quick test of FoldX mutation parsing fix."""

from src.features.ddg_foldx import _parse_mutations_from_id

# Test mutation parsing
test_cases = [
    ("FAST_PETase|S121E_D186H_R224Q_N233K_R280E", 5, ["SA121E", "DA186H", "RA224Q", "NA233K", "RA280E"]),
    ("Bhr_NMT|H218N_F222M_F243T", 3, ["HA218N", "FA222M", "FA243T"]),
    ("S238F_W159H|IsPETase_mutations", 2, ["SA238F", "WA159H"]),
    ("IsPETase_WT|P0C395|Ideonella_sakaiensis", 0, []),
    ("LCC_ICCG|I208C_G263C", 2, ["IA208C", "GA263C"]),
]

print("Testing FoldX mutation parsing...")
print("=" * 60)

all_passed = True
for seq_id, expected_count, expected_mutations in test_cases:
    mutations = _parse_mutations_from_id(seq_id, chain='A')
    passed = len(mutations) == expected_count and mutations == expected_mutations

    status = "[PASS]" if passed else "[FAIL]"
    print(f"\n{status} {seq_id}")
    print(f"  Expected: {expected_count} mutations - {expected_mutations}")
    print(f"  Got:      {len(mutations)} mutations - {mutations}")

    if not passed:
        all_passed = False

print("\n" + "=" * 60)
if all_passed:
    print("[SUCCESS] ALL TESTS PASSED! FoldX mutation parsing is working correctly.")
    print("\nNext: Test FoldX BuildModel on one variant...")
    print("Command: python -m src.cli --input data/real_sequences/petase_variants.fasta --outdir data/output_with_foldx --config config.yaml")
else:
    print("[ERROR] SOME TESTS FAILED. Check mutation parsing logic.")
