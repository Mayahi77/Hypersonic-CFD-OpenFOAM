"""ParaView 5.7 automation for paraFoam --script or pvbatch.
Uses ParaView rendering and Plot Over Line; no matplotlib.
NOT executed successfully in the delivery environment: see docs/VISUALIZATION.md.
Environment: PORTFOLIO_COARSE, PORTFOLIO_FINE, PORTFOLIO_OUTPUT (optional).
Both input paths must be disposable copies with reconstructed saved fields.
"""
import os
from pathlib import Path
from paraview.simple import *

import paraview.simple as pvs
pvs._DisableFirstRenderCameraReset()
root = Path(__file__).resolve().parents[1]
out = Path(os.environ.get('PORTFOLIO_OUTPUT', str(root / 'results')))
readers = {}
for name, variable in [('coarse', 'PORTFOLIO_COARSE'), ('fine', 'PORTFOLIO_FINE')]:
    case = Path(os.environ[variable]).resolve()
    marker = case / 'portfolio.foam'
    marker.touch()
    reader = OpenFOAMReader(FileName=str(marker))
    reader.MeshRegions = ['internalMesh']
    reader.CellArrays = ['p', 'T']
    reader.UpdatePipelineInformation()
    readers[name] = reader
    folder = out / name
    folder.mkdir(parents=True, exist_ok=True)
    frames = folder / 'frames'
    frames.mkdir(exist_ok=True)
    section = Slice(Input=reader)
    section.SliceType = 'Plane'
    section.SliceType.Normal = [0, 0, 1]
    section.SliceType.Origin = [0, 0, 0]
    view = CreateView('RenderView')
    view.ViewSize = [1200, 700]
    view.UseColorPaletteForBackground = 0
    view.Background = [1, 1, 1]
    view.OrientationAxesVisibility = 0
    display = Show(section, view)
    text = Text()
    annotation = Show(text, view)
    annotation.Color = [0.1, 0.1, 0.1]
    annotation.FontSize = 16
    annotation.WindowLocation = 'Upper Left Corner'
    for field, limits, preset, filename in [('p', [0, 40000], 'Viridis (matplotlib)', 'pressure.png'),
                                            ('T', [200, 3000], 'Inferno (matplotlib)', 'temperature.png')]:
        ColorBy(display, ('CELLS', field))
        lut = GetColorTransferFunction(field)
        lut.ApplyPreset(preset, True)
        lut.RescaleTransferFunction(*limits)
        lut.AutomaticRescaleRangeMode = 'Never'
        display.SetScalarBarVisibility(view, True)
        bar = GetScalarBar(lut, view)
        bar.Title = 'Pressure (Pa)' if field == 'p' else 'Temperature (K)'
        bar.ComponentTitle = ''
        bar.TitleColor = [0.1, 0.1, 0.1]
        bar.LabelColor = [0.1, 0.1, 0.1]
        bar.TitleFontSize = 16
        bar.LabelFontSize = 14
        times = list(reader.TimestepValues) if field == 'T' else [0.01]
        for i, time in enumerate(times):
            view.ViewTime = time
            reader.UpdatePipeline(time)
            text.Text = name.capitalize() + ' | t = %.4f s' % time
            view.CameraParallelProjection = 1
            view.CameraPosition = [0.6, 0.7, 10]
            view.CameraFocalPoint = [0.6, 0.7, 0]
            view.CameraViewUp = [0, 1, 0]
            view.CameraParallelScale = 0.82
            Render(view)
            if field == 'T':
                SaveScreenshot(str(frames / ('frame_%03d.png' % i)), view)
            if abs(time - 0.01) < 1e-10:
                SaveScreenshot(str(folder / filename), view, ImageResolution=[1800, 1050])
        display.SetScalarBarVisibility(view, False)
    display.Representation = 'Surface With Edges'
    ColorBy(display, None)
    display.DiffuseColor = [0.88, 0.92, 0.96]
    display.EdgeColor = [0.15, 0.22, 0.3]
    text.Text = name.capitalize() + ' mesh'
    SaveScreenshot(str(folder / 'mesh.png'), view, ImageResolution=[1800, 1050])
# True ParaView Plot Over Line, identical endpoints and sample times.
lines = {}
for name, reader in readers.items():
    reader.UpdatePipeline(0.01)
    points = CellDatatoPointData(Input=reader)
    line = PlotOverLine(Input=points, Source='High Resolution Line Source')
    line.Source.Point1 = [-1, 0.375, 0]
    line.Source.Point2 = [0, 0.375, 0]
    line.Source.Resolution = 500
    line.UpdatePipeline(0.01)
    lines[name] = line
    SaveData(str(out / name / 'line_paraview.csv'), proxy=line)
for field, unit, filename in [('p', 'Pa', 'line_pressure.png'), ('T', 'K', 'line_temperature.png')]:
    chart = CreateView('XYChartView')
    chart.ViewSize = [1200, 700]
    chart.ViewTime = 0.01
    chart.ChartTitle = ('Pressure' if field == 'p' else 'Temperature') + ' | y = 0.375 m, z = 0 | t = 0.01 s'
    chart.BottomAxisTitle = 'Distance from P1 along x (m)'
    chart.LeftAxisTitle = ('Pressure' if field == 'p' else 'Temperature') + ' (' + unit + ')'
    for name, line in lines.items():
        series = Show(line, chart)
        series.UseIndexForXAxis = 0
        series.XArrayName = 'arc_length'
        series.SeriesVisibility = [field]
        series.SeriesLabel = [field, name.capitalize()]
        series.SeriesLineThickness = [field, '3']
    Render(chart)
    SaveScreenshot(str(out / filename), chart)
print('ParaView exports complete. Review outputs, then pack frames with pack_media.py.')
