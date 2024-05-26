import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel,
                             QScrollArea, QFrame, QTabWidget, QSplitter,QPlainTextEdit, QPushButton, QGridLayout)
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
        self.orbital_types = self.doscar.orbital_types
        self.e_fermi = self.doscar.efermi

        poscar = PoscarParser(os.path.join(dir, "POSCAR"))
        self.atoms_symb_and_num = poscar.symbol_and_number()
        self.number_of_atoms = poscar.number_of_atoms()
        self.list_atomic_symbols = poscar.list_atomic_symbols()
        self.atomic_symbols = poscar.atomic_symbols()


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
        self.orb_types = [["s"], ["py", "pz", "px"], ["dxy", "dyz", "dz", "dxz", "dx2y2"],
                          ["fy(3x2-y2)", "fxyz", "fyz2", "fz3", "fxz2", "fz(x2-y2)", "fx(x2-3y2)"]]

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

        ######################################################## tab 2 - orbital selector ###########################
        # Create QHBoxLayout for checkboxes
        self.scroll_area_widget = QWidget()
        self.scroll_area_layout = QHBoxLayout(self.scroll_area_widget)

        # Left side of the scroll area for atoms
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

        # Right side for orbitals
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

        all_btn_layout = QVBoxLayout()
        btn_orb_layout = QHBoxLayout()
        btn_atoms_layout = QHBoxLayout()
        all_btn_layout.addLayout(btn_orb_layout)
        all_btn_layout.addLayout(btn_atoms_layout)

        ####################### Select ORBITALS buttons#################################################
        select_layout = QVBoxLayout()
        for i, orbital_list in enumerate(self.orbital_types):
            orb_letter = orbital_list[0] if len(orbital_list) == 1 else orbital_list[0][0]
            btn = QPushButton(f"select {orb_letter}", self)
            btn.clicked.connect(lambda _, x=i: self.select_orbital(x))
            select_layout.addWidget(btn)

        select_all_btn = QPushButton("select all", self)
        select_all_btn.clicked.connect(self.select_all_orbitals)
        select_layout.addWidget(select_all_btn)

        btn_orb_layout.addLayout(select_layout)

        # Deselect buttons
        deselect_layout = QVBoxLayout()
        for i, orbital_list in enumerate(self.orbital_types):
            orb_letter = orbital_list[0] if len(orbital_list) == 1 else orbital_list[0][0]
            btn = QPushButton(f"deselect {orb_letter}", self)
            btn.clicked.connect(lambda _, x=i: self.deselect_orbital(x))
            deselect_layout.addWidget(btn)

        deselect_all_btn = QPushButton("Deselect all", self)
        deselect_all_btn.clicked.connect(self.deselect_all_orbitals)
        deselect_layout.addWidget(deselect_all_btn)

        btn_orb_layout.addLayout(deselect_layout)

        ############################################ ATOMS ##########################################
        select_atom_layout = QVBoxLayout()
        deselect_atom_layout = QVBoxLayout()

        for i, atom_list in enumerate(self.atomic_symbols):
            atom_letter = atom_list
            btn = QPushButton(f"select {atom_letter}", self)
            btn.clicked.connect(lambda _, x=i: self.select_atom(x))
            select_atom_layout.addWidget(btn)

        select_all_atoms_btn = QPushButton("Select all", self)
        select_all_atoms_btn.clicked.connect(self.select_all_atoms)
        select_atom_layout.addWidget(select_all_atoms_btn)

        for i, atom_list in enumerate(self.atomic_symbols):
            atom_letter = atom_list
            btn = QPushButton(f"Deselect {atom_letter}", self)
            btn.clicked.connect(lambda _, x=i: self.deselect_atom(x))
            deselect_atom_layout.addWidget(btn)

        deselect_all_atoms_btn = QPushButton("Deselect all", self)
        deselect_all_atoms_btn.clicked.connect(self.deselect_all_atoms)
        deselect_atom_layout.addWidget(deselect_all_atoms_btn)


        btn_atoms_layout.addLayout(select_atom_layout)
        btn_atoms_layout.addLayout(deselect_atom_layout)
        self.scroll_area_layout.addLayout(all_btn_layout)
        ########################################## additional buttons ##################################################
        self.additional_button_layout  = QGridLayout()
        self.color_button = pg.ColorButton()
        self.color_button.setColor('r')
        self.additional_button_layout.addWidget(self.color_button, 0, 0,)

        self.plot_merged_btn = QPushButton("Plot merged", self)
        self.additional_button_layout.addWidget(self.plot_merged_btn, 0, 1)
        self.plot_merged_btn.clicked.connect(self.plot_merged)

        self.full_range_plot.plot([1,2,3,4,5,6,7,8,9,10], pen = pg.mkPen(self.color_button.color()))




        all_btn_layout.addLayout(self.additional_button_layout)


        ###################################### tab 3 - atom selection ##################################################
        empty_widget = QWidget()  # An empty tab

        right_tab_widget.addTab(param_tree_widget, "Parameters")
        right_tab_widget.addTab(self.scroll_area_widget, "DOS atoms & orbitals")
        right_tab_widget.addTab(empty_widget, "Structure list")
        splitter.addWidget(right_tab_widget)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setFixedHeight(200)
        main_layout.addWidget(self.console)

    def select_atom(self, index):
        self.update_atom_checkboxes(self.partitioned_lists[index], True)

    def deselect_atom(self, index):
        self.update_atom_checkboxes(self.partitioned_lists[index], False)

    def select_all_atoms(self):
        self.update_atom_checkboxes(self.atoms_symb_and_num, True)

    def deselect_all_atoms(self):
        self.update_atom_checkboxes(self.atoms_symb_and_num, False)

    def select_orbital(self, index):
        self.update_checkboxes(self.orb_types[index], True)
        print(f"Selected: {self.orbital_up}")

    def deselect_orbital(self, index):
        self.update_checkboxes(self.orb_types[index], False)
        print(f"Deselected: {self.orbital_up}")

    def select_all_orbitals(self):
        all_orbitals = [orb for sublist in self.orb_types for orb in sublist]
        self.update_checkboxes(all_orbitals, True)
        print(f"Selected All: {self.orbital_up}")

    def deselect_all_orbitals(self):
        all_orbitals = [orb for sublist in self.orb_types for orb in sublist]
        self.update_checkboxes(all_orbitals, False)
        print("Deselected All")

    def update_checkboxes(self, orbitals, check):
        # Block signals to avoid multiple updates
        for checkbox in self.orbital_checkboxes:
            checkbox.blockSignals(True)
            if checkbox.text() in orbitals:
                checkbox.setChecked(check)
            checkbox.blockSignals(False)
        # Update orbital_up once after all changes
        self.checkbox_changed()

    def update_atom_checkboxes(self, atom, check):
        for checkbox in self.atom_checkboxes:
            checkbox.blockSignals(True)
            if checkbox.text() in atom:
                checkbox.setChecked(check)
            checkbox.blockSignals(False)
        self.checkbox_changed()

    def print_to_console(self, message):
        self.console.appendPlainText(">>> "+message)

    def parameter_changed(self, param, changes):
        for param, change, data in changes:
            if change == 'value':
                self.update_plot()

    def checkbox_changed(self):
        self.update_indexes()
        self.update_plot()
        self.orbital_up = [checkbox.text() for checkbox in self.orbital_checkboxes if checkbox.isChecked()]
        self.atoms_up = [checkbox for checkbox in self.atom_checkboxes if checkbox.isChecked()]

    def update_indexes(self):
        self.selected_atoms = [i for i, cb in enumerate(self.atom_checkboxes) if cb.isChecked()]
        self.selected_orbitals = [i for i, cb in enumerate(self.orbital_checkboxes) if cb.isChecked()]

    def plot_merged(self):
        '''
        print('starting')
        all_data = []
        for atom in self.selected_atoms:
            for oribtal in self.selected_orbitals:
                all_data.append(self.dataset_up[atom, oribtal])
        print()
        data_up   =   self.dataset_up[self.selected_atoms][self.selected_orbitals]
        data_down = self.dataset_down[self.selected_atoms][self.selected_orbitals]
        plot_color = self.color_button.color()

        self.clear_plot_data(self.full_range_plot)
        self.clear_plot_data(self.bounded_plot)

        #self.full_range_plot.plot(data_up, self.data.doscar.total_dos_energy, pen=pg.mkPen(plot_color))
        #self.bounded_plot.plot(data_up, self.data.doscar.total_dos_energy, pen=pg.mkPen(plot_color))

        #self.full_range_plot.plot(plot_data, self.data.doscar.total_dos_energy, pen=pg.mkPen(plot_color))
        #self.bounded_plot.plot(plot_data, self.data.doscar.total_dos_energy, pen=pg.mkPen(plot_color))
        '''
        pass


    def update_plot(self):
        selected_indices = [i for i, cb in enumerate(self.atom_checkboxes) if cb.isChecked()]
        middle_idx = self.param.param('Middle Index').value()

        # Clear only the data items, not the LinearRegionItem or InfiniteLine
        self.clear_plot_data(self.full_range_plot)
        self.clear_plot_data(self.bounded_plot)

        # plot dataset up
        colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k','b', 'r', 'g', 'c', 'm', 'y', 'k','b', 'r', 'g', 'c', 'm', 'y', 'k']  # Add more colors if needed
        for atom_index in self.selected_atoms:
            for orbital_index in self.selected_orbitals:
                plot_color = colors[orbital_index]  # Cycle through colors
                plot_data = self.dataset_up[atom_index][orbital_index]
                self.full_range_plot.plot(plot_data, self.data.doscar.total_dos_energy, pen=pg.mkPen(plot_color))
                self.bounded_plot.plot(plot_data, self.data.doscar.total_dos_energy, pen=pg.mkPen(plot_color))

        # plot dataset down
        for atom_index in self.selected_atoms:
            for orbital_index in self.selected_orbitals:
                plot_color = colors[orbital_index]  # Cycle through colors
                plot_data = self.dataset_down[atom_index][orbital_index]
                self.full_range_plot.plot([-x for x in plot_data], self.data.doscar.total_dos_energy, pen=pg.mkPen(plot_color))
                self.bounded_plot.plot([-x for x in plot_data], self.data.doscar.total_dos_energy, pen=pg.mkPen(plot_color))

        self.update_bounded_plot_y_range()
        self.print_to_console(f'added {self.selected_atoms} {self.selected_orbitals}')

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
        self.data = VaspData("D:\\OneDrive - Uniwersytet Jagielloński\\modelowanie DFT\\CeO2\\CeO2_bulk\\Ceria_bulk_vacancy\\0.Ceria_bulk_1vacancy\\scale_0.98")
        #self.data = VaspData("D:\\OneDrive - Uniwersytet Jagielloński\\modelowanie DFT\\czasteczki\\O2")
        #self.data = VaspData("D:\\OneDrive - Uniwersytet Jagielloński\\modelowanie DFT\\co3o4_new_new\\2.ROS\\1.large_slab\\1.old_random_mag\\6.CoO-O_CoO-O\\antiferro\\HSE\\DOS_new")
        self.dataset_down = self.data.data_down
        self.dataset_up = self.data.data_up
        self.number_of_atoms = self.data.number_of_atoms
        self.orbitals = self.data.orbitals
        self.orbital_types = self.data.orbital_types
        self.atoms_symb_and_num = self.data.atoms_symb_and_num
        self.e_fermi = self.data.e_fermi
        self.list_atomic_symbols = self.data.list_atomic_symbols
        self.atomic_symbols = self.data.atomic_symbols

        self.partitioned_lists = [[] for _ in range(len(self.atomic_symbols))]

        # Partition the original list
        for item in self.atoms_symb_and_num:
            for i, atom in enumerate(self.atomic_symbols):
                if item.startswith(atom):
                    self.partitioned_lists[i].append(item)
                    break  # Once found, no need to continue checking other atoms


def main():
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.print_to_console(' Welcome to DOSwizard! This is very experimental! ')
    mainWin.print_to_console('            use at your own risk.                 ')
    mainWin.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
