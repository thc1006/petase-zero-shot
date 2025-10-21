import os, pandas as pd, matplotlib.pyplot as plt
def plot_distributions(df, outdir):
    for col in ['activity_score','stability_score','expression_score']:
        plt.figure()
        df[col].hist(bins=20)
        plt.title(col)
        plt.xlabel('score'); plt.ylabel('count')
        fp = os.path.join(outdir, f'{col}_hist.png')
        plt.savefig(fp, bbox_inches='tight'); plt.close()
