"""Per-scenario synthetic response discrepancies; no aggregate engine ranking."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    report=json.loads(args.report.read_text())
    if report['verification']['outcomes_reproduced'] != 30 or report['observed_comparison_complete'] != 30:
        parser.error('This complete-cohort figure requires all30 observable comparisons')
    profiles=[('mujoco-imp09-500us','MuJoCo impedance0.9','#0072B2'),
              ('mujoco-imp0001-500us','MuJoCo impedance0.001','#009E73'),
              ('superdex-load-damping-500us','SuperDex load damping','#D55E00')]
    fig,axes=plt.subplots(2,1,figsize=(11,7),layout='constrained',sharex=True)
    plt.rcParams.update({'font.size':10})
    for profile,label,color in profiles:
        rows=sorted((r for r in report['results'] if r['profile']==profile),key=lambda r:r['seed'])
        if len(rows)!=10:
            parser.error('Missing paired scenarios')
        for ax,key in zip(axes,('worst_window_rms_m','peak_error_m')):
            ax.plot(range(10),[r[key]*1e6 for r in rows],'o',color=color,label=label)
    for ax,limit,ylabel in zip(axes,(10,25),('Worst positive-load window RMS (µm)','Peak positive-load error (µm)')):
        ax.axhline(limit,ls='--',color='#555555',label=f'Existing synthetic target: <{limit} µm')
        ax.set(yscale='log',ylabel=ylabel);ax.grid(alpha=.2)
    handles, labels = axes[0].get_legend_handles_labels()
    labels[-1] = 'Dashed: existing RMS <10 / peak <25 µm targets'
    fig.legend(handles, labels, loc='outside lower center', ncol=2, fontsize=9)
    axes[1].set_xticks(range(10),[f'{i:02d}' for i in range(10)])
    axes[1].set_xlabel('Seed suffix (20261005xx); identical mass/size per column')
    fig.suptitle('Prospective mass/size transfer with unchanged nominal mappings\n30 paired episodes: 0 combined passes; all failures retained. Not hardware accuracy.',fontsize=12)
    fig.savefig(args.output,dpi=170,bbox_inches='tight')
    plt.close(fig)


if __name__=='__main__':
    main()
