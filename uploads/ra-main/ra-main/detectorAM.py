import numpy as np

# ---------- physical constants ----------
epsilon_0 = 8.854187817e-12   # F/m
mu_0      = 4.0e-7 * np.pi    # H/m

# ---------- parameters ----------
# 555 oscillator
V_CC = 9.0            # supply voltage (V)
f0   = 100.0e3        # fundamental frequency (Hz)
n    = 7              # harmonic number (must be odd)
h_eff = 0.05          # effective length of the radiating trace (m)

# geometry
d_metal_to_trace = 0.05   # distance from 555 trace to metal object (m)
L     = 1.0               # length of metal rod (m)
a_rod = 0.005             # radius of rod (m)  (diameter = 1 cm)
r     = 0.3               # distance from rod to AM radio (m)
theta = 90.0              # angle between rod axis and line to radio (deg)

# AM radio ferrite rod
mu_eff = 50.0             # effective relative permeability of ferrite
N_rx   = 80               # number of turns in antenna coil
A_rod  = 1.0e-4           # cross‑sectional area of ferrite core (m²)  (1 cm²)

# ---------- derived quantities ----------
f_harm = n * f0                     # frequency of the harmonic (Hz)
omega = 2.0 * np.pi * f_harm

# 1. Harmonic voltage amplitude
V_n = (2.0 * V_CC) / (n * np.pi)
print(f"Harmonic n={n}: f = {f_harm/1e3:.1f} kHz,  V_n = {V_n:.2f} V")

# 2. Incident electric field at the metal (short electric dipole approximation)
E_inc = (V_n * h_eff) / (2.0 * np.pi * d_metal_to_trace**3)
print(f"Incident E‑field at metal: {E_inc:.2f} V/m")

# 3. Electric polarizability of the rod (perfect conductor, prolate spheroid)
#    Volume of rod
V_rod = np.pi * a_rod**2 * L
#    Demagnetisation factor along the major axis (slender rod)
if L > a_rod:
    N_d = (4.0 * a_rod**2 / L**2) * (np.log(L / a_rod) - 1.0)
else:
    N_d = 1.0/3.0    # fallback for a sphere
print(f"Rod volume: {V_rod:.3e} m³,  N_d = {N_d:.4f}")

alpha_e = V_rod / N_d          # electric polarizability (m³)
print(f"Electric polarizability α_e = {alpha_e:.3e} m³")

# 4. Induced electric dipole moment
p = epsilon_0 * alpha_e * E_inc      # C·m
print(f"Induced dipole moment p = {p:.3e} C·m")

# 5. Magnetic near‑field at the radio
theta_rad = np.deg2rad(theta)
H_phi = (omega * p * np.sin(theta_rad)) / (4.0 * np.pi * r**2)
print(f"Magnetic field at radio: H_φ = {H_phi:.3e} A/m")

# 6. Open‑circuit voltage in the ferrite rod antenna
V_rx = omega * mu_0 * mu_eff * N_rx * A_rod * H_phi
print(f"Received open‑circuit voltage V_rx = {V_rx:.3e} V  ({V_rx*1e6:.2f} µV)")

# ---------- sensitivity check ----------
if V_rx > 1e-6:
    print("\nSignal is well above typical AM radio sensitivity (~1 µV). Clearly audible.")
elif V_rx > 1e-7:
    print("\nSignal is around 0.1–1 µV. Might be detectable with a quiet receiver.")
else:
    print("\nSignal is below 0.1 µV. Probably undetectable unless very low noise.")