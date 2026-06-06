import math

# ====================== CONSTANTS ======================
mu0 = 4 * math.pi * 1e-7          # H/m
epsilon0 = 8.854187817e-12        # F/m
c = 3e8                           # speed of light

# Typical ferrite rod parameters for Aiwa-style 6-transistor radio
mu_eff = 120
N_rx = 120
A_rod = 6e-5                      # m² (approx 8mm diameter rod)

# Pico transmitter parameters
V_CC = 3.3                        # volts
l_tx = 0.15                       # transmitter wire length (m)
f0 = 550_000                      # fundamental frequency (Hz)
n = 1                             # harmonic number (1 = fundamental)

# Stray capacitance of transmitter wire/trace
C_s = 8e-12                       # ~8 pF (reasonable for 15cm wire + GPIO)

# ====================== SURFACE-TO-UNDERGROUND GEOMETRY ======================
# The transmitter is at the surface origin (0, 0).
# The object is buried directly beneath a point x_tx meters away.
# The radio sits further down the surface at distance x_rx from the object's surface projection.
depth = 0.50                      # Depth of the iron object underground (m)
x_tx = 0.60                       # Horizontal distance from transmitter to object projection (m)
x_rx = 0.90                       # Horizontal distance from object projection to AM Radio (m)

# Calculate slant distances using Pythagoras
d_slant = math.sqrt(x_tx**2 + depth**2)  # Transmitter to underground object (m)
r_slant = math.sqrt(x_rx**2 + depth**2)  # Underground object to AM radio (m)

# Direct path distance across the surface (Transmitter straight to Radio)
r_direct = x_tx + x_rx 

# ====================== HELPER FUNCTIONS ======================
def omega(n, f0):
    return 2 * math.pi * n * f0

# ====================== DIRECT MODEL (No Metal) ======================
def calculate_direct_Vrx(V_CC, l_tx, f0, n, r):
    """Direct near-field coupling from transmitter wire to radio across the surface"""
    # Using V_CC/2 as the peak driving voltage amplitude for unipolar square wave harmonics
    I0 = (V_CC / 2) * omega(n, f0) * (40e-12 * l_tx)   # approx current, C_ant ~40 pF/m
    H = (I0 * l_tx) / (4 * math.pi * r**2)              # near-field H (broadside)
    V_rx = omega(n, f0) * mu0 * mu_eff * N_rx * A_rod * H
    return V_rx

# ====================== RE-RADIATION MODEL (With Metal) ======================
def calculate_reradiation_Vrx(V_CC, l_tx, f0, n, r, d, alpha_e, C_s, cos_phi=1.0, sin_theta=1.0):
    """Re-radiation via buried metal object using slant distances"""
    # The derived formula implicitly handles Vn substitution and omega cancellation
    prefactor = (mu0 * mu_eff * N_rx * A_rod * alpha_e * C_s) / (2 * math.pi)
    V_rx = prefactor * n * (f0**2) * V_CC * l_tx * cos_phi * sin_theta / (r**2 * d**3)
    return V_rx

# ====================== POLARIZABILITY α_e FOR DIFFERENT SHAPES ======================
def alpha_rod(L, a=0.002):          # L = length, a = radius (e.g., 4mm diameter rebar/nail)
    """Thin conducting rod (prolate spheroid approximation)"""
    if L < 2*a:
        return 0
    return (4*math.pi/3) * (L**3) / (math.log(2*L/a) - 1)

def alpha_disc(R):
    """Thin conducting disk"""
    return (8/3.0) * R**3

# ====================== MAIN CALCULATION ======================
print("=== SURFACE-TO-UNDERGROUND COUPLING COMPARISON ===\n")
print(f"Transmitter: {V_CC}V, {l_tx*100:.1f}cm wire @ {f0/1000} kHz (n={n})")
print(f"Object Burial Depth: {depth} m")
print(f"Surface Distance (Tx to Radio): {r_direct} m")
print(f"Slant Distance Tx->Object (d):  {d_slant:.3f} m")
print(f"Slant Distance Object->Rx (r):  {r_slant:.3f} m\n")

# Sample iron/steel metal objects buried underground
objects = [
    ("No Metal (Direct Path Surface)", 0, 0),
    ("Buried Iron Coin (Disc R=1.5cm)", alpha_disc(0.015), 1),
    ("Buried Spike/Nail (Rod L=10cm)", alpha_rod(0.10), 1),
    ("Buried Rebar Section (Rod L=40cm)", alpha_rod(0.40), 1),
    ("Buried Metal Plate (Disc R=12cm)", alpha_disc(0.12), 1),
]

print(f"{'Object Profile':35} | {'Model Used':12} | {'Induced V_rx':12}")
print("-" * 67)

for name, alpha_e, model_type in objects:
    if model_type == 0:  # Direct surface coupling
        V_rx = calculate_direct_Vrx(V_CC, l_tx, f0, n, r_direct)
        model = "DIRECT"
    else:  # Re-radiation through the ground asset
        V_rx = calculate_reradiation_Vrx(V_CC, l_tx, f0, n, r_slant, d_slant, alpha_e, C_s)
        model = "RE-RADIATION"
    
    print(f"{name:35} | {model:12} | {V_rx*1e6:8.3f} µV")