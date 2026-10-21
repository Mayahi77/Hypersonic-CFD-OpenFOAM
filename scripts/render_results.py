#!/usr/bin/env python3
"""Render actual saved wedge cells and OpenFOAM line CSVs; never runs CFD.
Usage: python3 scripts/render_results.py COARSE_RESULTS FINE_RESULTS
Requires numpy, matplotlib, Pillow. Outputs go to the portfolio results directory.
"""
import argparse
import io
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle
from PIL import Image, ImageSequence
from audit_fields import mesh, values

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('coarse', type=Path)
parser.add_argument('fine', type=Path)
parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1]/'results')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
records = json.loads((args.output/'audit.json').read_text())


def axes(ax, title):
    ax.set(xlim=(-.8, 2), ylim=(0, 1.4), xlabel='Axial position x (m)', ylabel='Radius r (m)', title=title)
    ax.set_aspect('equal')
    ax.add_patch(Rectangle((0,.25), 1,.25, facecolor='#263343', edgecolor='white', linewidth=.8, zorder=5))


meshes = []
for name in ['coarse', 'fine']:
    case = getattr(args,name).resolve()
    nc, vol, polys, ids = mesh(case)
    meshes.append(polys)
    folder = args.output/name
    folder.mkdir(exist_ok=True)
    times = records[name]['times']
    frames = []
    for field, label, limits, cmap, filename in [
        ('p','Pressure (Pa)',(0,40000),'viridis','pressure.png'),
        ('T','Temperature (K)',(200,3000),'inferno','temperature.png')]:
        fig, ax = plt.subplots(figsize=(10,5.8), dpi=100)
        axes(ax,'')
        pc = PolyCollection(polys, array=np.zeros(len(ids)), cmap=cmap, clim=limits,
                            edgecolors='none', antialiaseds=False)
        ax.add_collection(pc)
        fig.colorbar(pc, ax=ax, fraction=.035, pad=.035, label=label)
        fig.subplots_adjust(left=.08,right=.90,bottom=.13,top=.90)
        for t in (times if field=='T' else [times[-1]]):
            pc.set_array(values(case/t/field,nc)[ids])
            ax.set_title(name.capitalize()+' | '+format(nc,',')+' cells | '+label+' | t = %.4f s'%float(t))
            if t==times[-1]:fig.savefig(folder/filename,dpi=170)
            if field=='T':
                buf=io.BytesIO();fig.savefig(buf,format='png',dpi=100);buf.seek(0)
                with Image.open(buf) as im:frames.append(im.convert('RGB').copy())
        plt.close(fig)
    # A shared palette within each GIF avoids frame-to-frame palette flicker.
    montage=Image.new('RGB',(250*len(frames),145))
    for i,frame in enumerate(frames):montage.paste(frame.resize((250,145)),(i*250,0))
    palette=montage.quantize(colors=256)
    frames=[im.quantize(palette=palette,dither=getattr(Image, 'Dither', Image).NONE) for im in frames]
    gifpath=folder/'animation.gif'
    frames[0].save(gifpath,save_all=True,append_images=frames[1:],loop=0,
                   duration=[80]*(len(frames)-1)+[800],optimize=True,disposal=2)
    with Image.open(gifpath) as gif:
        assert gif.n_frames==len(times)
        assert gif.info['loop']==0
        for frame in ImageSequence.Iterator(gif):frame.load()
    print(name,len(times),'frames;',gifpath.stat().st_size,'bytes',flush=True)

fig,axs=plt.subplots(1,2,figsize=(14,5),constrained_layout=True)
for ax,name,polys in zip(axs,['coarse','fine'],meshes):
    axes(ax,name.capitalize()+' | '+format(records[name]['cells'],',')+' cells')
    ax.add_collection(PolyCollection(polys,facecolors='#edf3f7',edgecolors='#34485e',linewidths=.22))
fig.savefig(args.output/'mesh_comparison.png',dpi=160);plt.close(fig)
for column,field,unit in [(3,'pressure','Pa'),(4,'temperature','K')]:
    fig,ax=plt.subplots(figsize=(9,5),constrained_layout=True)
    for name,color in [('coarse','#2563a5'),('fine','#d44d26')]:
        a=np.loadtxt(args.output/name/'line.csv',delimiter=',',skiprows=1)
        assert a.shape==(501,5) and np.allclose(a[:,0],np.linspace(-1,0,501))
        ax.plot(a[:,0],a[:,column],label=name.capitalize(),color=color,lw=2)
    ax.set(xlabel='Axial position x (m)',ylabel=field.capitalize()+' ('+unit+')',xlim=(-1,0),
           title=field.capitalize()+' | y = 0.375 m, z = 0 | t = 0.01 s')
    ax.grid(alpha=.25);ax.legend()
    fig.savefig(args.output/('line_'+field+'.png'),dpi=170);plt.close(fig)
# Sampling line in physical coordinates, with the endpoint on the front wall.
nc,vol,polys,ids=mesh(args.fine)
fig,ax=plt.subplots(figsize=(10,5.8),constrained_layout=True)
axes(ax,'Sampling line | (-1, 0.375, 0) to (0, 0.375, 0)')
ax.set_xlim(-1.1,1.5)
pc=PolyCollection(polys,array=values(args.fine/'0.01/p',nc)[ids],cmap='viridis',
                  clim=(0,40000),edgecolors='none',antialiaseds=False)
ax.add_collection(pc)
ax.plot([-1,0],[.375,.375],color='white',lw=2,marker='o',markersize=5,zorder=8)
ax.text(-.98,.41,'P1',color='white',weight='bold');ax.text(-.10,.41,'P2',color='white',weight='bold')
fig.colorbar(pc,ax=ax,label='Pressure (Pa)',fraction=.04)
fig.savefig(args.output/'line_location.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
for name,record in records.items():
    rows=record['history'][2:]
    for ax,field in zip(axs,['p','T']):
        ax.semilogy([r['time'] for r in rows],[r[field+'_relative_L2_change']*100 for r in rows],'-o',label=name)
        ax.set(xlabel='Time (s)',ylabel='Relative change (%)',title=field+': volume-weighted change between saves')
        ax.grid(alpha=.25);ax.legend()
fig.savefig(args.output/'settling.png',dpi=150);plt.close(fig)
print('Field stills, mesh comparison, pressure/temperature line plots, line location, and settling plot exported.')
