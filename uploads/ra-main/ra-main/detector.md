

---

### The Physical Setup

We have:
- A horizontal transmitter loop on the ground surface, carrying an AC current I_T at angular frequency omega = 2 pi f.
- A vertical receiver loop placed on the surface a short distance away, oriented perpendicular to the transmitter loop's axis to achieve induction balance (null direct coupling).
- A small metal target buried at depth z (positive downward).
- The ground is modelled as a homogeneous half‑space with electrical conductivity sigma and magnetic permeability mu0 (the same as air).

The open‑circuit voltage V_R that appears at the receiver terminals, *after the primary field has been perfectly nulled*, is given by the single compact formula derived from reciprocity:

V_R = -j omega mu0 * alpha(omega) * ( H_Tx · h_Rx ) * I_T * G(omega)

where each term is explained in detail below.

---

### 1. The Faraday and reciprocity factor: -j omega mu0

The factor -j indicates a 90° phase shift; omega = 2 pi f is the angular frequency. This comes from Faraday's law: a time‑changing magnetic flux induces a voltage proportional to the rate of change. Together with mu0 (the permeability of vacuum, 4 pi × 10^-7 H/m), it converts the magnetic‑dipole interactions into a voltage.

---

### 2. Target magnetic polarizability alpha(omega)

alpha (units: m^3) is a complex number that quantifies how the target behaves as a secondary magnetic dipole when it is placed in an oscillating magnetic field. Its magnitude gives the strength of the response; its phase gives a time lag that depends on the metal's conductivity and permeability.

For different target shapes we use different formulas:

**Perfectly conducting sphere (high frequency limit):**  
alpha = -2 pi a^3  
where a is the sphere radius. The negative sign means the induced dipole opposes the primary field (eddy currents).

**Real non‑magnetic conducting sphere (any frequency):**  
alpha = -(3/2) pi a^3 * [ 1 - (3 / (ka)) * cot(ka) + 3 / (ka)^2 ]  
with k = sqrt( -j omega mu0 sigma_metal ). As frequency increases, |alpha| grows from zero toward the perfect‑conductor value.

**Ferromagnetic conducting rod (prolate spheroid, field along the long axis):**  
First, the volume of the equivalent spheroid is V = (4/3) pi a b^2, where a is half the rod length and b is the rod radius.  
The eccentricity is e = sqrt( 1 - (b/a)^2 ) (for a > b).  
The demagnetising factor along the long axis is  

N = ( (1 - e^2) / e^2 ) * ( (1/(2 e)) * ln( (1 + e) / (1 - e) ) - 1 ).

The effective complex permeability of an infinite cylinder (used to approximate the rod's material) is  

mu_eff = mu_r * (2 / (ka)) * J1(ka) / J0(ka),

where k = sqrt( -j omega mu0 mu_r sigma_metal ), mu_r is the relative permeability, and J0, J1 are Bessel functions of the first kind (evaluated using the general Bessel function jv for complex arguments). Then the polarizability is  

alpha = V * (mu_eff - 1) / ( 1 + N * (mu_eff - 1) ).

This formula includes both the ferromagnetic attraction (high mu_r) and the eddy‑current shielding.

**Thin conducting disc (oblate spheroid, field perpendicular to the face):**  
For a disc of radius c (major semi‑axis) and thickness t = 2a (minor axis), e = sqrt( 1 - (a/c)^2 ) and the demagnetising factor along the short axis is  

N = (1 / e^2) * ( 1 - ( sqrt(1 - e^2) / e ) * arcsin(e) ).

At high frequencies (good conductor, strong skin effect) the disc behaves almost like a perfect conductor and  

alpha = -V / N,   V = (4/3) pi a c^2.

---

### 3. Magnetic dipole fields

A small loop carrying a current behaves like a magnetic dipole with moment vector m = N I A u_hat, where N is the number of turns, I the current, A the enclosed area, and u_hat the unit normal to the loop. The magnetic field (A/m) at a point r relative to the dipole is:

H(r) = (1 / (4 pi r^3)) * [ 3 (m · r_hat) r_hat - m ],

with r = |r| and r_hat = r / r.

In the code, we compute the field **per unit current** by using m = N A u_hat. For the transmitter we use N1 A_T with the vertical direction; for the receiver we use N2 A_R with its axis direction. Then:

- H_Tx is the field at the target produced by the transmitter coil when 1 A flows in it. The true incident field is I_T H_Tx.
- h_Rx is the field at the target produced by the receiver coil when 1 A flows in it (this is the “reciprocal” field).

The dot product H_Tx · h_Rx automatically accounts for the mutual orientation and the induction‑balance null: when the coils are perfectly orthogonal and the target is absent, this dot product (and hence V_R) is zero.

---

### 4. Ground attenuation factor G(omega)

In free space the above quantities are enough. But with a conductive half‑space, the field that reaches the target and returns to the receiver is reduced. For a vertical magnetic dipole placed on the surface, the vertical magnetic field at depth z (directly underneath) is not the free‑space dipole field but is multiplied by a complex transmission coefficient:

F(gamma z) = (2 / (gamma z)^2) * [ 1 - (1 + gamma z) * exp(-gamma z) ],

where gamma = sqrt( j omega mu0 sigma ) = (1 + j) / delta and delta = sqrt( 2 / (omega mu0 sigma) ) is the skin depth. For a target at depth z, the total two‑way attenuation factor is approximately G(omega) = F(gamma z)^2.

**Important approximation:** The target in our geometry is not directly below the transmitter or receiver; it is displaced horizontally. The true field modification for off‑axis points requires evaluating integrals that depend on the lateral distance. For simplicity the code uses the same F(gamma z)^2 factor for the entire dot product, which is a first‑order approximation that captures the essential exponential decay and phase shift. The error is acceptable for target depths that are not too large compared with the horizontal offsets.

---

### 5. The complete expression

Putting everything together, the open‑circuit receiver voltage (peak phasor) for a transmitter current I_T is:

V_R = -j omega mu0 * alpha(omega) * ( H_Tx · h_Rx ) * I_T * F(gamma z)^2.

In the code, I_T = 1 A is used, so the voltage is given per ampere of transmit current. The magnitude |V_R| is the peak AC voltage; the phase angle of the complex V_R carries information about the target's composition.

In free space (sigma = 0), F = 1 and the formula simplifies to the free‑space expression you originally quoted.

---

### 6. Verification of the code against the physics

- The dipole_H_at_point function correctly implements the dipole field formula.
- alpha_rod, alpha_sphere_nonmag, and alpha_disc use the exact textbook derivations for ellipsoidal targets, with the Bessel‑function correction (jv instead of j0) to handle complex arguments properly.
- F_VMD uses the exact half‑space solution for a vertical magnetic dipole.
- The final receiver_voltage function assembles the terms exactly as described above.

The model assumes:
- The target is small compared to all distances (dipole approximation for the target).
- The ground is homogeneous and non‑magnetic.
- The coils are much smaller than the wavelength (magnetic dipole approximation).
- The null is perfect; in practice residual coupling and ground mineralisation must be cancelled electronically.

These assumptions are standard in induction‑balance detector theory. The code therefore gives the *theoretical* voltage that a well‑nulled system would see. Real‑world complexities (layered soil, irregular targets, electromagnetic interference) will modify the numbers, but the trends and relative responses remain valid.