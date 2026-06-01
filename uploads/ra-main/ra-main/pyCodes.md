```python
V_DD = 9.0
V_D_target = 4.5
I_D = 1e-3
R_D = (V_DD - V_D_target) / I_D
R_D_std = 4700.0
V_D = V_DD - I_D * R_D_std
V_GS = V_D
V_th = 2.1
V_ov = V_GS - V_th
g_m = 2 * I_D / V_ov
A_v = -g_m * R_D_std
E = 0.05
h_eff = 0.15
V_oc = E * h_eff
C_ant = 3e-12
C_iss = 50e-12
V_gate = V_oc * C_ant / (C_ant + C_iss)
v_drain = abs(A_v) * V_gate
f_T = g_m / (2 * 3.141592653589793 * C_iss)

print("2N7000 Amplifier")
print("V_DD =", V_DD, "V")
print("R_D (standard) =", R_D_std, "ohm")
print("V_D (DC) =", round(V_D, 2), "V")
print("V_GS =", round(V_GS, 2), "V")
print("V_ov =", round(V_ov, 2), "V")
print("g_m =", round(g_m*1000, 3), "mS")
print("A_v =", round(A_v, 2))
print("V_oc (RMS) =", round(V_oc*1000, 3), "mV")
print("C_ant =", C_ant, "F, C_iss =", C_iss, "F")
print("V_gate =", round(V_gate*1000, 4), "mV RMS")
print("v_drain (AC RMS) =", round(v_drain*1000, 3), "mV RMS")
print("f_T =", round(f_T/1e6, 2), "MHz")
```

```python
V_DD = 12.0
V_D_target = 6.0
I_D_est = 10e-3
R_D = (V_DD - V_D_target) / I_D_est
R_D_std = 560.0
V_D = V_DD - I_D_est * R_D_std
g_fs = 24e-3
A_v = -g_fs * R_D_std
E = 0.05
h_eff = 0.15
V_oc = E * h_eff
C_ant = 3e-12
C_iss = 2.1e-12
V_gate = V_oc * C_ant / (C_ant + C_iss)
v_drain = abs(A_v) * V_gate

print("BF998 Amplifier")
print("V_DD =", V_DD, "V")
print("R_D (standard) =", R_D_std, "ohm")
print("V_D (DC) =", round(V_D, 2), "V")
print("g_fs =", round(g_fs*1000, 1), "mS")
print("A_v =", round(A_v, 2))
print("V_oc (RMS) =", round(V_oc*1000, 2), "mV")
print("C_ant =", C_ant, "F, C_iss =", C_iss, "F")
print("V_gate =", round(V_gate*1000, 3), "mV RMS")
print("v_drain (AC RMS) =", round(v_drain*1000, 1), "mV RMS")
```

```python
V_DD = 9.0
IDSS = 15e-3
V_P = -2.5
R_D = V_DD / (2 * IDSS)
R_D_std = 330.0
V_D = V_DD - IDSS * R_D_std
g_m0 = 2 * IDSS / abs(V_P)
A_v = -g_m0 * R_D_std
E1 = 0.05
h_eff = 0.15
V_oc1 = E1 * h_eff
C_ant = 3e-12
C_iss = 2.5e-12
V_gate1 = V_oc1 * C_ant / (C_ant + C_iss)
v_drain1 = abs(A_v) * V_gate1

E2 = 1.0
V_oc2 = E2 * h_eff
V_gate2 = V_oc2 * C_ant / (C_ant + C_iss)
v_drain2 = abs(A_v) * V_gate2

print("J310 Amplifier")
print("V_DD =", V_DD, "V")
print("IDSS =", IDSS*1000, "mA, V_P =", V_P, "V")
print("R_D (standard) =", R_D_std, "ohm")
print("V_D (DC) =", round(V_D, 2), "V")
print("g_m0 =", round(g_m0*1000, 2), "mS")
print("A_v =", round(A_v, 2))
print("--- For 0.05 V/m ---")
print("V_oc (RMS) =", round(V_oc1*1000, 3), "mV")
print("V_gate =", round(V_gate1*1000, 3), "mV RMS")
print("v_drain (AC RMS) =", round(v_drain1*1000, 2), "mV RMS")
print("--- For 1.0 V/m ---")
print("V_oc (RMS) =", round(V_oc2*1000, 2), "mV")
print("V_gate =", round(V_gate2*1000, 3), "mV RMS")
print("v_drain (AC RMS) =", round(v_drain2*1000, 1), "mV RMS")
```

