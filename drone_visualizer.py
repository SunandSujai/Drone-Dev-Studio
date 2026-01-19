import pyqtgraph.opengl as gl
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt
from physics_engine import DronePhysics

class DroneVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        
        # 1. Simulation State
        self.throttle = 0.0      
        self.altitude = 0.0      
        self.velocity = 0.0      
        self.params = None       # Will be set by DroneStudio when 'Run' is clicked
        
        # 2. UI Layout & Overlay
        self.layout = QVBoxLayout(self)
        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor('#1a1a1a')
        self.layout.addWidget(self.view)
        
        # Top-Right HUD for Throttle/Altitude
        self.hud = QLabel("Throttle: 0% | Altitude: 0.00m", self)
        self.hud.setStyleSheet("""
            color: #00ff00; 
            font-family: 'Consolas', monospace; 
            font-size: 18px; 
            background: rgba(0, 0, 0, 150); 
            padding: 10px;
            border: 1px solid #00ff00;
        """)
        self.hud.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # 3. 3D Environment
        grid = gl.GLGridItem()
        grid.scale(2, 2, 1)
        self.view.addItem(grid)

        # 4. The Unit Cube (The Drone)
        self.create_cube()

        # 5. Physics Timer (60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_physics_step)

    def create_cube(self):
        # Define vertices for a 1x1x1 unit cube
        verts = np.array([
            [0,0,0], [1,0,0], [1,1,0], [0,1,0],
            [0,0,1], [1,0,1], [1,1,1], [0,1,1]
        ]) - 0.5 # Center the cube
        
        faces = np.array([
            [0,1,2], [0,2,3], [4,5,6], [4,6,7], # Bottom/Top
            [0,1,5], [0,5,4], [1,2,6], [1,6,5], # Sides
            [2,3,7], [2,7,6], [3,0,4], [3,4,7]
        ])
        
        self.drone_mesh = gl.GLMeshItem(
            vertexes=verts, faces=faces, 
            color=(0.1, 0.5, 0.9, 0.8), 
            drawEdges=True, edgeColor=(1, 1, 1, 1)
        )
        self.view.addItem(self.drone_mesh)

    def start_sim(self, drone_data):
        self.params = drone_data
        self.timer.start(16) # ~60 FPS
        self.setFocus()      # Ensure this widget catches key presses

    def run_physics_step(self):
        if not self.params: return

        # Instantiate physics to get max thrust for current hardware
        engine = DronePhysics(
            self.params['kv'], self.params['cells'], 
            self.params['weight'], self.params['diam'], self.params['pitch']
        )
        stats = engine.compute_flight_stats()
        
        # Force Calculation
        max_thrust = stats['Total Thrust (g)']
        weight = self.params['weight']
        current_thrust = (self.throttle / 100.0) * max_thrust
        
        # Net Acceleration (including Gravity)
        # 9.81 converts the unitless G-ratio into meters/second^2
        acceleration = ((current_thrust - weight) / weight) * 9.81
        
        # Integration (dt = 0.016 seconds)
        dt = 0.016
        self.velocity += acceleration * dt
        self.altitude += self.velocity * dt
        
        # Ground Collision Check
        if self.altitude <= 0:
            self.altitude = 0
            self.velocity = 0

        # Update HUD and 3D Position
        self.drone_mesh.resetTransform()
        self.drone_mesh.translate(0, 0, self.altitude)
        self.hud.setText(f"Throttle: {int(self.throttle)}% | Altitude: {self.altitude:.2f}m")
        self.hud.adjustSize()
        self.hud.move(self.width() - self.hud.width() - 20, 20) # Keep in top-right

    def keyPressEvent(self, event):
        # Standard Flight Simulator Controls
        if event.key() == Qt.Key.Key_Up:
            self.throttle = min(100.0, self.throttle + 2.0)
        elif event.key() == Qt.Key.Key_Down:
            self.throttle = max(0.0, self.throttle - 2.0)