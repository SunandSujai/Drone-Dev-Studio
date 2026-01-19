import sys
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

        # 1. TOP TOOLBAR (New Feature)
        self.create_toolbar()

        # 2. CENTRAL WORKSPACE
        self.central_tabs = QTabWidget()
        self.central_tabs.setTabsClosable(True)
        self.central_tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.central_tabs)
        
        self.editor_tab = QTextEdit("// Select a file to edit...")
        self.central_tabs.addTab(self.editor_tab, "Welcome")

        # 3. PANELS
        self.create_log_panel()
        self.create_project_tree()
        self.create_hardware_panel()

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

        # 3 Columns now: Parameter | Value | Unit
        self.prop_table = QTableWidget(4, 3) 
        self.prop_table.setHorizontalHeaderLabels(["Parameter", "Value", "Unit"])
        
        # Define Data: (Name, Default Value, Unit)
        data = [
            ("Motor KV", "2400", "KV"),
            ("Max Current", "45", "A"),
            ("Battery Cells", "6", "S"),
            ("Frame Weight", "650", "g")
        ]

        for row, (name, val, unit) in enumerate(data):
            # Column 0: Parameter Name (Read-Only)
            item_name = QTableWidgetItem(name)
            item_name.setFlags(item_name.flags() ^ Qt.ItemFlag.ItemIsEditable) # Remove edit flag
            self.prop_table.setItem(row, 0, item_name)

            # Column 1: Value (Editable)
            self.prop_table.setItem(row, 1, QTableWidgetItem(val))

            # Column 2: Unit (Read-Only)
            item_unit = QTableWidgetItem(unit)
            item_unit.setFlags(item_unit.flags() ^ Qt.ItemFlag.ItemIsEditable) # Remove edit flag
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
        self.log_output.append("📡 Syncing parameters...")

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