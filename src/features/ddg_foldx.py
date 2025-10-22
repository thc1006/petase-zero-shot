"""
FoldX ΔΔG Stability Predictions

Uses FoldX BuildModel to predict protein stability changes (ΔΔG) for mutations.
Negative ΔΔG = stabilizing, Positive ΔΔG = destabilizing.

Key functions:
- ddg_foldx_scores(seqs, cfg): Main interface returning {seq_id: ddg_score}

Implementation following TDD principles (tests in tests/test_ddg.py).

References:
- FoldX 5 manual: http://foldxsuite.crg.eu/
- Schymkowitz et al., Nucleic Acids Res. 2005 (FoldX original paper)
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Dict
import shutil
import re


def _generate_mutation_list(wt_seq: str, mut_seq: str, chain: str = 'A') -> List[str]:
    """
    Generate FoldX mutation list from WT and mutant sequences.

    FoldX format: [WT_aa][Chain][Position][Mut_aa]
    Example: SA121E (Serine at position 121 of chain A mutated to Glutamate)

    Args:
        wt_seq: Wild-type amino acid sequence
        mut_seq: Mutant amino acid sequence
        chain: PDB chain identifier (default 'A')

    Returns:
        List of mutations in FoldX format (e.g., ["SA121E", "DA186H"])
    """
    if len(wt_seq) != len(mut_seq):
        raise ValueError(f"Sequence length mismatch: WT={len(wt_seq)}, Mut={len(mut_seq)}")

    mutations = []
    for i, (wt_aa, mut_aa) in enumerate(zip(wt_seq, mut_seq)):
        if wt_aa != mut_aa:
            # FoldX uses 1-indexed positions
            position = i + 1
            mutation = f"{wt_aa}{chain}{position}{mut_aa}"
            mutations.append(mutation)

    return mutations


def _parse_mutations_from_id(seq_id: str, chain: str = 'A', pdb_offset: int = 0) -> List[str]:
    """
    Parse mutation codes from FASTA sequence ID.

    Examples:
        "FAST_PETase|S121E_D186H_R224Q_N233K_R280E" -> ["SA121E", "DA186H", "RA224Q", "NA233K", "RA280E"]
        "Bhr_NMT|H218N_F222M_F243T" -> ["HA218N", "FA222M", "FA243T"]
        "IsPETase_WT|P0C395|Ideonella_sakaiensis" -> [] (no mutations)

    Args:
        seq_id: FASTA sequence ID containing mutation codes
        chain: PDB chain identifier (default 'A')
        pdb_offset: Offset to add to sequence positions for PDB numbering (default 0)
                    Example: If PDB starts at residue 30, offset = 29

    Returns:
        List of mutations in FoldX format (e.g., ["SA121E", "DA186H"])
    """
    # Pattern: [Single letter][1-4 digit number][Single letter]
    # Must be preceded by _ or | and followed by _ or end of string
    # Example: S121E, D186H, R224Q (from "...| S121E_D186H...")
    mutation_pattern = r'(?:^|[_|])([A-Z])(\d{1,4})([A-Z])(?=[_|]|$)'

    matches = re.findall(mutation_pattern, seq_id)

    mutations = []
    for wt_aa, position, mut_aa in matches:
        # Apply PDB offset to position
        pdb_position = int(position) + pdb_offset
        # FoldX format: [WT_aa][Chain][Position][Mut_aa]
        mutation = f"{wt_aa}{chain}{pdb_position}{mut_aa}"
        mutations.append(mutation)

    return mutations


def _create_individual_list(mutations: List[str], output_file: Path):
    """
    Create FoldX individual_list.txt file.

    Format: Each line contains comma-separated mutations ending with semicolon.
    Example:
        SA121E,DA186H,RA224Q;

    Args:
        mutations: List of mutations in FoldX format
        output_file: Path to write individual_list.txt
    """
    if not mutations:
        # Wild-type: empty mutation list
        content = ";\n"
    else:
        content = ",".join(mutations) + ";\n"

    output_file.write_text(content, encoding='utf-8')


def _run_foldx_buildmodel(
    pdb_path: str,
    mutation_file: Path,
    work_dir: str,
    foldx_exe: str = "tools/foldx/foldx_20251231.exe",
    timeout: int = 300
) -> Dict:
    """
    Run FoldX BuildModel command.

    IMPORTANT: FoldX must run from the FoldX directory (not temp directories).
    This function uses the FoldX installation directory as working directory.

    Args:
        pdb_path: Path to reference PDB structure
        mutation_file: Path to individual_list.txt
        work_dir: Output directory for FoldX results (files will be moved here after)
        foldx_exe: Path to FoldX executable (or WSL wrapper)
        timeout: Timeout in seconds (default 300 = 5 minutes)

    Returns:
        Dict with execution metadata (returncode, stdout, stderr)
    """
    # FoldX must run from its installation directory
    # Use tools/foldx/ as working directory
    foldx_dir = Path("tools/foldx").resolve()
    pdb_name = Path(pdb_path).name

    # Copy PDB to FoldX directory if not already there
    foldx_pdb = foldx_dir / pdb_name
    if not foldx_pdb.exists() or foldx_pdb != Path(pdb_path).resolve():
        shutil.copy(pdb_path, foldx_pdb)

    # Read mutation file content
    mutation_content = mutation_file.read_text(encoding='utf-8').strip()

    # Detect if using WSL wrapper and construct appropriate command
    if 'wsl' in foldx_exe.lower() or foldx_exe.endswith('.bat'):
        # WSL mode: Call Linux FoldX directly via WSL
        foldx_dir_wsl = str(foldx_dir).replace('\\', '/').replace('C:', '/mnt/c').replace('D:', '/mnt/d')
        foldx_linux = f"{foldx_dir_wsl}/foldx_20251231"

        # CRITICAL: Create individual_list.txt inside bash command to avoid WSL file copy issues
        # Construct WSL command - run from FoldX directory
        cmd = [
            "wsl", "bash", "-c",
            f"cd '{foldx_dir_wsl}' && echo '{mutation_content}' > individual_list.txt && '{foldx_linux}' --command=BuildModel --pdb={pdb_name} --mutant-file=individual_list.txt --numberOfRuns=1"
        ]
        run_cwd = None
    else:
        # Native Windows FoldX
        foldx_exe_abs = os.path.abspath(foldx_exe)
        cmd = [
            foldx_exe_abs,
            "--command=BuildModel",
            f"--pdb={pdb_name}",
            "--mutant-file=individual_list.txt",
            "--numberOfRuns=1",  # Using 1 run due to FoldX crash with multiple runs
        ]
        run_cwd = str(foldx_dir)

    try:
        result = subprocess.run(
            cmd,
            cwd=run_cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Move output files to work_dir for parsing
        if result.returncode == 0:
            for fxout_file in foldx_dir.glob("*.fxout"):
                shutil.move(str(fxout_file), Path(work_dir) / fxout_file.name)

        return {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            'returncode': -1,
            'stdout': '',
            'stderr': f'FoldX timeout after {timeout}s',
        }
    except FileNotFoundError:
        return {
            'returncode': -1,
            'stdout': '',
            'stderr': f'FoldX executable not found: {foldx_exe}',
        }


def _parse_foldx_output(work_dir: str) -> Dict[str, float]:
    """
    Parse FoldX output files to extract ΔΔG values.

    FoldX creates files:
    - Average_<PDB>.fxout: Contains average ΔΔG across runs
    - Dif_<PDB>.fxout: Contains detailed energy differences

    Args:
        work_dir: FoldX working directory

    Returns:
        Dict mapping mutation IDs to ΔΔG values
    """
    ddg_dict = {}

    # Look for Average_*.fxout files
    work_path = Path(work_dir)
    avg_files = list(work_path.glob("Average_*.fxout"))

    if not avg_files:
        # No output files found, return empty
        return ddg_dict

    # Parse first Average file (usually only one)
    avg_file = avg_files[0]

    try:
        lines = avg_file.read_text(encoding='utf-8').splitlines()

        for line in lines:
            if not line.strip() or line.startswith('#'):
                continue

            parts = line.split('\t')
            if len(parts) < 3:
                continue

            # Format: PDB_name    mutation_id    ddG    ...
            mutation_id = parts[1].strip()
            try:
                ddg_value = float(parts[2].strip())
                ddg_dict[mutation_id] = ddg_value
            except (ValueError, IndexError):
                continue

    except Exception as e:
        print(f"[WARN] Failed to parse FoldX output: {e}")

    return ddg_dict


def _get_pdb_range(pdb_path: str, chain: str = 'A') -> tuple:
    """
    Get the residue numbering range from PDB file.

    Args:
        pdb_path: Path to PDB structure file
        chain: Chain identifier

    Returns:
        Tuple of (first_residue, last_residue, offset)
        e.g., (30, 292, 29) means PDB numbered 30-292, offset +29
    """
    try:
        from Bio.PDB import PDBParser

        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_path)

        for model in structure:
            for pdb_chain in model:
                if pdb_chain.id == chain:
                    residue_numbers = []
                    for residue in pdb_chain:
                        if residue.id[0] == ' ':  # Standard residue
                            residue_numbers.append(residue.id[1])

                    if residue_numbers:
                        first_res = min(residue_numbers)
                        last_res = max(residue_numbers)
                        offset = first_res - 1
                        return (first_res, last_res, offset)
    except Exception as e:
        print(f"[WARN] Could not determine PDB range: {e}")

    return (1, 999999, 0)  # Default: no filtering


def _get_pdb_offset(pdb_path: str, chain: str = 'A') -> int:
    """
    Get the residue numbering offset from PDB file.

    PDB files often start numbering from a value > 1.
    This function returns (first_residue_number - 1).

    Args:
        pdb_path: Path to PDB structure file
        chain: Chain identifier

    Returns:
        Offset to add to sequence positions (e.g., 29 if PDB starts at residue 30)
    """
    try:
        from Bio.PDB import PDBParser

        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_path)

        for model in structure:
            for pdb_chain in model:
                if pdb_chain.id == chain:
                    for residue in pdb_chain:
                        if residue.id[0] == ' ':  # First standard residue
                            first_residue_num = residue.id[1]
                            offset = first_residue_num - 1
                            return offset
    except Exception as e:
        print(f"[WARN] Could not determine PDB offset: {e}")

    return 0  # Default: no offset


def _extract_wt_sequence_from_pdb(pdb_path: str, chain: str = 'A') -> str:
    """
    Extract wild-type amino acid sequence from PDB file.

    Args:
        pdb_path: Path to PDB structure file
        chain: Chain identifier to extract

    Returns:
        Wild-type amino acid sequence
    """
    try:
        from Bio.PDB import PDBParser
        from Bio.PDB.Polypeptide import protein_letters_3to1

        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_path)

        for model in structure:
            for pdb_chain in model:
                if pdb_chain.id == chain:
                    sequence = []
                    for residue in pdb_chain:
                        if residue.id[0] == ' ':  # Standard amino acid
                            resname_upper = residue.resname.upper()
                            if resname_upper in protein_letters_3to1:
                                aa = protein_letters_3to1[resname_upper]
                                sequence.append(aa)
                    return ''.join(sequence)

    except Exception as e:
        print(f"[WARN] Could not extract sequence from PDB: {e}")

    return None


def ddg_foldx_scores(seqs: List[Tuple[str, str]], cfg: dict) -> Dict[str, float]:
    """
    Calculate ΔΔG stability scores using FoldX BuildModel.

    Args:
        seqs: List of (seq_id, sequence) tuples
        cfg: Configuration dict with:
            - foldx_exe: Path to FoldX executable
            - foldx_pdb: Path to reference PDB structure
            - foldx_wt_seq: Wild-type sequence (optional, auto-extract from PDB)
            - foldx_timeout: Timeout per variant in seconds (default 300)
            - foldx_chain: PDB chain identifier (default 'A')

    Returns:
        Dict mapping seq_id to ΔΔG score (negative = stabilizing, positive = destabilizing)

    Example:
        >>> seqs = [("WT", "MNFP..."), ("S121E", "MNFP...")]
        >>> cfg = {'foldx_exe': 'tools/foldx/foldx_20251231.exe', 'foldx_pdb': 'tools/foldx/5XJH.pdb'}
        >>> ddg_foldx_scores(seqs, cfg)
        {'WT': 0.0, 'S121E': -1.23}
    """
    if not seqs:
        return {}

    # Extract configuration
    foldx_exe = cfg.get('foldx_exe', 'tools/foldx/foldx_20251231.exe')
    pdb_path = cfg.get('foldx_pdb', 'tools/foldx/5XJH.pdb')
    timeout = cfg.get('foldx_timeout', 300)
    chain = cfg.get('foldx_chain', 'A')

    # Check FoldX executable exists
    if not os.path.exists(foldx_exe):
        print(f"[ERROR] FoldX executable not found: {foldx_exe}")
        return {}

    # Check PDB exists
    if not os.path.exists(pdb_path):
        print(f"[ERROR] Reference PDB not found: {pdb_path}")
        return {}

    # Get wild-type sequence
    wt_seq = cfg.get('foldx_wt_seq')
    if not wt_seq:
        print("[INFO] Extracting WT sequence from PDB...")
        wt_seq = _extract_wt_sequence_from_pdb(pdb_path, chain)

    if not wt_seq:
        print("[ERROR] Could not determine wild-type sequence")
        return {}

    print(f"[INFO] Wild-type sequence: {len(wt_seq)} aa")

    # Get PDB residue numbering range
    first_res, last_res, pdb_offset = _get_pdb_range(pdb_path, chain)
    print(f"[INFO] PDB numbering: {first_res}-{last_res}")

    # Process each variant
    ddg_results = {}

    for seq_id, mut_seq in seqs:
        try:
            # Parse mutations from sequence ID
            # NOTE: Mutation codes in FASTA headers (e.g., S121E) already use PDB residue numbering!
            # Do NOT apply additional offset - they are PDB-compatible positions
            # (e.g., "FAST_PETase|S121E_D186H_R224Q_N233K_R280E")
            all_mutations = _parse_mutations_from_id(seq_id, chain, pdb_offset=0)

            # Filter mutations to only include those within PDB range
            mutations = []
            filtered_out = []
            for mut in all_mutations:
                # Extract position from mutation string (e.g., "SA150E" -> 150)
                pos_str = ''.join(filter(str.isdigit, mut))
                if pos_str:
                    pos = int(pos_str)
                    if first_res <= pos <= last_res:
                        mutations.append(mut)
                    else:
                        filtered_out.append(mut)

            if filtered_out:
                print(f"[WARN] {seq_id}: Filtered {len(filtered_out)} mutations outside PDB range: {', '.join(filtered_out)}")

            # Wild-type has ΔΔG = 0.0
            if not mutations:
                ddg_results[seq_id] = 0.0
                print(f"[INFO] {seq_id}: WT (ΔΔG = 0.0)")
                continue

            print(f"[INFO] {seq_id}: {len(mutations)} mutations - {', '.join(mutations[:5])}")

            # Create temp directory for FoldX
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create individual_list.txt
                mut_file = Path(tmpdir) / "individual_list.txt"
                _create_individual_list(mutations, mut_file)

                # Run FoldX BuildModel
                result = _run_foldx_buildmodel(
                    pdb_path=pdb_path,
                    mutation_file=mut_file,
                    work_dir=tmpdir,
                    foldx_exe=foldx_exe,
                    timeout=timeout
                )

                if result['returncode'] != 0:
                    print(f"[WARN] FoldX failed for {seq_id}: {result['stderr'][:200]}")
                    # Assign neutral ΔΔG for failed runs
                    ddg_results[seq_id] = 0.0
                    continue

                # Parse output
                ddg_dict = _parse_foldx_output(tmpdir)

                if ddg_dict:
                    # Take first result (usually only one entry)
                    ddg_value = list(ddg_dict.values())[0]
                    ddg_results[seq_id] = ddg_value
                    print(f"[INFO] {seq_id}: ΔΔG = {ddg_value:.2f} kcal/mol")
                else:
                    print(f"[WARN] No ΔΔG output for {seq_id}")
                    ddg_results[seq_id] = 0.0

        except Exception as e:
            print(f"[ERROR] Failed to process {seq_id}: {e}")
            ddg_results[seq_id] = 0.0

    return ddg_results
