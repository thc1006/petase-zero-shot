import argparse, os, yaml
from src.pipelines.run_all import run_pipeline

def main():
    ap = argparse.ArgumentParser(description='PETase Zero‑Shot predictions')
    ap.add_argument('--input', required=True, help='FASTA path')
    ap.add_argument('--outdir', required=True, help='Output dir')
    ap.add_argument('--config', default='config.yaml', help='YAML config')
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    with open(args.config, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    run_pipeline(args.input, args.outdir, cfg)

if __name__ == '__main__':
    main()
