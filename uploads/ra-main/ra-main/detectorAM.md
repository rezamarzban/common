
**Re-radiation Model — Metal Object Between Source and AM Radio**  
**Fully Derivation**

### Overview
This model describes the situation where a passive conducting metal object (rod, coin, plate, etc.) is located between a digital signal source and an AM radio. The source creates a reactive near-field that induces an oscillating electric dipole on the metal object. This dipole then re-radiates a magnetic field that is picked up by the radio’s ferrite rod antenna.

### Step-by-Step Derivation

**Step 1 — Source Harmonic Voltage**  
For a unipolar square wave (0 to V_CC, 50% duty cycle), the peak amplitude of the n-th odd harmonic is:  

V_n = (2 * V_CC) / (n * π)

**Step 2 — Incident Electric Field at the Metal Object**  
The source trace has stray capacitance C_s to ground and effective length h_eff. The oscillating charge creates a source dipole moment:  

p_s = C_s * V_n * h_eff  

The incident electric field at the metal object (broadside geometry) is:  

E_inc = (C_s * V_n * h_eff) / (4 * π * ε0 * d^3)

**Step 3 — Induced Electric Dipole Moment on the Metal Object**  
p = ε0 * α_e * E_inc  

Substituting E_inc and including orientation:  

p = (α_e * C_s * V_n * h_eff * cosφ) / (4 * π * d^3)  

(Note: ε0 cancels out completely.)

**Step 4 — Scattered Magnetic Field at the Radio**  
H_φ = (ω * p * sinθ) / (4 * π * r^2)  

Substituting p:  

H_φ = [ω * α_e * C_s * V_n * h_eff * cosφ * sinθ] / (16 * π² * r² * d³)

**Step 5 — Voltage Induced in the Ferrite Rod Antenna**  
V_rx = ω * μ0 * μ_eff * N_rx * A_rod * H_φ

### Final Combined Equation

After substituting ω = 2 * π * n * f0 and V_n = 2 * V_CC / (n * π), and simplifying the constants, the full equation is:

V_rx = [μ0 * μ_eff * N_rx * A_rod * α_e * C_s / (2 * π)] * n * f0² * V_CC * h_eff * cosφ * sinθ / (r² * d³)

### Simplified Scaling Form (Most Useful)

V_rx ∝ n * f0² * V_CC * h_eff * C_s * α_e * cosφ * sinθ / (r² * d³)

### Scaling Laws

| Parameter                        | Scaling of V_rx       | Notes                                      |
|----------------------------------|-----------------------|--------------------------------------------|
| Harmonic number n                | ∝ n (linear)         | One n from ω² is cancelled by 1/n in V_n  |
| Fundamental frequency f0         | ∝ f0²                 | Strong quadratic dependence                |
| Supply voltage V_CC              | ∝ V_CC                | Linear                                     |
| Source effective length h_eff    | ∝ h_eff               | Linear                                     |
| Stray capacitance C_s            | ∝ C_s                 | Important geometry factor                  |
| Object polarizability α_e        | ∝ α_e                 | Strongly depends on object size/shape      |
| Distance to object d             | ∝ 1/d³                | Extremely strong drop-off                  |
| Distance to radio r              | ∝ 1/r²                | Strong drop-off                            |
| Source-to-object angle φ         | ∝ cosφ                | Critical orientation factor                |
| Object-to-radio angle θ          | ∝ sinθ                | Critical orientation factor                |

This model provides accurate qualitative trends and realistic order-of-magnitude predictions for near-field passive re-radiation effects.
