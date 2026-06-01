This single Python script calculates the performance of all the common JFET transistors discussed earlier, for a range of frequencies from the AM broadcast band up through the FM band. The circuit is the simple common‑source amplifier with a 30 cm wire antenna, a gate‑to‑ground resistor, a drain load resistor, and a 9 V supply. The field strength is 0.05 V/m.

All equations are written in plain mathematical notation. The script outputs one line per transistor per frequency so you can see exactly how each device behaves.

Python code
```python
import math

# Physical constants and fixed parameters
E_field = 0.05           # V/m (RMS)
h_eff = 0.15             # effective height of 30 cm wire (m)
V_oc = E_field * h_eff   # open-circuit voltage RMS (V)
C_ant = 3e-12            # antenna capacitance (F)
V_DD = 9.0               # supply voltage (V)

# List of frequencies (Hz) from AM band to FM band
frequencies = [
    530e3,   # 530 kHz
    1e6,     # 1 MHz
    5e6,     # 5 MHz
    10e6,    # 10 MHz
    30e6,    # 30 MHz
    50e6,    # 50 MHz
    88e6,    # 88 MHz
    100e6,   # 100 MHz
    108e6    # 108 MHz
]

# JFET dictionary: key = name, value = (IDSS (A), V_P (V, negative), C_iss (F))
# Typical values are chosen from the datasheet ranges provided earlier.
jfets = {
    "J309":    (18e-3, -2.5, 5e-12),
    "J310":    (15e-3, -2.5, 2.5e-12),
    "U310":    (15e-3, -2.5, 2.5e-12),
    "2N5484":  (3e-3,  -1.5, 5e-12),
    "2N5485":  (7e-3,  -2.5, 5e-12),
    "2N5486":  (14e-3, -3.5, 5e-12),
    "BF245A":  (4e-3,  -1.2, 4e-12),
    "BF245B":  (10e-3, -2.5, 4e-12),
    "BF245C":  (18e-3, -3.5, 4e-12),
    "2N4416":  (10e-3, -2.5, 3.5e-12),
    "2N3819":  (10e-3, -3.0, 8e-12),
    "MPF102":  (10e-3, -2.5, 4.5e-12),
    "BF862":   (18e-3, -0.7, 10e-12),
    "J201":    (0.5e-3,-1.0, 5e-12),
    "J202":    (2e-3,  -2.0, 5e-12)
}

print("Amplifier calculations for common JFETs at various frequencies")
print("Assumptions: V_DD =", V_DD, "V, wire antenna 30 cm, E-field =", E_field, "V/m RMS")
print("V_oc =", round(V_oc*1000, 3), "mV RMS, C_ant =", C_ant*1e12, "pF")
print()

for name, (idss, vp, ciss) in jfets.items():
    # DC biasing: centre drain voltage
    R_D = V_DD / (2 * idss)          # ideal resistor to get V_D = V_DD/2
    # Standard resistor value (nearest preferred)
    if R_D < 100:
        R_D_std = 100
    elif R_D < 150:
        R_D_std = 150
    elif R_D < 220:
        R_D_std = 220
    elif R_D < 330:
        R_D_std = 330
    elif R_D < 470:
        R_D_std = 470
    else:
        R_D_std = round(R_D / 100) * 100  # rough rounding

    V_D = V_DD - idss * R_D_std

    # Transconductance at V_GS = 0
    g_m0 = 2 * idss / abs(vp)        # A/V (S)

    # Voltage gain (DC/low-frequency)
    A_v = g_m0 * R_D_std

    # Unity-current-gain frequency
    f_T = g_m0 / (2 * math.pi * ciss)

    # Gate voltage from capacitive divider (frequency-independent)
    V_gate = V_oc * C_ant / (C_ant + ciss)

    # Output header for this transistor
    print("---", name, "---")
    print("  IDSS =", idss*1000, "mA, V_P =", vp, "V, C_iss =", ciss*1e12, "pF")
    print("  R_D (std) =", R_D_std, "ohms, V_D (DC) =", round(V_D,2), "V")
    print("  g_m0 =", round(g_m0*1000,2), "mS, DC gain |Av| =", round(A_v,2))
    print("  f_T =", round(f_T/1e6,2), "MHz")
    print("  Gate voltage (RMS) =", round(V_gate*1000,3), "mV (constant)")
    print("  Frequency      Gain magnitude    V_drain (RMS)")
    for freq in frequencies:
        # Magnitude of voltage gain considering high-frequency roll-off
        # Simple model: |A_v(f)| = |A_v_DC| / sqrt(1 + (f/f_T)^2)
        A_v_f = A_v / math.sqrt(1 + (freq / f_T)**2)
        v_drain = A_v_f * V_gate
        print(f"    {freq/1e6:7.3f} MHz      {A_v_f:10.3f}            {v_drain*1000:7.3f} mV")
    print()
```

Common SPICE netlist (J310 amplifier)
This netlist can be used to simulate the frequency response of the J310 amplifier circuit. It uses a simple JFET model with typical parameters. Run an AC analysis from 0.5 MHz to 200 MHz.

```spice
J310 Common-Source Amplifier

V_ant in 0 AC 7.5mV
C_ant in gate 3p
R_G gate 0 1e6
R_D dd drain 330
V_DD dd 0 9
J1 drain gate 0 J310

.MODEL J310 NJF (VTO=-2.5 BETA=2.4m CGS=2p CGD=0.5p)

.AC DEC 50 0.5e6 200e6
.PROBE V(drain)
.END
```