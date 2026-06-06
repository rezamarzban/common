import numpy as np
import math

# --------------------------
# Global inputs (user values)
# --------------------------
Q = 100.0       # supplied heat (W)
A = 0.1         # area (m^2)
R = 8.314       # universal gas constant J/(mol K)
Tinf = 298.0    # ambient temperature (K)
n_exp = 1.75    # exponent for D(T) correction
Tref = 298.0    # reference temperature for Dref (K)

# --------------------------
# Liquid dataset (name, M(kg/mol), h_fg(J/kg), Ts(K), Dref(m2/s))
# --------------------------
L = np.array([
("Gasoline",0.114,3.0e5,373.0,7.38e-6),
("Diesel",0.200,2.5e5,550.0,6.0e-6),
("Kerosene",0.170,2.7e5,520.0,6.5e-6),
("Ethanol",0.04607,9.19e5,351.4,1.19e-5),
("Methanol",0.03204,1.165e6,337.9,1.75e-5),
("Isopropanol",0.0601,7.68e5,355.4,1.02e-5),
("Toluene",0.09214,4.13e5,383.6,1.69e-5),
("Benzene",0.07811,3.94e5,353.3,1.60e-5),
("Hexane",0.08618,3.65e5,341.9,1.51e-5),
("Heptane",0.1002,3.18e5,371.6,1.30e-5),
("Pentane",0.07215,3.67e5,309.3,1.88e-5),
("Acetone",0.05808,5.18e5,329.3,1.30e-5),
("MEK",0.07211,5.00e5,352.7,1.15e-5),
("Jet Fuel",0.160,2.6e5,540.0,6.2e-6),
("Crude Oil",0.220,2.3e5,600.0,5.5e-6),
("Engine Oil SAE30",0.400,2.0e5,650.0,4.0e-6),
("Engine Oil SAE40",0.450,1.9e5,680.0,3.8e-6),
("Motor Oil 5W-30",0.420,2.0e5,660.0,3.9e-6),
("Hydraulic Oil",0.390,2.1e5,640.0,4.2e-6),
# Added liquids
("Water",0.018015,2.26e6,373.15,2.6e-5),
("n-Butanol",0.07412,6.9e5,391.0,1.2e-5),
("Cyclohexane",0.08416,3.5e5,353.6,1.1e-5)
], dtype=object)

# --------------------------
# Optional Antoine database (A,B,C) for log10(p_mmHg) -- add/replace as needed
# --------------------------
antoine_db = {
    "Ethanol": (8.20417, 1642.89, 230.3),
    "Methanol": (8.08097, 1582.271, 239.726),
    "Isopropanol": (8.95464, 2161.0, 230.0),
    "Toluene": (6.95464, 1344.8, 219.48),
    "Benzene": (6.90565, 1211.033, 220.79),
    "Hexane": (6.8763, 1171.53, 224.0),
    "Heptane": (6.89366, 1264.04, 216.402),
    "Pentane": (6.85215, 1064.84, 233.9),
    "Acetone": (7.02447, 1161.0, 224.0),
    "MEK": (7.04412, 1203.835, 229.13),
    "Water": (8.07131, 1730.63, 233.426)
}
MMHG_TO_PA = 133.322368421052

# --------------------------
# Functions (all equations implemented as functions)
# --------------------------
def p_vap_from_antoine(name: str, T_k: float):
    """Return vapor pressure in Pa using Antoine (if available). T_k in K.
       Antoine: log10(p_mmHg) = A - B/(T_C + C) where T_C = T_k - 273.15
       Returns None if Antoine constants not present for 'name'."""
    if name not in antoine_db:
        return None
    A, B, C = antoine_db[name]
    T_c = T_k - 273.15
    p_mmHg = 10.0 ** (A - B / (T_c + C))
    return p_mmHg * MMHG_TO_PA

def p_vap_clausius(h_fg_Jperkg: float, M_kgpermol: float, T_k: float, Tb_k: float):
    """Clausius-Clapeyron approximate vapor pressure at T_k using latent heat and known Tb_k where p(Tb)=1 atm.
       ΔH_molar = h_fg * M (J/mol)
       ln(p/p0) = -ΔH_molar/R * (1/T - 1/Tb)
       p0 assumed 101325 Pa at Tb_k."""
    deltaH_molar = h_fg_Jperkg * M_kgpermol  # J/mol
    p0 = 101325.0
    exponent = - (deltaH_molar / R) * (1.0 / T_k - 1.0 / Tb_k)
    return p0 * math.exp(exponent)

