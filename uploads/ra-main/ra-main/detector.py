import numpy as np
from scipy.special import jv   # Bessel function for complex arguments

# ---------- physical constants ----------
mu0 = 4.0 * np.pi * 1e-7          # H/m

# ---------- soil & wave functions ----------
def skin_depth(f, sigma, mu_r=1.0):
    """skin depth δ (m) for a conductor"""
    omega = 2.0 * np.pi * f
    return np.sqrt(2.0 / (omega * mu0 * mu_r * sigma))

def gamma_soil(f, sigma):
    """propagation constant γ in soil (m⁻¹)"""
    delta = skin_depth(f, sigma, mu_r=1.0)
    return (1.0 + 1.0j) / delta

def F_VMD(z, f, sigma):
    """
    Field transmission factor for a vertical magnetic dipole
    on a homogeneous half‑space.
    z = depth (m), positive downward.
    Returns complex factor (free‑space reference = 1.0)
    """
    if sigma == 0.0 or z == 0.0:
        return 1.0 + 0.0j
    gamma = gamma_soil(f, sigma)
    gz = gamma * z
    F = 2.0 / (gz * gz) * (1.0 - (1.0 + gz) * np.exp(-gz))
    return F

# ---------- magnetic dipole field ----------
def dipole_H_at_point(pos, coil_pos, moment_vector):
    """
    Magnetic field H (A/m) per unit current at position pos
    from a magnetic dipole at coil_pos with moment vector.
    moment_vector = N * A * unit_direction (m²)
    """
    r = pos - coil_pos
    dist = np.linalg.norm(r)
    if dist < 1e-9:
        return np.zeros(3)
    r_hat = r / dist
    # Dipole field: (1/(4π r³)) [ 3 (m·r̂) r̂ - m ]
    return (1.0 / (4.0 * np.pi * dist**3)) * \
           (3.0 * np.dot(moment_vector, r_hat) * r_hat - moment_vector)

# ---------- target polarizabilities ----------
def alpha_perfect_sphere(radius):
    """Perfect conductor sphere (high‑freq limit)"""
    return -2.0 * np.pi * radius**3

def alpha_sphere_nonmag(radius, f, sigma_metal):
    """Exact α for a non‑magnetic conducting sphere (any frequency)"""
    omega = 2.0 * np.pi * f
    k = np.sqrt(-1.0j * omega * mu0 * sigma_metal)
    ka = k * radius
    if np.abs(ka) < 1e-6:
        return 0.0 + 0.0j
    cot_ka = np.cos(ka) / np.sin(ka)
    return -1.5 * np.pi * radius**3 * (1.0 - 3.0 * cot_ka / ka + 3.0 / (ka * ka))

# --- prolate spheroid (rod) ---
def demag_prolate(e):
    """Demagnetising factor along major axis of prolate spheroid"""
    if e < 1e-12:
        return 1.0 / 3.0
    return (1.0 - e*e) / (e*e) * (0.5 / e * np.log((1.0 + e) / (1.0 - e)) - 1.0)

