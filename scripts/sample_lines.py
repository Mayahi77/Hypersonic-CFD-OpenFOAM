#!/usr/bin/env python3
"""Sample p and T on (-1,.375,0) -> (0,.375,0) using temporary case copies.
Usage: python3 scripts/sample_lines.py COARSE_RESULTS FINE_RESULTS [--time 0.01]
Requires sourced OpenFOAM v1706 and numpy. Does not run a solver.
"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('coarse', type=Path)
parser.add_argument('fine', type=Path)
parser.add_argument('--time', default='0.01')
parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'results')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
data = {}
for name in ['coarse', 'fine']:
    (args.output/name).mkdir(parents=True, exist_ok=True)
for name in ['coarse', 'fine']:
    source = getattr(args, name).resolve()
    with tempfile.TemporaryDirectory(prefix='hypersonic-line-') as folder:
        case = Path(folder)
        for sub in ['constant', 'system', args.time]:
            shutil.copytree(source/sub, case/sub)
        shutil.copy2(Path(__file__).with_name('lineSample'), case/'system/lineSample')
        run = subprocess.run(['postProcess', '-case', str(case), '-time', args.time,
                              '-fields', '(p T)', '-func', 'lineSample'],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if run.returncode or 'FOAM Warning' in run.stdout or 'FOAM FATAL' in run.stdout:
            raise RuntimeError(run.stdout)
        raw = case/'postProcessing/lineSample'/args.time/'upstream_T_p.xy'
        a = np.loadtxt(raw)
        expected_x = np.linspace(-1, 0, 501)
        assert a.shape == (501, 3) and np.allclose(a[:, 0], expected_x, atol=1e-10)
        assert np.isfinite(a).all() and np.all(a[:, 1:] > 0)
        csv = np.column_stack([a[:, 0], np.full(501, .375), np.zeros(501), a[:, 2], a[:, 1]])
        np.savetxt(args.output/name/'line.csv', csv, delimiter=',', header='x_m,y_m,z_m,p_Pa,T_K', comments='', fmt='%.9g')
        data[name] = a
(args.output/'line_method.json').write_text(json.dumps({
    'point_1_m': [-1, .375, 0], 'point_2_m': [0, .375, 0], 'time_s': float(args.time),
    'samples': 501, 'method': 'OpenFOAM v1706 sampledSets, uniform, cellPoint interpolation',
    'endpoint_note': 'P2 is on the front annular wall. It is a boundary limit, not a fluid point inside the solid.',
    'pressure_units': 'Pa', 'temperature_units': 'K'
}, indent=2)+'\n')
print('Exported 501 matched pressure and temperature samples per case; no plots generated.')
