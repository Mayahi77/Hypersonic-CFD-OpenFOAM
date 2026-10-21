#!/usr/bin/env python3
"""Audit two saved ASCII v1706 cases, without writing into them.
Usage: python3 scripts/audit_fields.py COARSE_RESULTS FINE_RESULTS [--output DIR]
Dependencies: numpy. No CFD solver is invoked.
"""
import argparse
import json
import re
from pathlib import Path
import numpy as np


def foam_list(path):
    s = Path(path).read_text()
    s = re.sub(r'/\*.*?\*/|//[^\n]*', '', s, flags=re.S)
    s = s[s.index('}') + 1:]
    m = re.search(r'(\d+)\s*\(', s)
    return int(m[1]), s[m.end():s.rfind(')')]


def values(path, count=None):
    s = Path(path).read_text()
    m = re.search(r'internalField\s+nonuniform\s+List<\w+>\s+(\d+)\s*\((.*?)\)\s*;', s, re.S)
    if m:
        a = np.fromstring(m[2].replace('(', ' ').replace(')', ' '), sep=' ')
        a = a.reshape(int(m[1]), -1).squeeze()
        if count is not None and len(a) != count:
            raise ValueError('Field count does not match mesh: ' + str(path))
        return a
    m = re.search(r'internalField\s+uniform\s+([^;]+);', s)
    if not m or count is None:
        raise ValueError('Unsupported field: ' + str(path))
    a = np.fromstring(m[1].replace('(', ' ').replace(')', ' '), sep=' ')
    return np.full(count, a[0]) if len(a) == 1 else np.tile(a, (count, 1))


def mesh(case):
    root = case / 'constant/polyMesh'
    n, s = foam_list(root / 'points')
    pts = np.fromstring(s.replace('(', ' ').replace(')', ' '), sep=' ').reshape(n, 3)
    n, s = foam_list(root / 'faces')
    faces = [np.fromstring(x, sep=' ', dtype=int) for x in re.findall(r'\d+\s*\(([^)]*)\)', s)]
    if len(faces) != n:
        raise ValueError('Unsupported face encoding')
    own = np.fromstring(foam_list(root / 'owner')[1], sep=' ', dtype=int)
    nei = np.fromstring(foam_list(root / 'neighbour')[1], sep=' ', dtype=int)
    nc = int(own.max()) + 1
    vol = np.zeros(nc)
    for i, f in enumerate(faces):
        p = pts[f]
        sf = np.cross(p, np.roll(p, -1, axis=0)).sum(axis=0) / 2
        q = sf @ p.mean(axis=0) / 3
        vol[own[i]] += q
        if i < len(nei):
            vol[nei[i]] -= q
    if not np.all(vol > 0):
        raise ValueError('Nonpositive volume')
    boundary = (root / 'boundary').read_text()
    b = re.search(r'\bwedgeBack\s*\{([^}]+)', boundary)[1]
    start = int(re.search(r'startFace\s+(\d+)', b)[1])
    nf = int(re.search(r'nFaces\s+(\d+)', b)[1])
    ids = np.arange(start, start + nf)
    if nf != nc or len(np.unique(own[ids])) != nc:
        raise ValueError('Expected one wedge face for each cell')
    polys = []
    for i in ids:
        p = pts[faces[i]]
        polys.append(np.column_stack([p[:, 0], np.linalg.norm(p[:, 1:], axis=1)]))
    return nc, vol, polys, own[ids]


def audit(case):
    nc, vol, polys, ids = mesh(case)
    times = sorted([p.name for p in case.iterdir() if p.is_dir() and re.fullmatch(r'\d+(?:\.\d+)?', p.name)], key=float)
    rows, previous = [], None
    for t in times:
        fields = {f: values(case / t / f, nc) for f in ['T', 'p', 'rho', 'U'] if (case / t / f).exists()}
        row = {'time': float(t)}
        for f, a in fields.items():
            if not np.isfinite(a).all() or (f != 'U' and not np.all(a > 0)):
                raise ValueError('Invalid saved data: ' + str(case / t / f))
            row[f + '_min'] = float(a.min())
            row[f + '_max'] = float(a.max())
            if previous is not None and f in previous:
                w = vol if a.ndim == 1 else vol[:, None]
                row[f + '_relative_L2_change'] = float(np.sqrt(np.sum(w * (a - previous[f])**2) / np.sum(w * a**2)))
        rows.append(row)
        previous = fields
    return {'cells': nc, 'times': times, 'history': rows}, polys, ids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('coarse', type=Path)
    parser.add_argument('fine', type=Path)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'results')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    records = {name: audit(getattr(args, name).resolve())[0] for name in ['coarse', 'fine']}
    (args.output / 'audit.json').write_text(json.dumps(records, indent=2) + '\n')
    print('Verified saved fields for both cases; wrote audit.json')

if __name__ == '__main__':
    main()
