import os.path
import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel,
                             QScrollArea, QGridLayout, QPushButton, QFrame, QTabWidget, QSplitter)
from PyQt5 import QtCore
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree
from VASPparser import *

pg.setConfigOptions(antialias=True)


class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.plot = pg.PlotWidget()
        self.layout.addWidget(self.plot)

    def plot_data(self, data, color='b'):  # Add a parameter for color with default value 'b' (blue)
        self.plot.clear()
        for single_data in data:
            self.plot.plot(single_data, pen=pg.mkPen(color))  # Set the pen color

class GraphicsLayoutWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.graphlaywidget = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.graphlaywidget)
class VaspData():
    def __init__(self, dir):
        self.doscar = DOSCARparser(os.path.join(dir, "DOSCAR"))
        self.data_up = self.doscar.dataset_up
        self.data_down = self.doscar.dataset_down
        self.orbitals = self.doscar.orbitals
        self.e_fermi = self.doscar.efermi

        poscar = PoscarParser(os.path.join(dir, "POSCAR"))
        self.atoms_symb_and_num = poscar.symbol_and_number()
        self.number_of_atoms = poscar.number_of_atoms()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.create_data()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('DOSWave v.0.0.0')
        self.resize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        splitter = QSplitter()
        main_layout.addWidget(splitter)

        # Left tabs for plots
        left_tab_widget = QTabWidget()

        #DOS plot widgets
        self.plot_tab1_main = GraphicsLayoutWidget()
        self.plot_tab1_main.graphlaywidget.setBackground('w')
        self.plot_tab1 = self.plot_tab1_main.graphlaywidget.addPlot(row=0, col=2)
        self.plot_tab1_right = self.plot_tab1_main.graphlaywidget.addPlot(row=0, col=1)

        self.region = pg.LinearRegionItem(orientation='horizontal', brush=pg.mkBrush(255,235,14,100))
        self.region.setBounds([-20,15])
        self.region.setZValue(10)
        self.plot_tab1_right.addItem(self.region)

        def update():
            self.region.setZValue(10)
            self.plot_tab1.setYRange(*self.region.getRegion(), padding=0)

        def updateRegion():
            self.region.setRegion(self.plot_tab1_right.getViewBox().viewRange()[0])

        self.region.sigRegionChanged.connect(update)
        self.plot_tab1_right.sigYRangeChanged.connect(updateRegion)
        self.region.setRegion([1, 10])



        self.plot_tab2 = PlotWidget()
        self.plot_tab3 = PlotWidget()
        left_tab_widget.addTab(self.plot_tab1_main, "DOS")
        left_tab_widget.addTab(self.plot_tab2, "Structure")
        left_tab_widget.addTab(self.plot_tab3, "PARCHG/CHGCAR")
        splitter.addWidget(left_tab_widget)

        # Right tabs for GUI
        right_tab_widget = QTabWidget()
        param_tree_widget = QWidget()
        param_tree_layout = QVBoxLayout(param_tree_widget)

        self.param = Parameter.create(name='params', type='group', children=[
            {'name': 'Middle Index', 'type': 'int', 'value': 0, 'limits': (0, 15)}
        ])
        self.param_tree = ParameterTree()
        self.param_tree.setParameters(self.param, showTop=True)
        self.param.sigTreeStateChanged.connect(self.parameter_changed)
        param_tree_layout.addWidget(self.param_tree)

        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        # Left side of the scroll area for checkboxes
        self.checkboxes_widget = QWidget()
        self.checkboxes_layout = QVBoxLayout(self.checkboxes_widget)
        self.checkboxes_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_area_left = QScrollArea()  # New scroll area for checkboxes
        self.scroll_area_left.setWidgetResizable(True)
        self.scroll_area_left.setWidget(self.checkboxes_widget)
        self.scroll_area_left.setFrameShape(QFrame.NoFrame)
        self.scroll_layout.addWidget(self.scroll_area_left, 1, 1)

        label = QLabel("atoms:")
        self.checkboxes_layout.addWidget(label)

        self.atom_checkboxes = []
        for i in range(self.number_of_atoms):
            checkbox = QCheckBox(self.atoms_symb_and_num[i])
            if i == 1:
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.checkbox_changed)
            self.atom_checkboxes.append(checkbox)
            self.checkboxes_layout.addWidget(checkbox)

        # Right side for other content
        self.scroll_right_widget = QWidget()
        self.scroll_right_layout = QVBoxLayout(self.scroll_right_widget)
        self.scroll_right_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_layout.addWidget(self.scroll_right_widget,1, 2)

        label = QLabel("orbitals:")
        self.scroll_right_layout.addWidget(label)

        self.orbital_checkboxes = []
        for i in range(len(self.orbitals)):
            checkbox = QCheckBox(self.orbitals[i])
            if i == 1:
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.checkbox_changed)
            self.orbital_checkboxes.append(checkbox)
            self.scroll_right_layout.addWidget(checkbox)

        self.merge_button = QPushButton("Plot merged DOS")
        self.scroll_layout.addWidget(self.merge_button, 2, 1)
        self.merge_button.clicked.connect(self.plot_merged)

        empty_widget = QWidget()  # An empty tab

        right_tab_widget.addTab(param_tree_widget, "Parameters")
        right_tab_widget.addTab(self.scroll_area, "DOS atoms & orbitals")
        right_tab_widget.addTab(empty_widget, "Structure list")
        splitter.addWidget(right_tab_widget)

        self.update_indexes()


    def clear_plots(self):

        self.plot_tab1.clear()
        self.plot_tab1_right.clear()
        self.add_fermi_line()
        self.plot_tab1_right.addItem(self.region)


    def create_data(self):
        #self.data = VaspData("D:\\OneDrive - Uniwersytet Jagielloński\\modelowanie DFT\\CeO2\\CeO2_bulk\\Ceria_bulk_vacancy\\0.Ceria_bulk_1vacancy\\scale_0.98")
        self.data = VaspData("D:\\OneDrive - Uniwersytet Jagielloński\\modelowanie DFT\\czasteczki\\O2")
        #self.data = VaspData("D:\\OneDrive - Uniwersytet Jagielloński\\modelowanie DFT\\co3o4_new_new\\2.ROS\\1.large_slab\\1.old_random_mag\\6.CoO-O_CoO-O\\antiferro\\HSE\\DOS_new")
        self.dataset_down = self.data.data_down
        self.dataset_up = self.data.data_up
        self.number_of_atoms = self.data.number_of_atoms
        self.orbitals = self.data.orbitals
        self.atoms_symb_and_num = self.data.atoms_symb_and_num
        self.e_fermi = self.data.e_fermi

    def parameter_changed(self, param, changes):
        for param, change, data in changes:
            if change == 'value':
                self.update_plot()

    def checkbox_changed(self):
        self.update_plot(self.dataset_up, self.dataset_down)
        self.update_indexes()

    def plot_merged(self):
        print("merging...")
        self.clear_plots()
        self.merged_data_up = [sum(elements) for elements in zip(*[list[0] for list in self.plot_data_list_up])]
        self.merged_data_down = [sum(elements) for elements in zip(*[list[0] for list in self.plot_data_list_down])]
        self.plot_tab1_right.addItem(pg.PlotDataItem([-x for x in self.merged_data_down], self.data.doscar.total_dos_energy, pen=pg.mkPen('r')))

        self.plot_tab1.addItem(
            pg.PlotDataItem(self.merged_data_up, self.data.doscar.total_dos_energy, pen=pg.mkPen('r')))
        self.plot_tab1_right.addItem(pg.PlotDataItem(self.merged_data_up, self.data.doscar.total_dos_energy, pen=pg.mkPen('r')))
        
    def update_indexes(self):
        self.selected_atoms = [i for i, cb in enumerate(self.atom_checkboxes) if cb.isChecked()]
        self.selected_orbitals = [i for i, cb in enumerate(self.orbital_checkboxes) if cb.isChecked()]

    def update_plot(self, data_up, data_down):
        self.clear_plots()
        # Accumulate plot data from selected checkboxes
        self.plot_data_list_down = []
        self.plot_data_list_up = []
        colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k']  # Add more colors if needed
        for atom_color, atom_index in enumerate(self.selected_atoms):
            for orb_color, orbital_index in enumerate(self.selected_orbitals):
                plot_color = colors[orb_color % len(colors)]  # Cycle through colors
                plot_data = data_down[atom_index][orbital_index]
                self.plot_data_list_down.append((plot_data, plot_color))

        for atom_color, atom_index in enumerate(self.selected_atoms):
            for orb_color, orbital_index in enumerate(self.selected_orbitals):
                plot_color = colors[orb_color % len(colors)]  # Cycle through colors
                plot_data = data_up[atom_index][orbital_index]
                self.plot_data_list_up.append((plot_data, plot_color))

        # Plot all accumulated data in plot_tab1
        for plot_data, color in self.plot_data_list_down:
            self.plot_tab1.addItem(pg.PlotDataItem([-x for x in plot_data],self.data.doscar.total_dos_energy,  pen=pg.mkPen(color)))
            self.plot_tab1_right.addItem(pg.PlotDataItem([-x for x in plot_data],self.data.doscar.total_dos_energy,  pen=pg.mkPen(color)))
        for plot_data, color in self.plot_data_list_up:
            self.plot_tab1.addItem(pg.PlotDataItem(plot_data, self.data.doscar.total_dos_energy, pen=pg.mkPen(color)))
            self.plot_tab1_right.addItem(pg.PlotDataItem(plot_data,self.data.doscar.total_dos_energy,  pen=pg.mkPen(color)))



    def add_fermi_line(self):
        inf1 = pg.InfiniteLine(pos=float(self.e_fermi), movable=False, pen=(0,0,200), angle=0, label='E_Fermi={value:0.2f}', labelOpts={'position': 0.1, 'color': (0, 0, 255), 'fill': (0, 0, 255, 100),'movable': True})
        self.plot_tab1.addItem(inf1)
        self.plot_tab1_right.addItem(inf1)


def main():
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.update_plot(mainWin.dataset_up, mainWin.dataset_down)
    mainWin.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
