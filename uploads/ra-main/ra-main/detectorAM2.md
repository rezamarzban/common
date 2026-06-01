**Derivation of the Re-radiation Model (Metal Object in Between)**

This model applies when there is a passive conducting object (metal rod, coin, plate, etc.) located between the signal source and the AM radio. The source creates a near-field, the metal object scatters/re-radiates, and the radio picks up the scattered field.

### Step-by-Step Derivation

**1. Source Harmonic Voltage (Square/PWM wave)**  
For a square wave of amplitude V_CC (peak-to-peak = 2*V_CC) and fundamental frequency f0, the peak amplitude of the n-th odd harmonic is:

V_n = (2 * V_CC) / (n * π)

**2. Incident Electric Field at the Metal Object**  
In the reactive near-field (distance d ≪ λ) the dominant term for the electric field from a short driven conductor (trace/wire of effective length h_eff) is:

E_inc ≈ (V_n * h_eff) / (2 * π * d^3)

**3. Induced Electric Dipole Moment on the Metal Object**  
The metal object develops an induced electric dipole moment:

p = ε0 * α_e * E_inc

where α_e is the electric polarizability (in m³), which depends strongly on the object’s shape, size, and orientation.

**4. Scattered (Re-radiated) Magnetic Field at the Radio**  
In the near-field zone, the magnetic field produced by the oscillating electric dipole at distance r from the object is (azimuthal component):

H_φ ≈ (ω * p * sinθ) / (4 * π * r^2)

where θ is the angle between the dipole axis and the line to the receiver (maximum when sinθ = 1).

**5. Voltage Induced in the Ferrite Rod Antenna**  
The ferrite rod converts the magnetic field into an open-circuit voltage:

V_rx = ω * μ0 * μ_eff * N_rx * A_rod * H_φ

### Final Combined Equation

V_rx ≈ [ω² * μ0 * μ_eff * N_rx * A_rod * ε0 * α_e * sinθ / (8 * π² * r² * d³)] * V_CC * h_eff

**Simplified Scaling Form (Most Useful)**

V_rx ∝ (n * f0)² * V_CC * h_eff * α_e * sinθ / (r² * d³)

### Key Scaling Laws (Re-radiation Model)

| Parameter                  | Scaling of V_rx             | Strength of Effect          |
|----------------------------|-----------------------------|-----------------------------|
| Frequency / Harmonic       | ∝ n² f0²                    | Very strong (higher better) |
| Supply Voltage             | ∝ V_CC                      | Linear                      |
| Source effective length    | ∝ h_eff                     | Linear                      |
| Object polarizability      | ∝ α_e                       | Depends on size/shape       |
| Distance to radio (r)      | ∝ 1/r²                      | Strong                      |
| Distance to object (d)     | ∝ 1/d³                      | Extremely strong            |
| Orientation                | ∝ sinθ                      | Critical                    |

### Practical Notes
- This model explains why a metal object can enhance or modulate the detected signal even if it is not directly connected.
- α_e is the biggest unknown — for a thin rod aligned with the field it can be much larger than the physical volume; for a coin it is smaller.
- The overall distance dependence 1/(d³ r²) is very sharp, which is typical for near-field passive re-radiation.
- All approximations assume deep near-field regime (d, r ≪ λ / 2π).
