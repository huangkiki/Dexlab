"""Render a continuous replay from recorded cutting states, without resimulation."""

import argparse
import hashlib
import json
from pathlib import Path

import imageio.v2 as imageio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

from dexlab.cutting_score import score_run


COLORS = np.array(['#c8bc98', '#358ab0', '#e39851'])


def box_faces(center, half):
    corners = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]) * half + center
    return [corners[index] for index in ([0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1],
                                        [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3])]


def phase(t):
    if t < .3:
        return 'Settle'
    if t < 1.6:
        return 'Cut with force-driven blade'
    if t < 2.2:
        return 'Withdraw blade'
    if t < 2.4:
        return 'Persistent cut after withdrawal'
    return 'Diagnostic impulse to right half'


def render(directory, output, stride=2, fps=25):
    directory, output = Path(directory), Path(output)
    score = score_run(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    output.mkdir(parents=True, exist_ok=True)
    with np.load(directory / 'states.npz', allow_pickle=False) as data:
        states = {key: data[key] for key in data.files}
    with np.load(directory / 'trace.npz', allow_pickle=False) as data:
        trace = {key: data[key] for key in data.files}
    config = manifest['config']
    dt = config['dt']
    half = 1000 * np.array(config['blade_half_size'])
    t = trace['time_s']
    reaction = np.linalg.norm(trace['material_reaction_n'], axis=1)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False})
    fig = plt.figure(figsize=(12, 7.2), dpi=100, facecolor='#f9fafb')
    scene = fig.add_axes([.01, .17, .62, .71], projection='3d')
    scene.set(xlim=(-38, 40), ylim=(-24, 24), zlim=(0, 105),
              xlabel='x (mm)', ylabel='y (mm)', zlabel='z (mm)')
    scene.set_box_aspect((78, 48, 105))
    scene.view_init(elev=22, azim=-65)
    scene.set_facecolor('#f9fafb')
    floor = Poly3DCollection([[[-38, -24, 0], [40, -24, 0], [40, 24, 0], [-38, 24, 0]]],
                             facecolor='#d8dce1', alpha=.6)
    scene.add_collection3d(floor)
    points = scene.scatter(*states['position'][0].T * 1000, s=16, c=COLORS[states['sides'][0]],
                           edgecolors='none', depthshade=True)
    blade = Poly3DCollection(box_faces(1000 * trace['blade_position_m'][0], half),
                             facecolor='#9aadb8', edgecolor='#3e5565', linewidth=.6, alpha=.72)
    scene.add_collection3d(blade)
    force = fig.add_axes([.68, .55, .28, .27])
    force.plot(t, reaction, color='#436e90', lw=1.5)
    force.set(xlim=(0, 3), ylabel='Material reaction (N)', xlabel='Physical time (s)')
    force.grid(alpha=.15)
    force_cursor = force.axvline(0, color='#da8153', lw=1)
    motion = fig.add_axes([.68, .2, .28, .24])
    motion.plot(t, trace['target_edge_m'][:, 2] * 1000, '--', color='#9a9a9a', label='Command')
    motion.plot(t, (trace['blade_position_m'][:, 2] - half[2] / 1000) * 1000,
                color='#436e90', label='Measured edge')
    motion.set(xlim=(0, 3), ylabel='Blade edge height (mm)', xlabel='Physical time (s)')
    motion.legend(frameon=False, fontsize=9, loc='upper left')
    motion.grid(alpha=.15)
    motion_cursor = motion.axvline(0, color='#da8153', lw=1)
    fig.text(.04, .955, 'DexLab / synthetic tofu halving', fontsize=21, weight='bold', color='#253748')
    fig.text(.04, .91, 'BladeMaster-inspired CPU reference | recorded particles and dynamic blade', color='#617181')
    status = fig.text(.05, .09, '', fontsize=12, color='#253748')
    fig.text(.05, .035, 'Blue / orange: persistent cut sides. After 2.4 s: external diagnostic impulse, not robot manipulation.',
             fontsize=10, color='#617181')
    selected = list(range(0, len(states['time']), stride))
    if selected[-1] != len(states['time']) - 1:
        selected.append(len(states['time']) - 1)
    with imageio.get_writer(output / 'replay.mp4', fps=fps, codec='libx264', quality=8,
                            macro_block_size=1, pixelformat='yuv420p') as writer:
        gif_frames = []
        for frame in selected:
            now = states['time'][frame]
            index = max(0, round(now / dt) - 1)
            points._offsets3d = tuple(states['position'][frame].T * 1000)
            points.set_color(COLORS[states['sides'][frame]])
            blade.set_verts(box_faces(1000 * trace['blade_position_m'][index], half))
            force_cursor.set_xdata([now, now])
            motion_cursor.set_xdata([now, now])
            status.set_text(f'{now:4.2f} s  /  {phase(now)}')
            fig.canvas.draw()
            rgb = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
            writer.append_data(rgb)
            gif_frames.append(rgb[::2, ::2])
        fig.savefig(output / 'poster.png', dpi=140, facecolor=fig.get_facecolor())
    imageio.mimsave(output / 'replay.gif', gif_frames, duration=1000 / fps, loop=0)
    plt.close(fig)
    provenance = {
        'source_artifacts': manifest['artifacts'],
        'renderer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'frames': len(selected), 'fps': fps, 'physical_duration_s': float(states['time'][-1]),
        'playback_duration_s': len(selected) / fps, 'score': score,
        'description': 'Continuous actual particle-state replay; no generated motion or surface reconstruction.',
        'artifacts': {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                      for name in ('replay.mp4', 'replay.gif', 'poster.png')},
    }
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    render(args.directory, args.output)


if __name__ == '__main__':
    main()
