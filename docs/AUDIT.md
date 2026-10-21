# Audit of the supplied Mach 5 cases

Only the current coarse and fine Mach 5 cases were used. No earlier Mach 9 case or modified solver was copied. Original source inputs and results were preserved. All mesh checking and field processing used disposable copies or newly generated portfolio meshes.

## Inputs and mesh provenance

All three initial fields (`U`, `p`, `T`), both thermophysical/turbulence dictionaries, and `controlDict`, `fvSchemes`, and `fvSolution` match byte for byte between cases. Fine additionally supplies a four-subdomain `scotch` decomposition. Consequently, the principal differences are mesh resolution, serial versus four-process execution, and the adaptive timestep sequence that results from the different meshes. The files prescribe identical initial conditions, physics, numerics, output cadence, and Courant limit.

The geometry sources were located separately: coarse `geometry/cylinder2D.geo` and fine `geometry/cylinder2DFine.geo`. The portfolio copies retain their original contents. Gmsh 4.4.1 reports three unknown options in the fine source: `Mesh.MeshSizeFromPoints`, `Mesh.MeshSizeFromCurvature`, and `Mesh.MeshSizeExtendFromBoundary`. It ignores these while generating the mesh. Renaming them to their older supported aliases activates settings that were not active in that historical run and produces a different mesh. Therefore `mesh.sh` filters those three lines from its generated working input, preserving the actual original behavior without changing the archived geometry source. It keeps the Gmsh defaults and both local size fields.

Both regenerated meshes match the original `points`, `faces`, `owner`, and `neighbour` arrays exactly after ignoring dictionary headers and whitespace. Cell counts alone were not used to establish this match. Fresh `checkMesh` checks pass with paired ±2.5° wedge patches, positive volumes, one connected region, and a total sector volume of 1.626 m³. Sanitized check summaries are supplied beside this document.

The fine source's old `log.checkMesh`, review report, and review metrics describe the coarse mesh and were inherited during copying. Its old serial solver log is also not the evidence for the fine parallel run. They were excluded. Fine run evidence comes from its actual mesh, `log.parallel`, processor directories, and root reconstructed fields.

## Reconstruction and completion

The fine root mesh has 20,892 cells and each nonzero root field has that cell count. Four `cellProcAddressing` arrays cover every global cell exactly once. All 20 nonzero times and all four saved fields (`p`, `T`, `rho`, `U`) were compared with the processor results using this addressing: **80 field snapshots, maximum absolute difference 0**. No further reconstruction was necessary. `verify_sources.py` reproduces the read-only comparison; `results/source_verification.json` contains its evidence.

Both logs report v1706 and end at 0.01 s with normal `End` markers. Coarse records 14,501 timestep reports; fine records 47,543 and finalizes its four-process parallel run. Peak logged Courant numbers are 0.20911 and 0.200016. Small overshoots of the requested 0.2 occur under adaptive stepping; these alone do not indicate solver failure. No actual fatal-error or warning messages were found in those two solver logs. The standard message enabling floating-point exception trapping is not an error.

All stored internal fields are finite. Saved pressure, temperature, and density are positive, including startup snapshots. This checks saved data, not every unsaved step. Initial `0/` contains only U, p, T; density is supplied by the thermodynamics at runtime. Both cases save nonzero data at 0.0005 s increments through 0.01 s.

| Diagnostic | Coarse | Fine |
|---|---:|---:|
| Final internal p range (Pa) | 114.053–36235.1 | 33.2743–32915.8 |
| Final internal T range (K) | 299.999–2004.95 | 299.986–1851.53 |
| All saved T range (K), including startup | 215.928–2365.2 | 228.833–2729.3 |
| Final-interval p relative L2 change | 0.14594% | 0.15480% |
| Final-interval T relative L2 change | 0.03817% | 0.04762% |

The relative L2 change is sqrt(sum(V × (last − previous)²) / sum(V × last²)). The interval is 0.0095–0.01 s. Positive cell volumes are computed from oriented planar mesh faces. These small changes are evidence of reduced evolution, with no assertion that all local flow features have settled. No aerodynamic forces or heat-transfer performance are claimed.

## Line extraction

Both cases use identical endpoints (−1, 0.375, 0) and (0, 0.375, 0), 501 uniform samples, and t = 0.01 s. OpenFOAM v1706 `sampledSets` with `cellPoint` interpolation produces the committed CSVs. Both contain all requested coordinates with no gaps. The second endpoint is on the front annular wall and should be interpreted as a boundary limit. These CSVs are numerical extracts, not ParaView screenshots. No pressure-gradient plots are requested or supplied.

For a ParaView Plot Over Line comparison, cell-to-point interpolation can differ from OpenFOAM `cellPoint`; the same extraction method must be used for both meshes. Keep a separate filename for ParaView-exported CSVs. No shock position is quantified from an on-screen estimate or from the interpolated sample spacing.

## Reproduction checks and remaining work

Tested: Gmsh 4.4.1 meshing, v1706 `gmshToFoam`, patch-type correction, `checkMesh` for both meshes, four-way `decomposePar`, all saved-field checks, MPI reconstruction consistency, and exact line extraction using `postProcess`. No new solver integration was performed. Public reproduction of the full flow solution still requires running the documented solver commands on a working OpenFOAM installation.

Delivered: Python-rendered pressure/temperature stills, both temperature GIFs, mesh-comparison image, and pressure/temperature line charts. The owner approved Python plotting after ParaFoam could not render. ParaFoam exports remain an optional follow-up; they are not claimed as delivered. See `VISUALIZATION.md` for methods and the environment blocker.
