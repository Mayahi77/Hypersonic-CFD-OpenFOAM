"""Package existing ParaView PNGs as GIFs and a mesh comparison; no plotting.
Usage: python3 scripts/pack_media.py [RESULTS_DIRECTORY]
Requires Pillow. Refuses missing media; never fabricates simulation frames.
"""
from pathlib import Path
import sys
from PIL import Image, ImageSequence
root = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'results'
meshes = []
for name in ['coarse', 'fine']:
    paths = sorted((root/name/'frames').glob('frame_*.png'))
    if len(paths) < 2:
        raise ValueError('At least two actual ParaView frames required: '+name)
    frames = [Image.open(p).convert('RGB') for p in paths]
    frames = [im.resize((1000, round(im.height*1000/im.width)), getattr(Image, 'Resampling', Image).LANCZOS) for im in frames]
    montage = Image.new('RGB', (250*len(frames), frames[0].height//4))
    for i, frame in enumerate(frames):
        montage.paste(frame.resize((250, montage.height)), (i*250, 0))
    palette = montage.quantize(colors=256)
    frames = [im.quantize(palette=palette, dither=getattr(Image, 'Dither', Image).NONE) for im in frames]
    target = root/name/'animation.gif'
    frames[0].save(target, save_all=True, append_images=frames[1:], duration=[80]*(len(frames)-1)+[800], loop=0, optimize=True, disposal=2)
    with Image.open(target) as gif:
        assert gif.n_frames == len(paths)
        for frame in ImageSequence.Iterator(gif): frame.load()
    print(name, len(paths), 'frames;', target.stat().st_size, 'bytes')
    meshes.append(Image.open(root/name/'mesh.png').convert('RGB'))
assert meshes[0].size == meshes[1].size
combined = Image.new('RGB', (meshes[0].width*2, meshes[0].height), 'white')
combined.paste(meshes[0], (0,0));combined.paste(meshes[1], (meshes[0].width,0))
combined.save(root/'mesh_comparison.png', optimize=True)