```python
import cmath

V_CC = 9.0
I_C = 1e-3
V_CE_target = 4.5
R_C = (V_CC - V_CE_target) / I_C
R_C_std = 4700.0
V_CE = V_CC - I_C * R_C_std
beta = 100.0
I_B = I_C / beta
V_BE = 0.7
V_RB = V_CE - V_BE
R_B = V_RB / I_B
R_B_std = 390e3

g_m = I_C / 0.026
r_pi = beta / g_m
A_v_lf = -g_m * R_C_std

E = 0.05
h_eff = 0.15
V_oc = E * h_eff

C_ant = 3e-12
f = 100e6
omega = 2 * 3.141592653589793 * f
Z_ant = 1 / (1j * omega * C_ant)

C_mu = 4e-12
C_pi_est = 8e-12
C_miller = C_mu * (1 + abs(A_v_lf))
C_in_total = C_pi_est + C_miller

Z_in = 1 / (1/r_pi + 1j * omega * C_in_total)

V_base_complex = V_oc * Z_in / (Z_ant + Z_in)
V_base_mag = abs(V_base_complex)

v_out_lf_est = abs(A_v_lf) * V_base_mag

print("2N3904 BJT Amplifier")
print("V_CC =", V_CC, "V")
print("R_C (standard) =", R_C_std, "ohm")
print("V_CE (DC) =", round(V_CE, 2), "V")
print("I_C =", I_C*1000, "mA, I_B =", round(I_B*1e6, 2), "uA")
print("R_B (standard) =", R_B_std, "ohm")
print("g_m =", round(g_m*1000, 2), "mS, r_pi =", round(r_pi), "ohm")
print("Low-frequency A_v =", round(A_v_lf, 2))
print("C_mu =", C_mu, "F, estimated C_pi =", C_pi_est, "F")
print("C_miller =", round(C_miller*1e12, 1), "pF")
print("Total C_in =", round(C_in_total*1e12, 1), "pF")
print("Antenna impedance Z_ant magnitude =", round(abs(Z_ant)), "ohm")
print("Input impedance Z_in magnitude =", round(abs(Z_in), 1), "ohm")
print("V_oc (RMS) =", round(V_oc*1000, 2), "mV")
print("V_base (RMS) =", round(V_base_mag*1000, 3), "mV")
print("v_out (RMS, using low-freq gain) =", round(v_out_lf_est*1000, 2), "mV")
print("(Note: Actual gain at 100 MHz is lower due to f_T = 300 MHz)")
```

```python
import math

# BJT with LC tank (loop antenna)
f = 100e6
E = 0.05
E_1V = 1.0
mu0 = 4e-7 * math.pi
c = 3e8
r = 0.05
a = 0.0005
N = 1
area = math.pi * r**2
L = mu0 * r * (math.log(8 * r / a) - 2)
C_tot = 1 / ((2 * math.pi * f)**2 * L)
X_L = 2 * math.pi * f * L
Q_u = 100
R_p = Q_u * X_L
H = E / 377.0
B = mu0 * H
V_oc = 2 * math.pi * f * N * area * B
V_CC = 9.0
I_C = 2.5e-3
V_T = 26e-3
beta = 100
V_BE = 0.7
R_E = 470
R_C = 2200
V_E = I_C * R_E
V_B = V_E + V_BE
R2 = 27000
I_div = V_B / R2
R1 = (V_CC - V_B) / I_div
r_pi = beta * V_T / I_C
R_bias_par = (R1 * R2) / (R1 + R2)
R_in = r_pi
R_p_loaded = 1 / (1/R_p + 1/R_in)
Q_loaded = R_p_loaded / X_L
A_v = -R_C / R_E
V_tank = V_oc * Q_loaded
v_out = abs(A_v) * V_tank
V_oc_1V = 2 * math.pi * f * N * area * mu0 * (E_1V / 377.0)
V_tank_1V = V_oc_1V * Q_loaded
v_out_1V = abs(A_v) * V_tank_1V

print("BJT with LC tank (loop antenna)")
print(f"Loop inductance L = {L*1e6:.3f} uH")
print(f"Required total capacitance C_tot = {C_tot*1e12:.2f} pF")
print(f"Inductive reactance X_L = {X_L:.2f} Ohm")
print(f"Unloaded R_p = {R_p:.2f} Ohm")
print(f"Base input resistance r_pi = {r_pi:.2f} Ohm")
print(f"Loaded Q = {Q_loaded:.2f}")
print(f"Voltage gain |Av| = {abs(A_v):.2f}")
print(f"Induced V_oc for 0.05 V/m = {V_oc*1e3:.3f} mV RMS")
print(f"Tank voltage V_tank = {V_tank*1e3:.2f} mV RMS")
print(f"Output voltage v_out = {v_out*1e3:.2f} mV RMS")
print(f"For 1 V/m: V_oc = {V_oc_1V*1e3:.2f} mV RMS, V_tank = {V_tank_1V*1e3:.2f} mV RMS, v_out = {v_out_1V*1e3:.2f} mV RMS")
print()
```

