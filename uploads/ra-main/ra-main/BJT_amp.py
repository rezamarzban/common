import cmath, math

# Antenna and biasing constants
E_field = 1.0           # V/m
L_wire = 0.70           # m
h_eff = L_wire / 2.0    # m
V_oc = E_field * h_eff  # V RMS
C_ant = 5e-12           # F
V_CC = 9.0
I_C = 1e-3
V_CE_target = 4.5
R_C_exact = (V_CC - V_CE_target) / I_C
R_C_std = 4700.0        # nearest E24
V_CE = V_CC - I_C * R_C_std
V_BE = 0.7
gm = I_C / 0.026         # 0.03846 S
A_v_mag = gm * R_C_std   # ~181

# Standard E24 resistor values (1.0 to 9.1 in 10^n)
e24 = [1.0,1.1,1.2,1.3,1.5,1.6,1.8,2.0,2.2,2.4,2.7,3.0,3.3,3.6,3.9,4.3,4.7,5.1,5.6,6.2,6.8,7.5,8.2,9.1]
def nearest_e24(val):
    if val <= 0: return 1.0
    exp = math.floor(math.log10(val))
    mant = val / (10**exp)
    best = min(e24, key=lambda x: abs(x-mant))
    return best * (10**exp)

# Frequencies of interest (Hz)
freqs = [1e6, 10e6, 50e6, 88e6, 100e6, 108e6, 150e6]

# List of transistors: (name, f_T(Hz), C_mu(F), hFE_dc_typ)
transistors = [
    ("2N3904",  300e6, 4.0e-12, 150),
    ("2N2222A", 300e6, 8.0e-12, 150),
    ("BC547",   150e6, 4.5e-12, 200),
    ("BC548",   150e6, 4.5e-12, 200),
    ("BC549",   150e6, 4.5e-12, 300),
    ("2N4401",  250e6, 6.5e-12, 150),
    ("2N5088",   50e6, 4.0e-12, 500),
    ("2N5089",   50e6, 2.0e-12, 800),
    ("MPSA18",  100e6, 2.0e-12, 800),
    ("2N5551",  100e6, 6.0e-12, 150),
    ("S9014",   150e6, 3.5e-12, 300),
    ("S9018",   700e6, 1.7e-12, 100),
    ("BF199",   550e6, 1.6e-12, 100),
    ("BF494",   200e6, 1.6e-12, 80),
    ("2SC1815",  80e6, 3.5e-12, 200),
    ("2SC945",  150e6, 3.0e-12, 200),
    ("2N2369A", 500e6, 4.0e-12, 60),
    ("2SC2712",  80e6, 2.0e-12, 150),
    ("2N3903",  250e6, 4.0e-12, 100),
    ("2N4124",  300e6, 4.0e-12, 200),
]

print("=== BJT Amplifier Performance with 70cm Wire Antenna at 1 V/m ===")
print(f"Antenna: h_eff={h_eff:.2f}m, V_oc={V_oc*1000:.1f}mV RMS, C_ant={C_ant*1e12:.0f}pF")
print(f"Biasing: V_CC={V_CC}V, I_C={I_C*1000}mA, R_C={R_C_std/1000:.1f}kOhm, V_CE≈{V_CE:.2f}V")
print(f"Low-frequency voltage gain magnitude: {A_v_mag:.1f}\n")

for name, fT, Cmu, hFE in transistors:
    I_B = I_C / hFE
    R_B_exact = (V_CE_target - V_BE) / I_B   # using target V_CE=4.5V
    R_B_std = nearest_e24(R_B_exact)
    # Use actual V_CE for calculations (slightly different due to R_C_std)
    V_CE_actual = V_CC - I_C * R_C_std
    # Compute C_pi from fT
    Cpi = gm/(2*math.pi*fT) - Cmu
    if Cpi < 0:
        Cpi = 0.0
    C_miller = Cmu * (1 + A_v_mag)
    C_in = Cpi + C_miller

    print(f"--- {name}: fT={fT/1e6:.0f}MHz, Cmu={Cmu*1e12:.1f}pF, hFE={hFE} ---")
    print(f"    R_B exact={R_B_exact/1e3:.1f}k, nearest E24={R_B_std/1e3:.1f}k")
    print(f"    C_pi={Cpi*1e12:.1f}pF, C_miller={C_miller*1e12:.1f}pF, C_in={C_in*1e12:.1f}pF")
    for f in freqs:
        omega = 2*math.pi*f
        beta_ac = fT / f
        r_pi = beta_ac / gm
        Z_ant = 1/(1j*omega*C_ant)
        Z_in = 1/(1/r_pi + 1j*omega*C_in)
        V_base = V_oc * Z_in / (Z_ant + Z_in)
        v_out = A_v_mag * abs(V_base)
        print(f"    f={f/1e6:5.1f}MHz: |Z_ant|={abs(Z_ant):7.1f}Ω, |Z_in|={abs(Z_in):6.2f}Ω, "
              f"|V_base|={abs(V_base)*1000:5.2f}mV, v_out={v_out*1000:6.1f}mV RMS")
    print()