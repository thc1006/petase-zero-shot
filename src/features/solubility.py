from Bio.SeqUtils.ProtParam import ProteinAnalysis
def solubility_proxy_scores(seqs, cfg):
    out = {}
    for sid, s in seqs:
        p = ProteinAnalysis(s)
        gravy = p.gravy()
        aro = p.aromaticity()
        pi = p.isoelectric_point()
        aa = p.count_amino_acids()
        pos = aa.get('K',0)+aa.get('R',0)
        neg = aa.get('D',0)+aa.get('E',0)
        charge_balance = (pos-neg)/max(1,len(s))
        length_penalty = max(0, len(s)-300)*0.001
        score = (-gravy) + (-0.5*aro) + (0.5-abs(charge_balance)) - length_penalty
        out[sid] = float(score)
    return out
