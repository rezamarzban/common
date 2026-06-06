# Effective Vapor Boundary Layer Thickness Calculation

This document outlines the core physics and equations used to model the diffusion-driven vapor boundary layer above a boiling liquid surface with a constant heat input.

## Core Equations & Derivation

The model is based on the **Film Theory** of mass transfer, utilizing a **heat and mass transfer analogy (Lewis analogy)**. It calculates an **effective** diffusion layer thickness, representing the stagnant region where the vapor concentration drops from saturation at the surface to zero in the free stream.

### 1. Film Temperature (`T_f`)
The average temperature used to evaluate temperature-dependent fluid properties (like diffusivity).
```
T_f = (T_s + T_∞) / 2
```
*   `T_s`: Surface (boiling point) temperature of the liquid **(K)**.
*   `T_∞`: Ambient free air temperature **(K)**.

### 2. Temperature-Corrected Mass Diffusivity (`D`)
Mass diffusivity is strongly temperature-dependent. This equation scales a known reference value to the film temperature.
```
D = D_ref * (T_f / T_ref)^n
```
*   `D_ref`: Reference mass diffusivity of the vapor in air at `T_ref` **(m²/s)**.
*   `T_ref`: Reference temperature (typically 298 K) **(K)**.
*   `n`: Empirical temperature exponent (typically between 1.5 and 1.8 for vapor-air systems).

### 3. Saturation Vapor Concentration (`C_s`)
The density of vapor in equilibrium with the boiling liquid surface, calculated using the ideal gas law.
```
C_s = (P * M) / (R * T_s)
```
*   `P`: Ambient atmospheric pressure **(Pa)**.
*   `M`: Molecular weight of the evaporating fluid **(kg/mol)**.
*   `R`: Universal gas constant = 8.314 **(J/(mol·K))**.
*   `T_s`: Boiling point temperature of the liquid **(K)**.

### 4. Effective Mass Boundary Layer Thickness (`δ`)
The final equation derived from the film model (`δ = D / k_m`), where the mass transfer coefficient (`k_m`) is expressed in terms of the evaporative mass flux driven by the heat source.
```
δ = (D * C_s * A * h_fg) / Q
```
*   `D`: Temperature-corrected mass diffusivity **(m²/s)**.
*   `C_s`: Saturation vapor concentration at the surface **(kg/m³)**.
*   `A`: Surface area of the evaporating liquid **(m²)**.
*   `h_fg`: Latent heat of vaporization of the liquid **(J/kg)**.
*   `Q`: Constant heat input power **(W)**.

## Key Assumptions & Model Context

1.  **Steady-State Boiling**: The liquid surface is maintained at its boiling point (`T_s`).
2.  **All Heat for Evaporation**: The entire heat input `Q` is used for phase change (neglects convective/radiative losses from the hot surface). *This is a simplifying assumption; a more complete model partitions `Q` between evaporation and convection.*
3.  **Ideal Gas**: Vapor behaves as an ideal gas.
4.  **Semi-Infinite Still Air**: Ambient vapor concentration is zero (`C_∞ = 0`), and there is no forced convection.
5.  **Lewis Analogy**: Applies the mathematical similarity between heat and mass transfer, allowing the use of a simple film model.

## Calculation Flow
The code implements these equations in the following vectorized sequence for multiple liquids:
1.  Calculate `T_f` for each liquid.
2.  Correct the diffusivity `D` for temperature.
3.  Compute the saturation concentration `C_s`.
4.  Solve for the effective boundary layer thickness `δ`.
