import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QScrollArea, \
    QGroupBox


class OrbitalSelector(QWidget):
    def __init__(self, main_orbitals, orb_types):
        super().__init__()

        self.main_orbitals = main_orbitals
        self.orb_types = orb_types
        self.orbital_up = []

        # Flatten the main_orbitals list for checkboxes
        self.orbitals = [orb for sublist in main_orbitals for orb in sublist]

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Scroll area for checkboxes
        scroll_area = QScrollArea()
        scroll_content = QGroupBox()
        self.scroll_right_layout = QVBoxLayout(scroll_content)

        # Create checkboxes for each orbital
        self.orbital_checkboxes = []
        for orbital in self.orbitals:
            checkbox = QCheckBox(orbital)
            checkbox.stateChanged.connect(self.checkbox_changed)
            self.orbital_checkboxes.append(checkbox)
            self.scroll_right_layout.addWidget(checkbox)

        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Group for select and deselect buttons
        btn_group_layout = QHBoxLayout()

        # Select buttons
        select_layout = QVBoxLayout()
        for i, orbital_list in enumerate(self.main_orbitals):
            orb_letter = orbital_list[0] if len(orbital_list) == 1 else orbital_list[0][0]
            btn = QPushButton(f"select {orb_letter}", self)
            btn.clicked.connect(lambda _, x=i: self.select_orbital(x))
            select_layout.addWidget(btn)

        select_all_btn = QPushButton("select all", self)
        select_all_btn.clicked.connect(self.select_all_orbitals)
        select_layout.addWidget(select_all_btn)

        btn_group_layout.addLayout(select_layout)

        # Deselect buttons
        deselect_layout = QVBoxLayout()
        for i, orbital_list in enumerate(self.main_orbitals):
            orb_letter = orbital_list[0] if len(orbital_list) == 1 else orbital_list[0][0]
            btn = QPushButton(f"deselect {orb_letter}", self)
            btn.clicked.connect(lambda _, x=i: self.deselect_orbital(x))
            deselect_layout.addWidget(btn)

        deselect_all_btn = QPushButton("Deselect all", self)
        deselect_all_btn.clicked.connect(self.deselect_all_orbitals)
        deselect_layout.addWidget(deselect_all_btn)

        btn_group_layout.addLayout(deselect_layout)

        layout.addLayout(btn_group_layout)

        self.setLayout(layout)


    def checkbox_changed(self):
        self.orbital_up = [checkbox.text() for checkbox in self.orbital_checkboxes if checkbox.isChecked()]
        print(f"Checkboxes changed: {self.orbital_up}")

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
        self.update_checkboxes([], False)
        print("Deselected All")

    def update_checkboxes(self, orbitals, check):
        # Block signals to avoid multiple updates
        for checkbox in self.orbital_checkboxes:
            checkbox.blockSignals(True)
            if checkbox.text() in orbitals:
                checkbox.setChecked(check)
            elif not check:
                checkbox.setChecked(False)
            checkbox.blockSignals(False)

        # Update orbital_up once after all changes
        self.checkbox_changed()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Example data
    main_orbitals_in_system = [["s"], ["py", "pz", "px"], ["dxy", "dyz", "dz", "dxz", "dx2y2"]]
    orb_types = [["s"], ["py", "pz", "px"], ["dxy", "dyz", "dz", "dxz", "dx2y2"],
                 ["fy(3x2-y2)", "fxyz", "fyz2", "fz3", "fxz2", "fz(x2-y2)", "fx(x2-3y2)"]]

    ex = OrbitalSelector(main_orbitals_in_system, orb_types)
    ex.setWindowTitle('Orbital Selector')
    ex.show()

    sys.exit(app.exec_())