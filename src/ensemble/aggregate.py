import numpy as np, pandas as pd
from scipy.stats import rankdata

def _to_df(seqs, channel_dict):
    sids = [sid for sid,_ in seqs]
    cols = {}
    for name, mapping in (channel_dict or {}).items():
        cols[name] = pd.Series({sid: mapping.get(sid, np.nan) for sid in sids})
    if not cols:
        return pd.DataFrame(index=sids)
    return pd.DataFrame(cols)

def robust_scale(df):
    med = df.median(skipna=True)
    mad = (df - med).abs().median(skipna=True).replace(0,1e-6)
    return (df - med) / mad

def fuse_one(seqs, channels, weights=None, scaling='robust'):
    df = _to_df(seqs, channels)
    if df.empty:
        return pd.Series([0.0]*len(seqs), index=[sid for sid,_ in seqs])
    if scaling=='robust':
        df = robust_scale(df)
    else:
        df = (df - df.mean()) / (df.std(ddof=0).replace(0,1e-6))
    ranks = df.apply(lambda c: rankdata(c, method='average'), axis=0)
    ranks = pd.DataFrame(ranks, index=df.index, columns=df.columns)
    w = pd.Series(weights or {c:1.0 for c in ranks.columns}).reindex(ranks.columns).fillna(0.0)
    if w.sum()==0: w = pd.Series(1.0, index=ranks.columns)
    w = w / w.sum()
    fused = (ranks * w).sum(axis=1)
    fused = (fused - fused.min())/(fused.max()-fused.min()+1e-9)
    return fused

def fuse_scores(seqs, scores, cfg):
    sids = [sid for sid,_ in seqs]
    W = (cfg or {}).get('weights', {})
    scaling = (cfg or {}).get('scaling','robust')
    out = {}
    out['activity_score'] = fuse_one(seqs, scores.get('activity', {}), W.get('activity',{}), scaling)
    out['stability_score'] = fuse_one(seqs, scores.get('stability', {}), W.get('stability',{}), scaling)
    out['expression_score'] = fuse_one(seqs, scores.get('expression', {}), W.get('expression',{}), scaling)
    df = pd.DataFrame({'seq_id': sids})
    for k,v in out.items():
        df[k] = [float(v.loc[sid]) for sid in sids]
    return df