def effective_mu_cylinder(f, sigma, radius, mu_r):
    """Complex effective permeability of an infinite cylinder in axial field"""
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
    length = full rod length (m), radius = minor semi‑axis (m).
    """
    a = length / 2.0          # semi‑major axis
    b = radius
    if a <= b:
        raise ValueError("Length must be greater than diameter for a prolate spheroid.")
    e = np.sqrt(1.0 - (b / a)**2)
    N = demag_prolate(e)
    V = (4.0 / 3.0) * np.pi * a * b * b
    mu_eff = effective_mu_cylinder(f, sigma_metal, radius, mu_r)
    chi = mu_eff - 1.0
    return V * chi / (1.0 + N * chi)

# --- oblate spheroid (disc) ---
def demag_oblate(e):
    """Demagnetising factor along minor axis of oblate spheroid"""
    if e < 1e-12:
        return 1.0 / 3.0
    return (1.0 / (e*e)) * (1.0 - np.sqrt(1.0 - e*e) / e * np.arcsin(e))

def alpha_disc(f, radius, thickness, sigma_metal, mu_r):
    """
    Oblate spheroid disc, field perpendicular to the face.
    radius = disc radius (major semi‑axis), thickness = full thickness.
    """
    a = thickness / 2.0       # minor semi‑axis
    c = radius                # major semi‑axis
    if c <= a:
        raise ValueError("Disc radius must be greater than half thickness.")
    e = np.sqrt(1.0 - (a / c)**2)
    N = demag_oblate(e)
    V = (4.0 / 3.0) * np.pi * a * c * c
    if sigma_metal > 0.0:
        # Perfect‑conductor approximation for highly conducting disc
        return -V / N
    else:
        chi = mu_r - 1.0
        return V * chi / (1.0 + N * chi)

# ---------- unified receiver voltage ----------
def receiver_voltage(f, tx_pos, tx_orient, tx_moment_per_A,
                     rx_pos, rx_orient, rx_moment_per_A,
                     target_pos, target_alpha,
                     sigma_ground=0.0, I_T=1.0):
    """
    Returns complex open‑circuit voltage V_R for given Tx current I_T.
    Positions in metres; z positive downward (surface at 0).
    tx_orient / rx_orient : 'x','y','z' (unit directions).
    tx_moment_per_A = N_tx * A_tx
    rx_moment_per_A = N_rx * A_rx
    target_alpha : complex polarizability (m³)
    sigma_ground : soil conductivity (S/m), 0 = free space.
    """
    omega = 2.0 * np.pi * f
    dirs = {'x': np.array([1., 0., 0.]),
            'y': np.array([0., 1., 0.]),
            'z': np.array([0., 0., 1.])}
    m_tx = tx_moment_per_A * dirs[tx_orient]
    m_rx = rx_moment_per_A * dirs[rx_orient]

    # Magnetic fields per unit current at target
    H_tx = dipole_H_at_point(target_pos, tx_pos, m_tx)
    h_rx = dipole_H_at_point(target_pos, rx_pos, m_rx)

    # Free‑space voltage (without ground)
    V_free = -1.0j * omega * mu0 * target_alpha * np.dot(H_tx, h_rx) * I_T

    # Ground attenuation (two‑way)
    if sigma_ground > 0.0:
        z = target_pos[2]        # depth
        F_down = F_VMD(z, f, sigma_ground)
        # approximate round‑trip factor
        V_ground = V_free * (F_down * F_down)
        return V_ground
    else:
        return V_free

# ---------- example run ----------
if __name__ == "__main__":
    # Geometry (same as earlier discussion)
    tx_pos   = np.array([0.0, 0.0, 0.0])      # transmitter on surface
    rx_pos   = np.array([0.5, 0.0, 0.0])      # receiver on surface (slightly raised in earlier text; here at surface)
    target_pos = np.array([0.25, 0.3, 1.0])   # 1 m depth

    f = 10.0e3           # 10 kHz
    sigma_soil = 0.01    # moist soil (S/m)

    # Coil parameters: N1=10, A_T=0.196 m² ; N2=10, A_R=0.0314 m²
    N_tx, A_tx = 10, 0.196
    N_rx, A_rx = 10, 0.0314

    # Target 1: iron rod (1 cm diameter, 1 m long)
    rod_length = 1.0
    rod_radius = 0.005   # 0.5 cm radius
    sigma_iron = 1.0e7   # S/m
    mu_iron = 100.0      # relative permeability

    alpha_rod_val = alpha_rod(f, rod_length, rod_radius, sigma_iron, mu_iron)

    V_rod = receiver_voltage(f, tx_pos, 'z', N_tx * A_tx,
                             rx_pos, 'y', N_rx * A_rx,
                             target_pos, alpha_rod_val,
                             sigma_ground=sigma_soil)

    print("=== Iron rod (1 m x 1 cm) at 1 m depth, 10 kHz ===")
    print(f"|alpha| = {abs(alpha_rod_val):.4e} m³")
    print(f"V_R (peak) = {abs(V_rod):.4e} V, phase = {np.angle(V_rod, deg=True):.1f}°")

    # Target 2: perfect sphere, 10 cm radius
    alpha_sph = alpha_perfect_sphere(0.1)
    V_sph = receiver_voltage(f, tx_pos, 'z', N_tx * A_tx,
                             rx_pos, 'y', N_rx * A_rx,
                             target_pos, alpha_sph,
                             sigma_ground=sigma_soil)

    print("\n=== 10 cm perfect sphere at 1 m depth, 10 kHz ===")
    print(f"|alpha| = {abs(alpha_sph):.4e} m³")
    print(f"V_R (peak) = {abs(V_sph):.4e} V, phase = {np.angle(V_sph, deg=True):.1f}°")

    # Target 3: thin aluminium disc (radius 10 cm, thickness 1 mm)
    disc_radius = 0.1
    disc_thickness = 0.001
    sigma_al = 3.5e7   # S/m
    mu_al = 1.0
    alpha_disc_val = alpha_disc(f, disc_radius, disc_thickness, sigma_al, mu_al)
    V_disc = receiver_voltage(f, tx_pos, 'z', N_tx * A_tx,
                              rx_pos, 'y', N_rx * A_rx,
                              target_pos, alpha_disc_val,
                              sigma_ground=sigma_soil)

    print("\n=== Aluminium disc (20 cm dia, 1 mm thick) at 1 m depth, 10 kHz ===")
    print(f"|alpha| = {abs(alpha_disc_val):.4e} m³")
    print(f"V_R (peak) = {abs(V_disc):.4e} V, phase = {np.angle(V_disc, deg=True):.1f}°")