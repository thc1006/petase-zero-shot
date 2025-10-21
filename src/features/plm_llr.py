from typing import List, Tuple
def plm_activity_scores(seqs:List[Tuple[str,str]], cfg):
    try:
        import torch, esm
        name = cfg.get("plm_model","esm2_t30_150M_UR50D")
        device = "cuda" if cfg.get("device","auto")=="cuda" and torch.cuda.is_available() else "cpu"
        model, alphabet = esm.pretrained.load_model_and_alphabet(name)
        model.eval(); model = model.to(device)
        batch_converter = alphabet.get_batch_converter()
        labels, strings = zip(*seqs)
        batch = list(zip(labels, strings))
        _, _, toks = batch_converter(batch)
        toks = toks.to(device)
        L = toks.size(1)
        pll = 0.0
        with torch.no_grad():
            for pos in range(1, L-1):  # skip BOS/EOS
                masked = toks.clone()
                masked[:, pos] = alphabet.mask_idx
                out = model(masked, repr_layers=[], return_contacts=False)
                logits = out["logits"][:, pos, :]
                true_tok = toks[:, pos]
                ll = torch.log_softmax(logits, dim=-1).gather(1, true_tok.view(-1,1)).squeeze(1)
                if isinstance(pll, float): pll = ll
                else: pll += ll
        pll = pll / max(1,(L-2))
        return {lab: float(-pll[i].item()) for i, lab in enumerate(labels)}
    except Exception:
        # Fallback if fair-esm not installed
        return {sid: 0.0 for sid,_ in seqs}

def plm_perplexity_proxy(seqs:List[Tuple[str,str]], cfg):
    try:
        import math, torch, esm
        name = cfg.get("plm_model","esm2_t30_150M_UR50D")
        device = "cuda" if cfg.get("device","auto")=="cuda" and torch.cuda.is_available() else "cpu"
        model, alphabet = esm.pretrained.load_model_and_alphabet(name)
        model.eval(); model = model.to(device)
        batch_converter = alphabet.get_batch_converter()
        labels, strings = zip(*seqs)
        batch = list(zip(labels, strings))
        _, _, toks = batch_converter(batch)
        toks = toks.to(device)
        L = toks.size(1)
        pll = 0.0
        with torch.no_grad():
            for pos in range(1, L-1):
                masked = toks.clone()
                masked[:, pos] = alphabet.mask_idx
                out = model(masked, repr_layers=[], return_contacts=False)
                logits = out["logits"][:, pos, :]
                true_tok = toks[:, pos]
                ll = torch.log_softmax(logits, dim=-1).gather(1, true_tok.view(-1,1)).squeeze(1)
                if isinstance(pll, float): pll = ll
                else: pll += ll
        pll = pll / max(1,(L-2))
        import torch
        perp = torch.exp(-pll)
        return {lab: float(-perp[i].item()) for i, lab in enumerate(labels)}
    except Exception:
        return {sid: 0.0 for sid,_ in seqs}
