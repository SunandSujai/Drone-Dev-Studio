import sys
from physics_engine import DronePhysics
from drone_visualizer import DroneVisualizer
from PyQt6.QtWidgets import (QApplication, QMainWindow, QDockWidget, 
                             QTableWidget, QTableWidgetItem, QVBoxLayout, 
                             QWidget, QHeaderView, QTextEdit, QTabWidget,
                             QPushButton, QTreeView, QToolBar, QFileDialog, QMessageBox)
from PyQt6.QtGui import QAction, QFileSystemModel
from PyQt6.QtCore import Qt, QDir, QFileInfo

class DroneStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Dev Studio v1.2")
        self.resize(1200, 800)

        # 1. TOP TOOLBAR
        self.create_toolbar()

        # 2. CENTRAL WORKSPACE
        self.central_tabs = QTabWidget()
        self.central_tabs.setTabsClosable(True)
        self.central_tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.central_tabs)
        
        # Tab 1: Default Welcome / Editor
        self.editor_tab = QTextEdit("// Select a file to edit...")
        self.central_tabs.addTab(self.editor_tab, "Welcome")

        # Tab 2: The New 3D Visualizer (THIS IS NEW)
        self.sim_tab = DroneVisualizer()
        # We disable the 'close' button on the Sim tab so you don't accidentally kill it
        self.central_tabs.addTab(self.sim_tab, "3D Simulation")
        # Optional: Hide the close button specifically for the Sim tab (index 1)
        # self.central_tabs.tabBar().setTabButton(1, QTabBar.ButtonPosition.RightSide, None)

        # 3. PANELS
        self.create_log_panel()
        self.create_project_tree()
        self.create_hardware_panel()

    def start_flight_sim(self):
        try:
            # Scrape current hardware settings from your table
            data = {
                'kv': int(self.prop_table.item(0, 1).text()),
                'cells': int(self.prop_table.item(1, 1).text().upper().replace("S","")),
                'diam': float(self.prop_table.item(2, 1).text()),
                'pitch': float(self.prop_table.item(3, 1).text()),
                'weight': float(self.prop_table.item(5, 1).text())
            }
            
            # Switch to the simulation tab and start the loop
            self.central_tabs.setCurrentWidget(self.sim_tab)
            self.sim_tab.start_sim(data)
            self.log_output.append("🚀 Flight Simulator Active. Use UP/DOWN arrows to control throttle.")
            
        except Exception as e:
            self.log_output.append(f"❌ Sim Error: Ensure all specs are valid numbers. ({e})") 



    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)



        # Action: Open File
        open_action = QAction("Open File", self)
        open_action.setStatusTip("Open a specific file")
        open_action.triggered.connect(self.open_file_dialog)
        toolbar.addAction(open_action)

        # Action: Save File
        save_action = QAction("Save", self)
        save_action.setStatusTip("Save current file")
        save_action.triggered.connect(self.save_current_file)
        toolbar.addAction(save_action)

        toolbar.addSeparator() # Visual spacer

        # Action: Open Working Directory (Project Folder)
        folder_action = QAction("Open Project Folder", self)
        folder_action.setStatusTip("Change the root directory of the project tree")
        folder_action.triggered.connect(self.change_project_folder)
        toolbar.addAction(folder_action)

        run_action = QAction("Run Simulation", self)
        run_action.triggered.connect(self.start_flight_sim)
        toolbar.addAction(run_action)

    def create_project_tree(self):
        dock = QDockWidget("Project Files", self)
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.currentPath())
        
        self.tree = QTreeView()
        self.tree.setModel(self.file_model)
        self.tree.setRootIndex(self.file_model.index(QDir.currentPath()))
        
        for i in range(1, 4):
            self.tree.hideColumn(i)
        self.tree.setHeaderHidden(True)
        self.tree.doubleClicked.connect(self.open_file_from_tree)
            
        dock.setWidget(self.tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    def change_project_folder(self):
        # Opens a dialog to pick a new folder
        folder_path = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder_path:
            self.tree.setRootIndex(self.file_model.index(folder_path))
            self.log_output.append(f"📂 Project Root changed to: {folder_path}")

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if file_path:
            self.load_file_content(file_path)

    def open_file_from_tree(self, index):
        file_path = self.file_model.filePath(index)
        if not self.file_model.isDir(index):
            self.load_file_content(file_path)

    def load_file_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_editor = QTextEdit()
            new_editor.setText(content)
            file_name = QFileInfo(file_path).fileName()
            
            # Store the full path in the tab's "tooltip" so we know where to save later
            new_tab_index = self.central_tabs.addTab(new_editor, file_name)
            self.central_tabs.setTabToolTip(new_tab_index, file_path)
            self.central_tabs.setCurrentIndex(new_tab_index)
            
            self.log_output.append(f"📄 Opened: {file_name}")
        except Exception as e:
            self.log_output.append(f"❌ Error: {str(e)}")

    def save_current_file(self):
        current_index = self.central_tabs.currentIndex()
        if current_index == -1:
            return

        current_editor = self.central_tabs.widget(current_index)
        # We stored the path in the tooltip earlier
        file_path = self.central_tabs.tabToolTip(current_index)

        if not file_path:
            # If it's a new unsaved file (Implementation for 'Save As' would go here)
            self.log_output.append("⚠️ Cannot save: No file path associated.")
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(current_editor.toPlainText())
            self.log_output.append(f"💾 Saved: {file_path}")
        except Exception as e:
            self.log_output.append(f"❌ Save Error: {str(e)}")

    def close_tab(self, index):
        self.central_tabs.removeTab(index)

    def create_hardware_panel(self):
        dock = QDockWidget("Hardware Specs", self)
        container = QWidget()
        layout = QVBoxLayout(container)

        # Increased rows to 6 to accommodate new data
        self.prop_table = QTableWidget(6, 3) 
        self.prop_table.setHorizontalHeaderLabels(["Parameter", "Value", "Unit"])
        
        # Updated Data List with Prop Specs
        data = [
            ("Motor KV", "2400", "KV"),
            ("Battery Cells", "4", "S"),      # Changed default to 4S (common for beginners)
            ("Prop Diameter", "5", "inch"),   # NEW
            ("Prop Pitch", "4.5", "inch"),    # NEW
            ("Max Current", "45", "A"),
            ("Frame Weight", "650", "g")
        ]

        for row, (name, val, unit) in enumerate(data):
            # Column 0: Parameter Name (Locked)
            item_name = QTableWidgetItem(name)
            item_name.setFlags(item_name.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.prop_table.setItem(row, 0, item_name)

            # Column 1: Value (Editable)
            self.prop_table.setItem(row, 1, QTableWidgetItem(val))

            # Column 2: Unit (Locked)
            item_unit = QTableWidgetItem(unit)
            item_unit.setFlags(item_unit.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.prop_table.setItem(row, 2, item_unit)

        self.prop_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.prop_table.itemChanged.connect(self.handle_config_change)

        layout.addWidget(self.prop_table)
        
        self.sync_button = QPushButton("Sync Configuration")
        self.sync_button.clicked.connect(self.sync_data)
        layout.addWidget(self.sync_button)
        
        dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
    
    def sync_data(self):
        self.log_output.append("--- 📡 SYNC INITIATED ---")
        
        try:
            # 1. READ DATA by Row Index
            # Row 0: KV | Row 1: Cells | Row 2: Diam | Row 3: Pitch | Row 5: Weight
            raw_kv = self.prop_table.item(0, 1).text()
            raw_cells = self.prop_table.item(1, 1).text()
            raw_diam = self.prop_table.item(2, 1).text()
            raw_pitch = self.prop_table.item(3, 1).text()
            raw_weight = self.prop_table.item(5, 1).text() # Note: Weight is now row 5

            # 2. CONVERT
            motor_kv = int(raw_kv)
            battery_cells = int(raw_cells.upper().replace("S", ""))
            prop_diam = float(raw_diam)
            prop_pitch = float(raw_pitch)
            weight_g = float(raw_weight)

            # 3. RUN PHYSICS
            engine = DronePhysics(motor_kv, battery_cells, weight_g, prop_diam, prop_pitch)
            stats = engine.compute_flight_stats()

            # 4. DISPLAY
            self.log_output.append(f"🔋 Voltage: {stats['Voltage (V)']}V | RPM: {stats['Motor RPM']}")
            self.log_output.append(f"💨 Propeller: {prop_diam}x{prop_pitch}")
            self.log_output.append(f"🚀 Max Thrust: {stats['Total Thrust (g)']}g")
            
            if stats['TWR (Ratio)'] < 1.0:
                self.log_output.append(f"❌ CRITICAL: TOO HEAVY (TWR {stats['TWR (Ratio)']})")
            else:
                self.log_output.append(f"✅ READY (TWR {stats['TWR (Ratio)']})")
                self.log_output.append(f"   Hover Throttle: {stats['Hover Throttle (%)']}%")

        except ValueError:
            self.log_output.append("❌ Input Error: Ensure all fields are numbers.")
        except Exception as e:
            self.log_output.append(f"❌ System Error: {str(e)}")
    def create_log_panel(self):
        dock = QDockWidget("Telemetry & Output", self)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        dock.setWidget(self.log_output)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

    def handle_config_change(self, item):
        # Only log changes if they happen in the Value column (Column 1)
        if item.column() == 1:
            row = item.row()
            param = self.prop_table.item(row, 0).text()
            val = item.text()
            unit = self.prop_table.item(row, 2).text()
            self.log_output.append(f"🔧 Update: {param} set to {val} {unit}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = DroneStudio()
    window.show()
    sys.exit(app.exec())