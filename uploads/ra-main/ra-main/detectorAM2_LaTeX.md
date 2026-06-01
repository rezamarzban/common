**Derivation of the Re-radiation Model (Metal Object in Between)**

This model applies when there is a **passive conducting object** (metal rod, coin, plate, etc.) located between the signal source and the AM radio. The source creates a near-field, the metal object scatters/re-radiates, and the radio picks up the scattered field.

### Step-by-Step Derivation

**1. Source Harmonic Voltage (Square/PWM wave)**  
For a square wave of amplitude \(V_{CC}\) (peak-to-peak = 2\(V_{CC}\)) and fundamental frequency \(f_0\), the peak amplitude of the \(n\)-th odd harmonic is:

\[
V_n = \frac{2 V_{CC}}{n \pi}
\]

**2. Incident Electric Field at the Metal Object**  
In the reactive near-field (distance \(d \ll \lambda\)) the dominant term for the electric field from a short driven conductor (trace/wire of effective length \(h_{eff}\)) is:

\[
E_{\text{inc}} \approx \frac{V_n \cdot h_{eff}}{2\pi \, d^3}
\]

**3. Induced Electric Dipole Moment on the Metal Object**  
The metal object develops an induced electric dipole moment:

\[
p = \varepsilon_0 \, \alpha_e \, E_{\text{inc}}
\]

where \(\alpha_e\) is the **electric polarizability** (in m³), which depends strongly on the object’s shape, size, and orientation.

**4. Scattered (Re-radiated) Magnetic Field at the Radio**  
In the near-field zone, the magnetic field produced by the oscillating electric dipole at distance \(r\) from the object is (azimuthal component):

\[
H_\phi \approx \frac{\omega \, p \, \sin\theta}{4\pi \, r^2}
\]

where \(\theta\) is the angle between the dipole axis and the line to the receiver (maximum when \(\sin\theta = 1\)).

**5. Voltage Induced in the Ferrite Rod Antenna**  
The ferrite rod converts the magnetic field into an open-circuit voltage:

\[
V_{rx} = \omega \, \mu_0 \, \mu_{eff} \, N_{rx} \, A_{rod} \, H_\phi
\]

### Final Combined Equation

Substitute steps 1–4 into step 5:

\[
V_{rx} \approx \frac{\omega^{2} \,\mu_{0} \,\mu_{eff} \,N_{rx} \,A_{rod} \,\varepsilon_{0} \,\alpha_{e} \,\sin\theta}{8\,\pi^{2} \,r^{2} \,d^{3}} \cdot V_{CC} \cdot h_{eff}
\]

**Simplified Scaling Form (Most Useful)**

\[
V_{rx} \propto \frac{(n f_0)^2 \cdot V_{CC} \cdot h_{eff} \cdot \alpha_e \cdot \sin\theta}{r^{2} \, d^{3}}
\]

### Key Scaling Laws (Re-radiation Model)

| Parameter              | Scaling of \(V_{rx}\)       | Strength of Effect          |
|------------------------|-----------------------------|-----------------------------|
| Frequency / Harmonic   | \(\propto n^2 f_0^2\)       | Very strong (higher better) |
| Supply Voltage         | \(\propto V_{CC}\)          | Linear                      |
| Source effective length| \(\propto h_{eff}\)         | Linear                      |
| Object polarizability  | \(\propto \alpha_e\)        | Depends on size/shape       |
| Distance to radio (\(r\)) | \(\propto 1/r^2\)        | Strong                      |
| Distance to object (\(d\)) | \(\propto 1/d^3\)        | Extremely strong            |
| Orientation            | \(\propto \sin\theta\)      | Critical                    |

### Practical Notes
- This model explains **why a metal object can enhance or modulate** the detected signal even if it is not directly connected.
- \(\alpha_e\) is the biggest unknown — for a thin rod aligned with the field it can be much larger than the physical volume; for a coin it is smaller.
- The overall distance dependence \(1/(d^3 r^2)\) is very sharp, which is typical for near-field passive re-radiation.
- All approximations assume deep near-field regime (\(d, r \ll \lambda / 2\pi\)).