```python
import math

# MOSFET BF998 with loop antenna and resonant capacitor
f = 100e6
E = 0.05
E_1V = 1.0
mu0 = 4e-7 * math.pi
r = 0.05
a = 0.0005
N = 1
area = math.pi * r**2
L = mu0 * r * (math.log(8 * r / a) - 2)
C_tot = 1 / ((2 * math.pi * f)**2 * L)
X_L = 2 * math.pi * f * L
Q_u = 100
R_p = Q_u * X_L
C_iss = 2.1e-12
C_ext = C_tot - C_iss
V_DD = 12.0
R_D = 560
I_D = 10e-3
V_D = V_DD - I_D * R_D
g_fs = 24e-3
A_v = -g_fs * R_D
R_G = 100e3
R_p_loaded = 1 / (1/R_p + 1/R_G)
Q_loaded = R_p_loaded / X_L
H = E / 377.0
B = mu0 * H
V_oc = 2 * math.pi * f * N * area * B
V_tank = V_oc * Q_loaded
v_out = abs(A_v) * V_tank
V_oc_1V = 2 * math.pi * f * N * area * mu0 * (E_1V / 377.0)
V_tank_1V = V_oc_1V * Q_loaded
v_out_1V = abs(A_v) * V_tank_1V

print("MOSFET BF998 with loop antenna")
print(f"Loop inductance L = {L*1e6:.3f} uH")
print(f"Total capacitance C_tot = {C_tot*1e12:.2f} pF")
print(f"External capacitor C_ext = {C_ext*1e12:.2f} pF")
print(f"X_L = {X_L:.2f} Ohm, unloaded R_p = {R_p:.2f} Ohm")
print(f"Loaded Q = {Q_loaded:.2f}")
print(f"DC drain voltage V_D = {V_D:.2f} V")
print(f"Transconductance g_fs = {g_fs*1e3:.1f} mS")
print(f"Voltage gain |Av| = {abs(A_v):.2f}")
print(f"Induced V_oc = {V_oc*1e3:.3f} mV RMS")
print(f"Tank voltage V_tank = {V_tank*1e3:.2f} mV RMS")
print(f"Output v_out = {v_out*1e3:.2f} mV RMS")
print(f"For 1 V/m: V_oc = {V_oc_1V*1e3:.2f} mV, V_tank = {V_tank_1V*1e3:.2f} mV, v_out = {v_out_1V*1e3:.2f} mV RMS")
print()
```

```python
import math

# JFET J310 with loop antenna and resonant capacitor
f = 100e6
E = 0.05
E_1V = 1.0
mu0 = 4e-7 * math.pi
r = 0.05
a = 0.0005
N = 1
area = math.pi * r**2
L = mu0 * r * (math.log(8 * r / a) - 2)
C_tot = 1 / ((2 * math.pi * f)**2 * L)
X_L = 2 * math.pi * f * L
Q_u = 100
R_p = Q_u * X_L
C_iss = 2.5e-12
C_ext = C_tot - C_iss
V_DD = 9.0
I_DSS = 15e-3
V_P = -2.5
R_D = (V_DD / 2) / I_DSS
V_D = V_DD - I_DSS * R_D
g_m0 = 2 * I_DSS / abs(V_P)
A_v = -g_m0 * R_D
R_G = 1e6
R_p_loaded = 1 / (1/R_p + 1/R_G)
Q_loaded = R_p_loaded / X_L
H = E / 377.0
B = mu0 * H
V_oc = 2 * math.pi * f * N * area * B
V_tank = V_oc * Q_loaded
v_out = abs(A_v) * V_tank
V_oc_1V = 2 * math.pi * f * N * area * mu0 * (E_1V / 377.0)
V_tank_1V = V_oc_1V * Q_loaded
v_out_1V = abs(A_v) * V_tank_1V

print("JFET J310 with loop antenna")
print(f"Loop inductance L = {L*1e6:.3f} uH")
print(f"Total capacitance C_tot = {C_tot*1e12:.2f} pF")
print(f"External capacitor C_ext = {C_ext*1e12:.2f} pF")
print(f"X_L = {X_L:.2f} Ohm, unloaded R_p = {R_p:.2f} Ohm")
print(f"Loaded Q = {Q_loaded:.2f}")
print(f"Drain resistor R_D = {R_D:.2f} Ohm")
print(f"DC drain voltage V_D = {V_D:.2f} V")
print(f"Transconductance g_m0 = {g_m0*1e3:.1f} mS")
print(f"Voltage gain |Av| = {abs(A_v):.2f}")
print(f"Induced V_oc = {V_oc*1e3:.3f} mV RMS")
print(f"Tank voltage V_tank = {V_tank*1e3:.2f} mV RMS")
print(f"Output v_out = {v_out*1e3:.2f} mV RMS")
print(f"For 1 V/m: V_oc = {V_oc_1V*1e3:.2f} mV, V_tank = {V_tank_1V*1e3:.2f} mV, v_out = {v_out_1V*1e3:.2f} mV RMS")
print()
```