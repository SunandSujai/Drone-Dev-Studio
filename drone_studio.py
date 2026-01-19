import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QDockWidget, 
                             QTableWidget, QTableWidgetItem, QVBoxLayout, 
                             QWidget, QHeaderView, QTextEdit, QTabWidget)
from PyQt6.QtCore import Qt

class DroneStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Dev Studio v1.0")
        self.resize(1100, 700)

        # Central Workspace
        self.central_tabs = QTabWidget()
        self.setCentralWidget(self.central_tabs)
        self.editor_tab = QTextEdit("// Drone Logic Script")
        self.central_tabs.addTab(self.editor_tab, "Script Editor")

        self.create_hardware_panel()
        self.create_log_panel()

    def create_hardware_panel(self):
        dock = QDockWidget("Hardware Specs", self)
        container = QWidget()
        layout = QVBoxLayout(container)

        self.prop_table = QTableWidget(4, 2)
        self.prop_table.setHorizontalHeaderLabels(["Parameter", "Value"])
        
        data = [("Motor", "2306 2400KV"), ("ESC", "45A"), ("Battery", "6S"), ("Weight", "650g")]
        for i, (name, val) in enumerate(data):
            self.prop_table.setItem(i, 0, QTableWidgetItem(name))
            self.prop_table.setItem(i, 1, QTableWidgetItem(val))

        self.prop_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # TRIGGER: When a cell is changed, call our log function
        self.prop_table.itemChanged.connect(self.handle_config_change)

        layout.addWidget(self.prop_table)
        dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    def create_log_panel(self):
        dock = QDockWidget("Telemetry & Output", self)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        self.log_output.append("System: Initialized Drone Dev Studio.")
        dock.setWidget(self.log_output)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

    def handle_config_change(self, item):
        # This function runs every time you edit a table cell
        row = item.row()
        prop_name = self.prop_table.item(row, 0).text()
        new_value = item.text()
        self.log_output.append(f"Config Update: {prop_name} set to {new_value}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = DroneStudio()
    window.show()
    sys.exit(app.exec())