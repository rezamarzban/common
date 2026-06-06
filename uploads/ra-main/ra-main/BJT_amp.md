Here is the plain‑text explanation of all equations used in the Python script, followed by a common SPICE netlist that works for any of the 20 BJTs.

---

**Plain‑text equations explanation**

Antenna and signal source  
- Effective height of the 70 cm wire: h_eff = L_wire / 2 = 0.35 m.  
- Open‑circuit RMS voltage: V_oc = E_field * h_eff. For 1 V/m, V_oc = 1 * 0.35 = 0.35 V = 350 mV RMS.  
- Antenna capacitance C_ant = 5 pF. Its impedance at frequency f is Z_ant = 1 / (j * omega * C_ant), where omega = 2 * pi * f.  
  Magnitude of Z_ant = 1 / (omega * C_ant).

DC biasing (collector‑base feedback)  
- Supply V_CC = 9 V. Collector current I_C = 1 mA.  
- Desired V_CE ≈ V_CC / 2 = 4.5 V for maximum output swing.  
- Collector resistor: R_C = (V_CC - V_CE_target) / I_C = (9 - 4.5) / 0.001 = 4500 Ω → nearest E24 value 4.7 kΩ.  
- Actual V_CE = V_CC - I_C * R_C_std.  
- Base current I_B = I_C / h_FE, where h_FE is the transistor's typical DC current gain.  
- Base bias resistor: R_B = (V_CE_target - V_BE) / I_B. V_BE ≈ 0.7 V.  
  The calculated R_B is rounded to the nearest E24 standard value.

Transistor small‑signal model  
- Transconductance: g_m = I_C / V_T, with V_T ≈ 26 mV at room temperature. So g_m ≈ 0.0385 S.  
- Low‑frequency voltage gain magnitude: |A_v| = g_m * R_C_std. With R_C = 4.7 kΩ, |A_v| ≈ 0.0385 * 4700 ≈ 181.  
- Transition frequency f_T gives the current‑gain‑bandwidth product. At a frequency f, the effective AC current gain is beta_ac = f_T / f (valid when f is well above the transistor's beta cutoff).  
- Base‑emitter small‑signal resistance: r_pi = beta_ac / g_m.  

Capacitances and Miller effect  
- Collector‑base capacitance C_mu is taken from the datasheet (often called C_obo or C_JC).  
- The base‑emitter capacitance C_pi is derived from f_T: f_T = g_m / [2*pi*(C_pi + C_mu)], so C_pi = g_m/(2*pi*f_T) - C_mu. If the result is negative, C_pi is set to zero (the model becomes approximate).  
- Miller multiplication: the effective input capacitance due to C_mu is C_miller = C_mu * (1 + |A_v|).  
- Total input capacitance: C_in = C_pi + C_miller.  

Input impedance and voltage division  
- The transistor's input impedance Z_in is the parallel combination of r_pi and the reactance of C_in: Z_in = 1 / (1/r_pi + j*omega*C_in).  
  Its magnitude |Z_in| = 1 / sqrt( (1/r_pi)^2 + (omega*C_in)^2 ).  
- The antenna and Z_in form a voltage divider: V_base = V_oc * Z_in / (Z_ant + Z_in).  
  The magnitude of the complex quantity gives the RMS voltage at the base.  

Output voltage  
- The output voltage (RMS) at the collector is approximately v_out = |A_v| * |V_base|.  
  This uses the low‑frequency gain, which slightly over‑estimates the output at very high frequencies where collector load capacitance comes into play, but it remains a useful comparison.

---

**Common SPICE netlist for the amplifier**

The following netlist can be used for any of the NPN BJTs listed. Just replace the .MODEL line with the appropriate transistor model parameters. The AC analysis is run at a single frequency (100 MHz here, but can be changed). The antenna is modelled as a voltage source with a series 5 pF capacitor, representing the 70 cm wire in a 1 V/m field (350 mV RMS).

```spice
Common Emitter Feedback Amplifier - 70cm Wire Antenna, 1V/m

* Antenna equivalent
V_ant in 0 AC 0.35
C_ant in base 5p

* Biasing network
R_C cc collector 4.7k
R_B collector base {Rb_val}
V_CC cc 0 9

* Transistor (example: 2N3904)
Q1 collector base 0 2N3904
.MODEL 2N3904 NPN (IS=6.734e-15 BF=150 NF=1 VAF=74 IKF=0.1 ISE=6.734e-15 NE=2
+ BR=0.1 NR=1 VAR=4 IKR=0.025 ISC=6.734e-15 NC=2 RE=0 RC=1 RB=10
+ CJE=8p CJC=4p TF=0.5n TR=10n)

* AC analysis at a single frequency (100 MHz)
.AC DEC 1 100MEG 100MEG
.PRINT AC V(collector) VP(collector)
.END
```

To use a different transistor, change the .MODEL name and parameters accordingly. For example, for a 2N2222A use:

```spice
.MODEL 2N2222A NPN (IS=14.34f BF=150 NF=1 VAF=50 IKF=0.1 ISE=14.34f NE=2
+ BR=0.1 NR=1 VAR=20 IKR=0.025 ISC=14.34f NC=2 RE=0 RC=1 RB=10
+ CJE=25p CJC=8p TF=0.5n TR=10n)
```

The resistor R_B must be set to the calculated value for that transistor's DC gain. You can either replace `{Rb_val}` with a fixed number (e.g., 560k for 2N2222A) or keep it as a parameter and define it with `.PARAM Rb_val = 560k`. The SPICE simulation will give the actual AC voltage at the collector, which accounts for high‑frequency roll‑off and any other parasitics in the model.