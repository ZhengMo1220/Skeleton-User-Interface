import pyqtgraph as pg
from PyQt5.QtGui import QFont, QColor
from .analyze import PoseAnalyzer
import numpy as np

class GraphPlotter():
    def __init__(self, pose_analyzer: PoseAnalyzer, angle_name: str = "右手肘"):
        pg.setConfigOptions(foreground=QColor(113,148,116), antialias = True)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.angle_name = angle_name
        self.graph = pg.PlotWidget()
        self.pose_analyzer = pose_analyzer

    def _init_graph(self, frame_range: int) -> pg.PlotWidget:
        title = f'<span style="color: blue; font-size: 30px">{self.angle_name}角度 (度)</span>'
        self.graph.setTitle(f'{title}')
        font = QFont()
        font.setPixelSize(30)
        self.graph.addLegend(offset=(150, 5), labelTextSize="30pt")
        self.graph.setLabel('left', '<span style="font-size: 30px">角度 (度)</span>', color="blue")
        self.graph.setLabel('bottom', '<span style="font-size: 30px">幀</span>')
        self.graph.getAxis("bottom").setStyle(tickFont=font)
        self.graph.getAxis("left").setStyle(tickFont=font)
        self.graph.setXRange(0, frame_range - 1)
        self.graph.setYRange(0, 180)
        y_ticks = [(i, str(i)) for i in np.arange(0, 210, 30)]
        self.graph.getPlotItem().getAxis('left').setTicks([y_ticks])
        self.graph.getPlotItem().getAxis('left').setPen(color=QColor("blue"))
        self.graph.getPlotItem().getAxis('left').setTextPen(color=QColor("blue"))

    def updateGraph(self, frame_num: int):
        self.graph.clear()
        _, angle_info = self.pose_analyzer.get_frame_angle_data(frame_num, self.angle_name)
        try:
            angle_value = int(angle_info[0])
            title = f'<span style="color: blue; font-size: 30px">{self.angle_name}角度({int(angle_value):03}度)</span>'
        except TypeError:
            return
        self.graph.setTitle(f'{title}')
        kpt_times, kpt_angles = self.pose_analyzer.get_frame_angle_data(angle_name=self.angle_name)
        self.graph.plot(kpt_times, kpt_angles, pen='b')
        scatter = pg.ScatterPlotItem([frame_num], [angle_value], size=10, pen=pg.mkPen(None), brush=pg.mkBrush(255, 0, 0, 255))
        self.graph.addItem(scatter)

    def resize_graph(self, width, height):
        self.graph.resize(width, height)

    def setAngleName(self, angle_name):
        self.angle_name = angle_name

    def reset(self):
        self.graph = pg.PlotWidget()
