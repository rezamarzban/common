import numpy as np
from scipy.special import jv

mu0 = 4.0e-7 * np.pi          # H/m

# ---------- wire internal inductance ----------
def wire_int_inductance_per_m(f, r_wire, sigma_wire, mu_r_wire=1.0):
    omega = 2.0 * np.pi * f
    k = np.sqrt(-1.0j * omega * mu0 * mu_r_wire * sigma_wire)
    ka = k * r_wire
    if np.abs(ka) < 1e-6:
        return mu0 / (8.0 * np.pi)
    J0 = jv(0, ka)
    J1 = jv(1, ka)
    Z_int_per_m = (k / (2.0 * np.pi * r_wire * sigma_wire)) * (J0 / J1)
    return np.imag(Z_int_per_m) / omega

# ---------- coil inductance ----------
def coil_inductance(f, N_turns, loop_radius, wire_radius, sigma_wire, mu_r_wire=1.0):
    L_ext = mu0 * loop_radius * (np.log(8.0 * loop_radius / wire_radius) - 2.0)
    L_int_pm = wire_int_inductance_per_m(f, wire_radius, sigma_wire, mu_r_wire)
    wire_len = 2.0 * np.pi * loop_radius
    L_1turn = L_ext + L_int_pm * wire_len
    return N_turns * N_turns * L_1turn

# ---------- skin depth ----------
def skin_depth(f, sigma, mu_r=1.0):
    omega = 2.0 * np.pi * f
    return np.sqrt(2.0 / (omega * mu0 * mu_r * sigma))

# ---------- ground VMD factor ----------
def F_VMD(z, f, sigma):
    if sigma == 0.0 or z == 0.0:
        return 1.0 + 0.0j
    delta = skin_depth(f, sigma)
    gamma = (1.0 + 1.0j) / delta
    gz = gamma * z
    return 2.0 / (gz * gz) * (1.0 - (1.0 + gz) * np.exp(-gz))

# ---------- dipole field ----------
def dipole_H_at_point(pos, coil_pos, moment_vector):
    r = pos - coil_pos
    dist = np.linalg.norm(r)
    if dist < 1e-9:
        return np.zeros(3)
    r_hat = r / dist
    return (1.0 / (4.0 * np.pi * dist**3)) * \
           (3.0 * np.dot(moment_vector, r_hat) * r_hat - moment_vector)

# ---------- target polarizabilities (e^{jωt} convention) ----------
def alpha_sphere_nonmag(radius, f, sigma_metal):
    """
    Exact α for a non‑magnetic conducting sphere.
    The textbook formula gives α for e^{-iωt}; we conjugate it to obtain the
    e^{+jωt} version required by our reciprocity and Faraday‑law code.
    """
    omega = 2.0 * np.pi * f
    k = np.sqrt(-1.0j * omega * mu0 * sigma_metal)   # k = (1-j)/δ
    ka = k * radius
    if np.abs(ka) < 1e-6:
        return 0.0 + 0.0j
    cot_ka = np.cos(ka) / np.sin(ka)
    # Expression from the e^{-iωt} convention
    alpha_e_minus = -1.5 * np.pi * radius**3 * (1.0 - 3.0 * cot_ka / ka + 3.0 / (ka*ka))
    # Convert to e^{+jωt}
    return np.conj(alpha_e_minus)

def alpha_perfect_sphere(radius):
    """Perfect conductor (both conventions coincide for real α)."""
    return -2.0 * np.pi * radius**3

def demag_prolate(e):
    if e < 1e-12:
        return 1.0 / 3.0
    return (1.0 - e*e) / (e*e) * (0.5 / e * np.log((1.0 + e) / (1.0 - e)) - 1.0)

def effective_mu_cylinder(f, sigma, radius, mu_r):
    omega = 2.0 * np.pi * f
    k = np.sqrt(-1.0j * omega * mu0 * mu_r * sigma)
    ka = k * radius
    if np.abs(ka) < 1e-6:
        return mu_r + 0.0j
    J0 = jv(0, ka)
    J1 = jv(1, ka)
    return mu_r * (2.0 / ka) * (J1 / J0)

