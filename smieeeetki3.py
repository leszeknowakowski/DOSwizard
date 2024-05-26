import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel,
                             QScrollArea, QFrame, QTabWidget, QSplitter, QSizePolicy)
from PyQt5 import QtCore
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree
from VASPparser import *

pg.setConfigOptions(antialias=True)

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


class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.plot = pg.PlotWidget()
        self.plot.setBackground('w')  # Set background to white
        self.layout.addWidget(self.plot)

    def plot_data(self, data, color='b'):
        self.plot.clear()
        for single_data in data:
            self.plot.plot(single_data, pen=pg.mkPen(color))


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
        self.plot_tab1 = QWidget()
        self.plot_tab1_layout = QVBoxLayout(self.plot_tab1)  # Change to QVBoxLayout to accommodate the splitter
        left_tab_widget.addTab(self.plot_tab1, "DOS")
        left_tab_widget.addTab(PlotWidget(), "Structure")
        left_tab_widget.addTab(PlotWidget(), "PARCHG/CHGCAR")
        splitter.addWidget(left_tab_widget)

        # Create QSplitter to hold the full range plot and the bounded plot
        plot_splitter = QSplitter(QtCore.Qt.Horizontal)
        self.full_range_plot = pg.PlotWidget()
        self.full_range_plot.setBackground('w')  # Set background to white
        self.bounded_plot = pg.PlotWidget()
        self.bounded_plot.setBackground('w')  # Set background to white

        plot_splitter.addWidget(self.full_range_plot)
        plot_splitter.addWidget(self.bounded_plot)
        plot_splitter.setStretchFactor(0, 3)  # Aspect ratio 0.7
        plot_splitter.setStretchFactor(1, 3)  # Aspect ratio 0.3

        self.plot_tab1_layout.addWidget(plot_splitter)

        # Add LinearRegionItem to the full range plot
        self.region = pg.LinearRegionItem(orientation=pg.LinearRegionItem.Horizontal, brush=pg.mkBrush(255,235,14,100))
        self.full_range_plot.addItem(self.region)
        self.region.sigRegionChanged.connect(self.update_bounded_plot_y_range)

        # Connect view range change of the bounded plot to update the LinearRegion
        self.bounded_plot.sigRangeChanged.connect(self.update_region_from_bounded_plot)

        # Set an initial region to make sure it's visible
        self.region.setRegion([-5,5])

        # Add InfiniteLine at y=0.5 to both plots
        self.inf_line_full = pg.InfiniteLine(pos=float(self.data.doscar.efermi), angle=0, pen=pg.mkPen('b'), movable=False, label='E_Fermi={value:0.2f}',labelOpts={'position': 0.1, 'color': (0, 0, 255), 'fill': (0, 0, 255, 100),'movable': True})
        self.inf_line_bounded = pg.InfiniteLine(pos=float(self.data.doscar.efermi), angle=0, pen=pg.mkPen('b'), movable=False, label='E_Fermi={value:0.2f}',labelOpts={'position': 0.1, 'color': (0, 0, 255), 'fill': (0, 0, 255, 100),'movable': True})

        self.full_range_plot.addItem(self.inf_line_full)
        self.bounded_plot.addItem(self.inf_line_bounded)
        splitter.setSizes([1, 1])

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

        # Create QHBoxLayout for checkboxes
        self.scroll_area_widget = QWidget()
        self.scroll_area_layout = QHBoxLayout(self.scroll_area_widget)

        # Left side of the scroll area for checkboxes
        self.checkboxes_widget = QWidget()
        self.checkboxes_layout = QVBoxLayout(self.checkboxes_widget)
        self.checkboxes_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_area_left = QScrollArea()  # New scroll area for checkboxes
        self.scroll_area_left.setWidgetResizable(True)
        self.scroll_area_left.setWidget(self.checkboxes_widget)
        self.scroll_area_left.setFrameShape(QFrame.NoFrame)
        self.scroll_area_layout.addWidget(self.scroll_area_left)

        label = QLabel("atoms:")
        self.checkboxes_layout.addWidget(label)

        self.atom_checkboxes = []
        for i in range(self.number_of_atoms):
            checkbox = QCheckBox(self.atoms_symb_and_num[i])
            checkbox.stateChanged.connect(self.checkbox_changed)
            self.atom_checkboxes.append(checkbox)
            self.checkboxes_layout.addWidget(checkbox)

        # Right side for other content
        self.scroll_right_widget = QWidget()
        self.scroll_right_layout = QVBoxLayout(self.scroll_right_widget)
        self.scroll_right_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_area_right = QScrollArea()  # New scroll area for right content
        self.scroll_area_right.setWidgetResizable(True)
        self.scroll_area_right.setWidget(self.scroll_right_widget)
        self.scroll_area_right.setFrameShape(QFrame.NoFrame)
        self.scroll_area_layout.addWidget(self.scroll_area_right)

        label = QLabel("orbitals:")
        self.scroll_right_layout.addWidget(label)

        self.orbital_checkboxes = []
        for i in range(len(self.orbitals)):
            checkbox = QCheckBox(self.orbitals[i])
            checkbox.stateChanged.connect(self.checkbox_changed)
            self.orbital_checkboxes.append(checkbox)
            self.scroll_right_layout.addWidget(checkbox)

        param_tree_layout.addWidget(self.scroll_area_widget)

        empty_widget = QWidget()  # An empty tab

        right_tab_widget.addTab(param_tree_widget, "Parameters")
        right_tab_widget.addTab(self.scroll_area_widget, "DOS atoms & orbitals")
        right_tab_widget.addTab(empty_widget, "Structure list")
        splitter.addWidget(right_tab_widget)



    def parameter_changed(self, param, changes):
        for param, change, data in changes:
            if change == 'value':
                self.update_plot()

    def checkbox_changed(self):
        self.update_indexes()
        self.update_plot()


    def update_indexes(self):
        self.selected_atoms = [i for i, cb in enumerate(self.atom_checkboxes) if cb.isChecked()]
        self.selected_orbitals = [i for i, cb in enumerate(self.orbital_checkboxes) if cb.isChecked()]
    def update_plot(self):
        selected_indices = [i for i, cb in enumerate(self.atom_checkboxes) if cb.isChecked()]
        middle_idx = self.param.param('Middle Index').value()

        # Clear only the data items, not the LinearRegionItem or InfiniteLine
        self.clear_plot_data(self.full_range_plot)
        self.clear_plot_data(self.bounded_plot)

        # plot dataset up
        colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k']  # Add more colors if needed
        for atom_color, atom_index in enumerate(self.selected_atoms):
            for orbital_color, orbital_index in enumerate(self.selected_orbitals):
                plot_color = colors[orbital_color % len(colors)]  # Cycle through colors
                plot_data = self.dataset_up[atom_index][orbital_index]
                self.full_range_plot.plot(plot_data, self.data.doscar.total_dos_energy, pen=pg.mkPen(plot_color))
                self.bounded_plot.plot(plot_data, self.data.doscar.total_dos_energy, pen=pg.mkPen(plot_color))

        # plot dataset down
        for atom_color, atom_index in enumerate(self.selected_atoms):
            for orbital_color, orbital_index in enumerate(self.selected_orbitals):
                plot_color = colors[orbital_color % len(colors)]  # Cycle through colors
                plot_data = self.dataset_down[atom_index][atom_color]
                self.full_range_plot.plot([-x for x in plot_data], self.data.doscar.total_dos_energy, pen=pg.mkPen(plot_color))
                self.bounded_plot.plot([-x for x in plot_data], self.data.doscar.total_dos_energy, pen=pg.mkPen(plot_color))

        self.update_bounded_plot_y_range()  # Initial update for the bounded plot

    def clear_plot_data(self, plot_widget):
        items = [item for item in plot_widget.listDataItems() if isinstance(item, pg.PlotDataItem)]
        for item in items:
            plot_widget.removeItem(item)

    def update_bounded_plot_y_range(self):
        min_y, max_y = self.region.getRegion()
        self.bounded_plot.setYRange(min_y, max_y, padding=0)

    def update_region_from_bounded_plot(self):
        view_range = self.bounded_plot.viewRange()[1]
        self.region.setRegion(view_range)

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

def main():
    print('####################################################')
    print('# Welcome to DOSwizard! This is very experimental! #')
    print('# use at your own risk.                            #')
    print('####################################################')
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
