import math

class DronePhysics:
    """
    Advanced Physics Engine v1.1
    Now accounts for Propeller Geometry (Diameter & Pitch)
    """
    def __init__(self, motor_kv, battery_cells, weight_g, prop_diameter, prop_pitch):
        self.kv = motor_kv
        self.cells = battery_cells
        self.weight = weight_g
        self.diameter = prop_diameter
        self.pitch = prop_pitch

    def get_voltage(self):
        # 3.7V is nominal, 4.2V is peak. We use 3.8V for a realistic "loaded" voltage.
        return self.cells * 3.8

    def calculate_max_thrust(self):
        """
        Calculates total thrust using RPM and Propeller Geometry.
        Scaling Law: Thrust increases with Diameter cubed (D^3).
        """
        voltage = self.get_voltage()
        
        # 1. Calculate Theoretical RPM (Efficiency included as 80%)
        # As props get bigger, motors struggle more, so we lower efficiency slightly
        efficiency = 0.80
        rpm = self.kv * voltage * efficiency
        
        # 2. The Thrust Formula (Derived from empirical RC data)
        # Base constant roughly calibrated for 2-blade propellers
        # Formula: T ~ RPM^2 * Diameter^3 * Pitch
        
        # We normalize to thousands of RPM for manageable numbers
        rpm_k = rpm / 1000
        
        # Coefficients:
        # 5.3e-9 is a standard aerodynamic coefficient for this unit mix
        # But we will use a "Baseline Scaling" method which is safer for standard drones:
        
        # Baseline: A 5x4.5 prop at 25,000 RPM produces ~600g thrust.
        # We scale everything relative to that baseline.
        
        base_rpm = 25.0 # 25k
        base_diam = 5.0
        base_pitch = 4.5
        base_thrust = 600.0
        
        thrust_factor = ((rpm_k / base_rpm)**2) * \
                        ((self.diameter / base_diam)**3) * \
                        ((self.pitch / base_pitch)**1)
                        
        single_motor_thrust = base_thrust * thrust_factor
        
        return single_motor_thrust * 4

    def compute_flight_stats(self):
        total_thrust = self.calculate_max_thrust()
        twr = total_thrust / self.weight
        
        # Calculate Hover:
        if total_thrust > self.weight:
            hover_throttle = (self.weight / total_thrust) * 100
        else:
            hover_throttle = 100

        # Estimated Flight Time (Simple Amp-Draw Model)
        # Assuming battery is 1300mAh (default reference)
        # This is a placeholder for when we add Battery Capacity to UI
        
        return {
            "Total Thrust (g)": round(total_thrust, 2),
            "TWR (Ratio)": round(twr, 2),
            "Hover Throttle (%)": round(hover_throttle, 1),
            "Voltage (V)": round(self.get_voltage(), 1),
            "Motor RPM": int(self.kv * self.get_voltage() * 0.8)
        }