def alpha_rod(f, length, radius, sigma_metal, mu_r):
    """
    Prolate spheroid rod (field along length).
    Converts to e^{+jωt} via conjugation of the final χ.
    """
    a = length / 2.0
    b = radius
    if a <= b:
        raise ValueError("Length must be > diameter")
    e = np.sqrt(1.0 - (b / a)**2)
    N = demag_prolate(e)
    V = (4.0 / 3.0) * np.pi * a * b * b
    mu_eff = effective_mu_cylinder(f, sigma_metal, radius, mu_r)
    chi_e_minus = mu_eff - 1.0           # susceptibility for e^{-iωt}
    chi = np.conj(chi_e_minus)           # for e^{+jωt}
    return V * chi / (1.0 + N * chi)

# ---------- reflected impedance ----------
def reflected_impedance(f, coil_pos, coil_orient, coil_moment_per_A,
                        target_pos, target_alpha, sigma_ground=0.0):
    """
    ΔZ = j ω μ0 α |H_tx|²  (with α in e^{+jωt} convention)
    Returns dZ, dR, dL.
    """
    omega = 2.0 * np.pi * f
    dirs = {'x': np.array([1.,0.,0.]), 'y': np.array([0.,1.,0.]), 'z': np.array([0.,0.,1.])}
    m_coil = coil_moment_per_A * dirs[coil_orient]

    h = dipole_H_at_point(target_pos, coil_pos, m_coil)
    h_sq = np.dot(h, h)

    if sigma_ground > 0.0:
        F = F_VMD(target_pos[2], f, sigma_ground)
        att = F * F
    else:
        att = 1.0 + 0.0j

    dZ = 1.0j * omega * mu0 * target_alpha * h_sq * att
    dR = np.real(dZ)
    dL = np.imag(dZ) / omega
    return dZ, dL, dR

# ---------- frequency shift ----------
def frequency_shift(f_osc, L0, delta_L):
    return -0.5 * f_osc * (delta_L / L0)

# ========== Practical BFO example ==========
if __name__ == "__main__":
    f_osc = 100.0e3          # 100 kHz
    loop_diameter = 0.20     # 20 cm
    loop_radius = loop_diameter / 2.0
    wire_radius = 0.25e-3    # 0.25 mm
    sigma_copper = 5.8e7
    N_turns = 10
    coil_pos = np.array([0.0, 0.0, 0.0])

    # Target: copper sphere, radius 1 cm, depth 10 cm
    target_radius = 0.01
    target_depth = 0.10
    target_pos = np.array([0.0, 0.0, target_depth])
    sigma_soil = 0.01        # moist ground

    L0 = coil_inductance(f_osc, N_turns, loop_radius, wire_radius, sigma_copper)
    coil_area = np.pi * loop_radius**2
    moment_per_A = N_turns * coil_area

    alpha_Cu = alpha_sphere_nonmag(target_radius, f_osc, sigma_metal=5.8e7)
    dZ, dL, dR = reflected_impedance(f_osc, coil_pos, 'z', moment_per_A,
                                     target_pos, alpha_Cu, sigma_ground=sigma_soil)
    df = frequency_shift(f_osc, L0, dL)

    print("========== Practical BFO Detector (corrected) ==========")
    print(f"Frequency            : {f_osc/1e3:.0f} kHz")
    print(f"Coil: {N_turns} turns, diam {loop_diameter*100:.0f} cm, L0 = {L0*1e6:.1f} µH")
    print(f"Target: Cu sphere, r={target_radius*100:.1f} cm, depth={target_depth*100:.0f} cm")
    print(f"α = {alpha_Cu:.4e}   |α| = {abs(alpha_Cu):.3e} m³")
    print(f"Re(α) = {alpha_Cu.real:.4e}   Im(α) = {alpha_Cu.imag:.4e}")
    print(f"ΔZ = {dZ:.4e} Ω")
    print(f"ΔR = {dR:.4e} Ω   (now positive – real loss)")
    print(f"ΔL = {dL:.4e} H")
    print(f"ΔL / L0 = {dL/L0:.2e}")
    print(f"Frequency shift Δf = {df:.3f} Hz")
    print(f"Relative Δf / f    = {df/f_osc:.2e}")
    print("========================================================")