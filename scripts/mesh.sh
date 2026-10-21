#!/usr/bin/env bash
# Run only on a fresh portfolio case: never replaces an existing mesh.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
case_name=${1:?Usage: mesh.sh coarse|fine}
case "$case_name" in
  coarse) geo=cylinder2D.geo ;;
  fine) geo=cylinder2DFine.geo ;;
  *) echo 'Choose coarse or fine' >&2; exit 2 ;;
esac
case_dir="$root/cases/$case_name"
if [ -e "$case_dir/constant/polyMesh" ]; then
  echo "Mesh already exists in $case_dir; use a fresh checkout/copy." >&2; exit 1
fi
cd "$case_dir"
# Gmsh 4.4.1 ignored these newer option names in the historical fine file.
# Remove them explicitly to reproduce the effective original mesh settings.
sed '/^Mesh\.MeshSizeFromPoints =/d; /^Mesh\.MeshSizeFromCurvature =/d; /^Mesh\.MeshSizeExtendFromBoundary =/d' "$root/geometry/$geo" > mesh-input.geo
gmsh mesh-input.geo -3 -format msh2 -o mesh.msh > log.gmsh 2>&1
gmshToFoam mesh.msh > log.gmshToFoam 2>&1
python3 "$root/scripts/set_patch_types.py" constant/polyMesh/boundary
checkMesh > log.checkMesh 2>&1
cat log.checkMesh
if ! grep -q 'Mesh OK' log.checkMesh; then exit 1; fi
