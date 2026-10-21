#!/usr/bin/env python3
"""Read-only audit of original logs, input agreement, and MPI reconstruction.
Usage: python3 scripts/verify_sources.py COARSE_CASE FINE_CASE
"""
import json
import re
import sys
from pathlib import Path
import numpy as np
from audit_fields import foam_list, values
coarse, fine = [Path(s).resolve() for s in sys.argv[1:3]]
out = {}
files = ['0/U', '0/p', '0/T', 'constant/thermophysicalProperties', 'constant/turbulenceProperties',
         'system/controlDict', 'system/fvSchemes', 'system/fvSolution']
out['identical_case_inputs'] = {f: (coarse/f).read_bytes() == (fine/f).read_bytes() for f in files}
for name, case, logfile in [('coarse', coarse, 'log.rhoCentralFoam'), ('fine', fine, 'log.parallel')]:
    log = (case/logfile).read_text()
    co = np.array(re.findall(r'Mean and max Courant Numbers = (\S+) (\S+)', log), float)
    times = re.findall(r'^Time = (\S+)', log, re.M)
    out[name] = {
        'solver_log': logfile,
        'nProcs': int(re.search(r'nProcs\s*:\s*(\d+)', log)[1]),
        'timestep_reports': len(times), 'final_logged_time': float(times[-1]),
        'maximum_logged_Co': float(co[:, 1].max()),
        'normal_End_marker': bool(re.search(r'^End\s*$', log, re.M)),
        'warning_or_error_lines': [l for l in log.splitlines() if re.search(r'FOAM FATAL|FOAM Warning|\bnan\b|^.*[Ss]ignal.*floating point exception', l)]
    }
# Each root field is checked against every processor cell using global addressing.
# This catches stale copied coarse results and incomplete/stale reconstruction.
procs = sorted(fine.glob('processor[0-9]*'))
if len(procs) != 4:
    raise ValueError('Expected four source processor directories')
nc = 20892
seen = np.zeros(nc, int)
address = []
for proc in procs:
    n, s = foam_list(proc/'constant/polyMesh/cellProcAddressing')
    a = np.fromstring(s, sep=' ', dtype=int)
    assert len(a) == n
    seen[a] += 1
    address.append(a)
assert np.all(seen == 1)
checks = []
for time in sorted([p.name for p in fine.iterdir() if p.is_dir() and re.fullmatch(r'\d*\.?\d+', p.name) and p.name != '0'], key=float):
    for field in ['p', 'T', 'rho', 'U']:
        full = values(fine/time/field, nc)
        max_abs = 0.0
        for proc, a in zip(procs, address):
            part = values(proc/time/field, len(a))
            max_abs = max(max_abs, float(np.max(np.abs(full[a]-part))))
        checks.append({'time': float(time), 'field': field, 'max_abs_difference': max_abs})
out['reconstruction'] = {'all_cells_covered_once': True, 'checked_field_snapshots': len(checks),
                          'maximum_absolute_difference': max(c['max_abs_difference'] for c in checks), 'checks': checks}
print(json.dumps(out, indent=2))
