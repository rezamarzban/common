 
These equations **capture the qualitative trends correctly** — the received signal rises with the square of frequency, is proportional to the supply voltage, falls off roughly as the inverse cube of distance (combined near‑field and capacitive coupling), and depends on the object’s size and orientation.  

**However, the detailed derivation is physically inconsistent in two important places**, and the exact conversion from the metal’s induced voltage to the magnetic field at the radio is inaccurate.  

### Usable equations

**1. Square‑wave harmonic from the 555**  

The peak voltage of the `n`‑th odd harmonic is  

`V_n = (2 V_CC) / (n π)`  

(`V_CC` is the supply voltage, e.g. 9 V).  
The harmonic that falls in the AM band (`n f_0` between 530 kHz and 1710 kHz) is the one that matters.

**2. Incident electric field at the metal object**  

The 555’s output pin and connected traces act as a small, charged conductor. At a distance `d` that is much smaller than a wavelength, the dominant electric field component parallel to the trace can be crudely approximated by the field of a short dipole of effective length `h_eff` (roughly the trace length) carrying the harmonic voltage `V_n`:

`E_inc ≈ (V_n h_eff) / (2π d³)`   (for a short electric dipole near‑field, `E ∝ 1/r³`)

This is a rough estimate; in practice the field also depends on the board’s ground plane. The important point is `E_inc ∝ V_n` and falls off very rapidly with distance.

**3. Induced electric dipole moment of the metal**  

When the metal object is placed in this field, it becomes an electric dipole. For a conducting rod of length `L` and radius `a` (with `L ≫ a`) aligned with the field, the induced electric dipole moment `p` (peak phasor) is  

`p = ε₀ * α_e * E_inc`

where `ε₀` is the vacuum permittivity (8.854 × 10⁻¹² F/m) and `α_e` is the **electric polarizability** in m³.  
For a perfectly conducting prolate spheroid (a thin rod) with the field along the long axis:

`α_e = V / N`

- `V` = volume of the rod ≈ `π a² L`  
- `N` = depolarisation factor along the length. For a very slender rod, `N` ≈ `( (ln(2L/a) - 1) / (L/(2a))² )` – it is very small (∼ 10⁻³ for a 1 m rod, 1 cm thick).  

For a coin or disc, the polarizability is smaller and depends on orientation. For a rough estimate you can take `α_e` as several times the object’s volume for a rod, and roughly the volume itself for a sphere.

**4. Magnetic near‑field at the AM radio**  

The metal acts as an electric dipole radiating in the near‑field zone (because the distance `r` ≪ λ). The dominant magnetic component (azimuthal) at the radio’s location is:

`H_φ = (ω p sinθ) / (4π r²)`

where `θ` is the angle between the rod’s axis and the line to the radio. Maximum signal when the rod is broadside (`θ = 90°`).

**5. Voltage induced in the ferrite‑rod antenna**  

The AM radio’s ferrite rod (effective relative permeability `μ_eff`, cross‑sectional area `A_rod`, number of turns `N_rx`) converts this magnetic field to an open‑circuit peak voltage:

`V_rx = ω μ₀ μ_eff N_rx A_rod H_φ`

Combine with `H_φ`:

`V_rx = (ω² μ₀ μ_eff N_rx A_rod p sinθ) / (4π r²)`

Now insert `p` and `E_inc`:

`V_rx = (ω² μ₀ μ_eff N_rx A_rod ε₀ α_e E_inc sinθ) / (4π r²)`

And finally replace `E_inc` with its approximate form:

`V_rx ≈ (ω² μ₀ μ_eff N_rx A_rod ε₀ α_e sinθ) / (4π r²)   ×   (V_n h_eff) / (2π d³)`

This shows:

- **Frequency:** `V_rx ∝ ω²` (from the product `ω²` in the numerator).  
- **Supply voltage:** `V_rx ∝ V_n ∝ V_CC`.  
- **Distance:** The coupling path goes as `1/d³` (the incident field) and `1/r²` (the magnetic near‑field), so overall `1/(r² d³)`.  
- **Object size:** `α_e` is larger for longer/thicker metal objects → `V_rx ∝ α_e`.  
- **Orientation:** `sinθ` factor, plus the alignment of the rod with the incident electric field (maximum when parallel to the field).

---

### Practical note

These equations still contain unknown geometrical factors (`h_eff`, the exact form of `E_inc`, and the exact `α_e`). In practice you do not calculate an exact voltage; you use them to understand the **trends** and to guide the experiment (higher supply voltage, longer rod, correct harmonic, favorable orientation).  

The simplified capacitive‑divider model from the previous answer gave the same qualitative trends and can be used for a rough ballpark if you correct the magnetic field formula to `H_φ = (ω p sinθ)/(4π r²)` with `p = (C_self V_metal L_eff)`. The effective length `L_eff` for a short rod is about `L/2`. With that change the numbers become more realistic, though the precise amplitude will still be only accurate within a factor of 2–3.