def Cs_from_p(p_vap_Pa: float, M_kgpermol: float, T_k: float):
    """Vapor concentration (mass concentration, kg/m^3) from partial pressure using ideal gas:
       Cs = p_vap * M / (R * T)"""
    return (p_vap_Pa * M_kgpermol) / (R * T_k)

def D_temp_correction(Dref_m2s: float, Tf_K: float, Tref_K: float = Tref, exponent: float = n_exp):
    """Temperature correction for diffusion coefficient: D = Dref * (Tf/Tref)^n"""
    return Dref_m2s * (Tf_K / Tref_K) ** exponent

def delta_from_energy(D_m2s: float, Cs_kgperm3: float, A_m2: float, h_fg_Jperkg: float, Q_W: float):
    """Characteristic thickness δ (m) from combined diffusion+energy equation:
       δ = D * Cs * A * h_fg / Q"""
    return D_m2s * Cs_kgperm3 * A_m2 * h_fg_Jperkg / Q_W

def mass_flux_from_delta(D_m2s: float, Cs_kgperm3: float, delta_m: float):
    """Mass flux J (kg/m2/s) from diffusion: J = D * Cs / delta"""
    if delta_m <= 0:
        return float('inf')
    return D_m2s * Cs_kgperm3 / delta_m

def m_dot_from_Q(Q_W: float, h_fg_Jperkg: float):
    """Evaporation mass flow (kg/s) from supplied heat: m_dot = Q / h_fg"""
    if h_fg_Jperkg <= 0:
        return float('inf')
    return Q_W / h_fg_Jperkg

# --------------------------
# Main loop: compute for each liquid
# --------------------------
names = L[:,0]
M, h_fg, Ts_list, Dref = L[:,1:].astype(float).T

# Use surface temperature = Ts by default; change if you have another T_surf
T_surf_list = Ts_list.copy()

# film temperature for diffusion correction (Tf = (T_surf + Tinf)/2)
Tf_list = (T_surf_list + Tinf) / 2.0
D_corrected = np.array([D_temp_correction(Dref[i], Tf_list[i]) for i in range(len(Dref))])

# Compute results
results = []
for i, name in enumerate(names):
    name = str(name)
    Mi = M[i]
    hi = h_fg[i]
    T_surf = T_surf_list[i]
    Di = D_corrected[i]

    # 1) vapor pressure (Antoine if available else Clausius)
    p_vap = p_vap_from_antoine(name, T_surf)
    source = "Antoine" if p_vap is not None else "Clausius"
    if p_vap is None:
        # Use Clausius with Tb assumed equal to Ts in dataset (p(Tb)=1 atm)
        # If you know a different reference boiling temp Tb or p(Tb), change here.
        Tb = Ts_list[i]
        p_vap = p_vap_clausius(hi, Mi, T_surf, Tb)

    # 2) concentration Cs (kg/m^3)
    Cs = (p_vap * Mi) / (R * T_surf)

    # 3) delta using energy-diffusion combination
    delta = delta_from_energy(Di, Cs, A, hi, Q)

    # 4) mass flux (from delta) and mass flow from Q
    J = mass_flux_from_delta(Di, Cs, delta)
    m_dot_Q = m_dot_from_Q(Q, hi)

    results.append({
        "name": name,
        "p_vap_Pa": p_vap,
        "Cs_kgperm3": Cs,
        "D_m2s": Di,
        "delta_m": delta,
        "J_kg_m2s": J,
        "m_dot_Q_kg_s": m_dot_Q,
        "p_source": source
    })

# Print nicely
print("\nResults (δ in mm, Cs in kg/m^3, p_vap in Pa):\n")
for r in results:
    print(f"{r['name']:18} δ = {r['delta_m']*1000:7.2f} mm | p_vap = {r['p_vap_Pa']:8.1f} Pa ({r['p_source']}) | Cs = {r['Cs_kgperm3']:7.4f} kg/m^3 | D = {r['D_m2s']:.3e} m2/s")

# End of script
