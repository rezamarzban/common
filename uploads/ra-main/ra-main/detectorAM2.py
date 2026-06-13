"""
Re-radiation Model — Buried Iron Objects: Source and AM Radio on Surface
========================================================================

Corrected combined equation (V_rx open-circuit):

  V_rx = [ μ₀·μ_eff·N_rx·A_rod·α_e·C_s / (2π·εr) ]
         × n·f₀²·V_CC·h_eff·cosφ·sinθ / (r²·d³)

Geometry (vertical cross-section):

  Source ──────── x_obj ──────────────── Radio
    O    (surface, z=0)                    O
         ↘ d                         r ↙
           [Iron object at depth z_depth]

  d = √(x_obj²  + z_depth²)   source  → object
  r = √((D−x_obj)² + z_depth²) object → radio
  D = total horizontal surface separation

Steps verified:
  1. V_n  = 2·V_CC / (n·π)                              harmonic amplitude
  2. E_inc = C_s·V_n·h_eff / (4π·εr·ε₀·d³)             incident E-field (broadside)
  3. p    = α_e·C_s·V_n·h_eff·cosφ / (4π·εr·d³)        induced dipole  [ε₀ cancels]
  4. H_φ  = ω·p·sinθ / (4π·r²)                          scattered H-field
  5. V_rx = ω·μ₀·μ_eff·N_rx·A_rod·H_φ                  antenna voltage

Scaling law (corrected): V_rx ∝ n·f₀²  (NOT n²·f₀²)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import pandas as pd
from dataclasses import dataclass

# ═══════════════════════════════════════════════════════════════════
# 1.  PHYSICAL CONSTANTS
# ═══════════════════════════════════════════════════════════════════
EPS0   = 8.854187817e-12   # F/m   vacuum permittivity
MU0    = 4e-7 * np.pi      # H/m   vacuum permeability
CLIGHT = 2.998e8           # m/s

# ═══════════════════════════════════════════════════════════════════
# 2.  POLARIZABILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def alpha_rod(length_m, radius_m):
    """
    Thin conducting rod — polarizability along the long axis (maximum).
    Prolate-spheroid approximation, valid for L >> a.

        α_e = (4π/3) · L³ / [ln(2L/a) − 1]    [m³]

    L = half-length, a = wire radius.
    For flat coins / disks the disk formula is more appropriate.
    """
    L = length_m / 2.0
    a = radius_m
    if a >= L:                          # degenerate → sphere
        return (4 * np.pi / 3) * a**3
    denom = np.log(2.0 * L / a) - 1.0
    if denom <= 0:
        denom = 1e-3
    return (4 * np.pi / 3) * L**3 / denom


def alpha_sphere(radius_m):
    """
    Conducting sphere (exact).
        α_e = 4π · R³    [m³]
    """
    return 4.0 * np.pi * radius_m**3


def alpha_disk(radius_m):
    """
    Thin conducting disk — in-plane (parallel to disk face, maximum coupling).
        α_e = (16/3) · R³    [m³]
    Out-of-plane (perpendicular): (8/3)·R³  (half as large).
    """
    return (16.0 / 3.0) * radius_m**3


def alpha_rect_plate(a_m, b_m):
    """
    Thin rectangular conducting plate.
    Approximated as equivalent-area disk with in-plane polarizability.
        R_eff = √(a·b / π),   α_e = (16/3)·R_eff³
    """
    R_eff = np.sqrt(a_m * b_m / np.pi)
    return alpha_disk(R_eff)


# ═══════════════════════════════════════════════════════════════════
# 3.  IRON OBJECT CATALOGUE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class MetalObject:
    name    : str
    dims    : str          # human-readable dimensions
    alpha_e : float        # electric polarizability  [m³]
    color   : str
    marker  : str


OBJECTS = [
    MetalObject("Small Nail",    "L=80 mm, r=2 mm",
                alpha_rod(0.080, 0.002),        "#E63946", "o"),
    MetalObject("Iron Bolt",     "L=150 mm, r=5 mm",
                alpha_rod(0.150, 0.005),        "#F4A261", "s"),
    MetalObject("Iron Ball",     "R=30 mm",
                alpha_sphere(0.030),            "#8338EC", "p"),
    MetalObject("Rebar",         "L=600 mm, r=8 mm",
                alpha_rod(0.600, 0.008),        "#2A9D8F", "^"),
    MetalObject("Iron Pipe",     "L=400 mm, r=25 mm",
                alpha_rod(0.400, 0.025),        "#457B9D", "D"),
    MetalObject("Disk/Washer",   "R=40 mm, thin",
                alpha_disk(0.040),              "#FB5607", "h"),
    MetalObject("Iron Plate",    "150×100 mm, thin",
                alpha_rect_plate(0.150, 0.100), "#3A86FF", "*"),
]


# ═══════════════════════════════════════════════════════════════════
# 4.  SYSTEM PARAMETERS
# ═══════════════════════════════════════════════════════════════════

# ── Source (PWM / digital trace) ───────────────────────────────────
F0    = 100e3   # Hz   fundamental PWM frequency (100 kHz)
V_CC  = 12.0   # V    supply voltage  (unipolar 0 → V_CC)
H_EFF = 0.20   # m    effective trace/wire length
C_S   = 50e-12 # F    stray capacitance of trace to ground  (50 pF)

# ── AM radio ferrite rod antenna ───────────────────────────────────
MU_EFF = 200    # effective relative permeability of ferrite core
N_RX   = 300    # number of turns on rod
A_ROD  = 1.0e-4 # m²  cross-sectional area  (≈ 11.3 mm diameter)

# ── Geometry ───────────────────────────────────────────────────────
D_SPAN = 2.0    # m   horizontal surface separation: source ↔ radio
X_OBJ  = D_SPAN / 2.0  # object horizontally below midpoint (symmetric)

# ── Orientation (worst-case = maximum coupling) ────────────────────
COS_PHI   = 1.0  # source→object: field parallel to object axis  (φ = 0°)
SIN_THETA = 1.0  # object→radio:  broadside observation          (θ = 90°)

# ── Soil ───────────────────────────────────────────────────────────
EPS_R = 8.0     # relative permittivity  (damp earth: typical 4–20)
# Note: εr appears only in the E_inc term (Step 2); the H-field
# propagation uses μr ≈ 1 for non-magnetic soil, so no correction there.

# ── Detection threshold ────────────────────────────────────────────
V_THRESH = 1e-6  # V  (1 µV — typical AM receiver sensitivity floor)

# ── Harmonic sweep ─────────────────────────────────────────────────
HARMONICS = np.array([1, 3, 5, 7, 9, 11, 13, 15])  # odd harmonics
N_SHOW    = 9     # harmonic used in depth / position sweeps
#                   → 9 × 100 kHz = 900 kHz  (mid-AM band)


# ═══════════════════════════════════════════════════════════════════
# 5.  CORE EQUATIONS
# ═══════════════════════════════════════════════════════════════════

def calc_vrx(n, f0, V_CC, h_eff, C_s, alpha_e,
             d, r, mu_eff, N_rx, A_rod,
             cos_phi=1.0, sin_theta=1.0, eps_r=1.0):
    """
    Corrected combined formula — direct substitution.

        V_rx = [μ₀·μ_eff·N_rx·A_rod·α_e·C_s / (2π·εr)]
               · n·f₀²·V_CC·h_eff·cosφ·sinθ / (r²·d³)

    Returns V_rx  [V]  (open-circuit antenna voltage).
    All distances in metres, frequency in Hz.
    """
    bracket = (MU0 * mu_eff * N_rx * A_rod * alpha_e * C_s) / (2.0 * np.pi * eps_r)
    scaling = (n * f0**2 * V_CC * h_eff * cos_phi * sin_theta) / (r**2 * d**3)
    return bracket * scaling


def step_by_step(n, f0, V_CC, h_eff, C_s, alpha_e,
                 d, r, mu_eff, N_rx, A_rod,
                 cos_phi=1.0, sin_theta=1.0, eps_r=1.0):
    """
    Return all intermediate quantities (Steps 1-5) for inspection.
    Demonstrates ε₀ cancellation between Steps 2 and 3.
    """
    omega  = 2.0 * np.pi * n * f0
    V_n    = 2.0 * V_CC / (n * np.pi)
    # Step 2: E_inc includes ε₀ in denominator
    E_inc  = (C_s * V_n * h_eff) / (4.0 * np.pi * eps_r * EPS0 * d**3)
    # Step 3: p = ε₀·α_e·E_inc → ε₀ cancels
    p      = (alpha_e * C_s * V_n * h_eff * cos_phi) / (4.0 * np.pi * eps_r * d**3)
    H_phi  = (omega * p * sin_theta) / (4.0 * np.pi * r**2)
    V_rx   = omega * MU0 * mu_eff * N_rx * A_rod * H_phi
    return {
        "ω [rad/s]"   : omega,
        "V_n [V]"     : V_n,
        "E_inc [V/m]" : E_inc,
        "p [C·m]"     : p,
        "H_φ [A/m]"   : H_phi,
        "V_rx [V]"    : V_rx,
    }


def geometry(x_obj, depth, D=D_SPAN, x_src=0.0):
    """Distances d (source→object) and r (object→radio) for buried object."""
    d = np.sqrt((x_obj - x_src)**2 + depth**2)
    r = np.sqrt((D - x_obj)**2    + depth**2)
    return float(d), float(r)


def nearfield_limit(n, f0):
    """λ/(2π) for the n-th harmonic — near-field valid when d,r ≪ this."""
    return CLIGHT / (2.0 * np.pi * n * f0)


# ═══════════════════════════════════════════════════════════════════
# 6.  COMPUTE SWEEP DATA
# ═══════════════════════════════════════════════════════════════════

depths     = np.linspace(0.05, 1.50, 300)   # m
x_positions = np.linspace(0.10, D_SPAN - 0.10, 300)  # m

# ── A: V_rx vs burial depth  (object below midpoint, n = N_SHOW) ──
vrx_vs_depth = {}
for obj in OBJECTS:
    vals = []
    for z in depths:
        d, r = geometry(X_OBJ, z)
        vals.append(calc_vrx(N_SHOW, F0, V_CC, H_EFF, C_S, obj.alpha_e,
                              d, r, MU_EFF, N_RX, A_ROD,
                              COS_PHI, SIN_THETA, EPS_R))
    vrx_vs_depth[obj.name] = np.array(vals)

# ── B: V_rx vs harmonic  (fixed depth 0.3 m, object at midpoint) ──
Z_HARM = 0.30   # m
d_h, r_h = geometry(X_OBJ, Z_HARM)
vrx_vs_harm = {}
for obj in OBJECTS:
    vrx_vs_harm[obj.name] = np.array([
        calc_vrx(int(n), F0, V_CC, H_EFF, C_S, obj.alpha_e,
                 d_h, r_h, MU_EFF, N_RX, A_ROD,
                 COS_PHI, SIN_THETA, EPS_R)
        for n in HARMONICS
    ])

# ── C: V_rx vs object horizontal position  (fixed depth 0.3 m) ───
Z_POS = 0.30   # m
vrx_vs_pos = {}
for obj in OBJECTS:
    vals = []
    for x in x_positions:
        d, r = geometry(x, Z_POS)
        vals.append(calc_vrx(N_SHOW, F0, V_CC, H_EFF, C_S, obj.alpha_e,
                              d, r, MU_EFF, N_RX, A_ROD,
                              COS_PHI, SIN_THETA, EPS_R))
    vrx_vs_pos[obj.name] = np.array(vals)

# ── D: Step-by-step table at reference geometry ───────────────────
Z_REF = 0.30   # m
d_ref, r_ref = geometry(X_OBJ, Z_REF)

rows = []
for obj in OBJECTS:
    sb = step_by_step(N_SHOW, F0, V_CC, H_EFF, C_S, obj.alpha_e,
                      d_ref, r_ref, MU_EFF, N_RX, A_ROD,
                      COS_PHI, SIN_THETA, EPS_R)
    rows.append({
        "Object"      : obj.name,
        "Dimensions"  : obj.dims,
        "α_e [m³]"    : f"{obj.alpha_e:.3e}",
        "E_inc [V/m]" : f"{sb['E_inc [V/m]']:.3e}",
        "p [C·m]"     : f"{sb['p [C·m]']:.3e}",
        "H_φ [A/m]"   : f"{sb['H_φ [A/m]']:.3e}",
        "V_rx [nV]"   : f"{sb['V_rx [V]']*1e9:.4g}",
    })
df_table = pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════
# 7.  PLOT
# ═══════════════════════════════════════════════════════════════════

plt.rcParams.update({
    "figure.facecolor" : "#0d1117",
    "axes.facecolor"   : "#161b22",
    "axes.edgecolor"   : "#30363d",
    "axes.labelcolor"  : "#cdd9e5",
    "axes.titlecolor"  : "#e6edf3",
    "xtick.color"      : "#8b949e",
    "ytick.color"      : "#8b949e",
    "grid.color"       : "#21262d",
    "text.color"       : "#cdd9e5",
    "legend.facecolor" : "#161b22",
    "legend.edgecolor" : "#30363d",
    "font.family"      : "monospace",
    "font.size"        : 8.5,
    "axes.titlesize"   : 9.5,
    "axes.labelsize"   : 8.5,
})

fig = plt.figure(figsize=(17, 14))
gs  = gridspec.GridSpec(
    3, 2, figure=fig,
    hspace=0.46, wspace=0.30,
    left=0.07, right=0.97, top=0.92, bottom=0.05
)

ax_depth  = fig.add_subplot(gs[0, :])   # row 0 full-width
ax_harm   = fig.add_subplot(gs[1, 0])   # row 1 left
ax_pos    = fig.add_subplot(gs[1, 1])   # row 1 right
ax_alpha  = fig.add_subplot(gs[2, 0])   # row 2 left
ax_geo    = fig.add_subplot(gs[2, 1])   # row 2 right (geometry)

THRESH_NV = V_THRESH * 1e9   # threshold in nV


# ─── Panel 1: V_rx vs burial depth ───────────────────────────────
for obj in OBJECTS:
    ax_depth.semilogy(depths * 100,
                      np.abs(vrx_vs_depth[obj.name]) * 1e9,
                      color=obj.color, marker=obj.marker, markevery=40,
                      linewidth=1.8, markersize=5,
                      label=f"{obj.name}  ({obj.dims})")

ax_depth.axhline(THRESH_NV, color="#ffd700", lw=1.3, ls="--",
                 label="AM sensitivity  1 µV")
ax_depth.set_xlabel("Burial Depth  [cm]")
ax_depth.set_ylabel("V_rx  [nV]")
ax_depth.set_title(
    f"Received Voltage vs Burial Depth  "
    f"[n={N_SHOW},  {N_SHOW}×{F0/1e3:.0f} kHz = {N_SHOW*F0/1e3:.0f} kHz,  "
    f"surface span D={D_SPAN} m,  soil εr={EPS_R}]"
)
ax_depth.set_xlim(depths[0]*100, depths[-1]*100)
ax_depth.grid(True, alpha=0.35)
ax_depth.legend(ncol=2, fontsize=7.8, loc="upper right",
                framealpha=0.85)

# Near-field limit annotation
nfl = nearfield_limit(N_SHOW, F0)
ax_depth.text(0.02, 0.04,
              f"Near-field valid: d, r << lambda/2pi = {nfl:.0f} m  (satisfied)",
              transform=ax_depth.transAxes, fontsize=7.5,
              color="#8b949e", style="italic")


# ─── Panel 2: V_rx vs harmonic number ────────────────────────────
freqs_kHz = HARMONICS * F0 / 1e3

for obj in OBJECTS:
    ax_harm.semilogy(freqs_kHz,
                     np.abs(vrx_vs_harm[obj.name]) * 1e9,
                     color=obj.color, marker=obj.marker,
                     linewidth=1.6, markersize=6,
                     label=obj.name)

ax_harm.axhline(THRESH_NV, color="#ffd700", lw=1.3, ls="--",
                label="1 µV threshold")
ax_harm.set_xlabel("Frequency  n × f₀  [kHz]")
ax_harm.set_ylabel("V_rx  [nV]")
ax_harm.set_title(
    f"V_rx vs Harmonic  "
    f"[depth={Z_HARM*100:.0f} cm,  d=r={d_h:.2f} m]"
)
ax_harm.grid(True, alpha=0.35)
ax_harm.legend(fontsize=7.2, loc="upper left", framealpha=0.85)

# Annotate ∝ n slope
x0, x1 = freqs_kHz[0], freqs_kHz[-1]
# Reference slope line through rebar (largest rod)
ref = vrx_vs_harm["Rebar"]
slope_line = ref[0] * (freqs_kHz / freqs_kHz[0])
ax_harm.plot(freqs_kHz, slope_line * 1e9, ":", color="#ffffff",
             lw=0.9, alpha=0.5)
ax_harm.text(freqs_kHz[-3], slope_line[-3] * 1e9 * 1.6,
             "slope ∝ n", color="#ffffff", fontsize=7.5, alpha=0.6)


# ─── Panel 3: V_rx vs object horizontal position ─────────────────
for obj in OBJECTS:
    ax_pos.semilogy(x_positions,
                    np.abs(vrx_vs_pos[obj.name]) * 1e9,
                    color=obj.color, marker=obj.marker, markevery=50,
                    linewidth=1.6, markersize=5,
                    label=obj.name)

ax_pos.axhline(THRESH_NV, color="#ffd700", lw=1.3, ls="--",
               label="1 µV threshold")
ax_pos.axvline(D_SPAN / 2, color="#8b949e", lw=0.9, ls=":",
               alpha=0.7, label="Midpoint")
ax_pos.set_xlabel("Object Horizontal Position  [m from source]")
ax_pos.set_ylabel("V_rx  [nV]")
ax_pos.set_title(
    f"V_rx vs Object Position  "
    f"[n={N_SHOW},  depth={Z_POS*100:.0f} cm]"
)
ax_pos.set_xlim(x_positions[0], x_positions[-1])
ax_pos.grid(True, alpha=0.35)
ax_pos.legend(fontsize=7.2, loc="upper center", framealpha=0.85)

# Mark optimum position (min r²·d³)
def rd_factor(x, z, D=D_SPAN):
    d_ = np.sqrt(x**2 + z**2)
    r_ = np.sqrt((D-x)**2 + z**2)
    return r_**2 * d_**3

rd_vals = np.array([rd_factor(x, Z_POS) for x in x_positions])
x_opt   = x_positions[np.argmin(rd_vals)]
ax_pos.axvline(x_opt, color="#ff9f43", lw=0.9, ls="--", alpha=0.8)
ax_pos.text(x_opt + 0.05, ax_pos.get_ylim()[0] * 1.5,
            f"opt≈{x_opt:.2f}m", color="#ff9f43",
            fontsize=7, va="bottom")


# ─── Panel 4: Polarizability comparison ──────────────────────────
names_short = [obj.name for obj in OBJECTS]
alphas_     = [obj.alpha_e for obj in OBJECTS]
colors_     = [obj.color for obj in OBJECTS]
x_ticks     = np.arange(len(OBJECTS))

bars = ax_alpha.bar(x_ticks, alphas_, color=colors_,
                    edgecolor="#30363d", linewidth=0.7, width=0.65,
                    bottom=1e-5)
ax_alpha.set_yscale("log")
ax_alpha.set_ylim(3e-5, 1.5e-1)          # fixed headroom for labels/annotation
ax_alpha.set_xticks(x_ticks)
ax_alpha.set_xticklabels(names_short, rotation=32, ha="right", fontsize=7.5)
ax_alpha.set_ylabel("α_e  [m³]")
ax_alpha.set_title("Electric Polarizability α_e by Object")
ax_alpha.grid(True, axis="y", alpha=0.35)

for bar, a in zip(bars, alphas_):
    ax_alpha.text(bar.get_x() + bar.get_width()/2,
                  a * 1.35,
                  f"{a:.2e}",
                  ha="center", va="bottom", fontsize=6.6,
                  color="#e6edf3")

# Polarizability formula reference — upper-left, clear of all bars/labels
ax_alpha.text(0.03, 0.96,
              "Rod:    (4π/3)·L³ / [ln(2L/a)−1]\n"
              "Sphere: 4π·R³\n"
              "Disk:   (16/3)·R³   [in-plane]",
              transform=ax_alpha.transAxes,
              fontsize=6.8, color="#8b949e",
              ha="left", va="top", style="italic",
              linespacing=1.6,
              bbox=dict(boxstyle="round,pad=0.35",
                       facecolor="#0d1117", edgecolor="#30363d",
                       alpha=0.85))


# ─── Panel 5: Geometry schematic ─────────────────────────────────
ax_geo.set_facecolor("#060d1a")
ax_geo.set_xlim(-0.25, D_SPAN + 0.25)
ax_geo.set_ylim(-1.70, 0.55)
ax_geo.set_aspect("equal")
ax_geo.set_xlabel("Horizontal position  [m]")
ax_geo.set_ylabel("Depth  [m]")
ax_geo.set_title("Geometry Cross-section")
ax_geo.set_yticks([-1.5, -1.0, -0.5, 0.0])
ax_geo.set_yticklabels(["1.5 m", "1.0 m", "0.5 m", "0 m"])

# Ground fill
ax_geo.axhline(0, color="#6b4423", lw=2.5)
ax_geo.fill_between([-0.25, D_SPAN + 0.25], -1.70, 0,
                    color="#2d1a0e", alpha=0.85)
ax_geo.text(0.5, -1.58, "SOIL  (εr = 8)",
            ha="center", color="#6b4423", fontsize=7.5, style="italic")

# Source symbol
ax_geo.plot(0, 0.28, "s", color="#ffd700", ms=12, zorder=6)
ax_geo.text(0, 0.43, "Source\n(PWM/trace)", color="#ffd700",
            ha="center", fontsize=7.2)
ax_geo.annotate("", xy=(0, 0.01), xytext=(0, 0.22),
                arrowprops=dict(arrowstyle="-|>", color="#ffd700", lw=1.2))

# Radio symbol
ax_geo.plot(D_SPAN, 0.28, "^", color="#58a6ff", ms=12, zorder=6)
ax_geo.text(D_SPAN, 0.43, "AM Radio\n(ferrite rod)", color="#58a6ff",
            ha="center", fontsize=7.2)
ax_geo.annotate("", xy=(D_SPAN, 0.01), xytext=(D_SPAN, 0.22),
                arrowprops=dict(arrowstyle="-|>", color="#58a6ff", lw=1.2))

# Surface label
ax_geo.text(D_SPAN/2, 0.07, "Ground surface  (z = 0)",
            ha="center", color="#8b6914", fontsize=7, style="italic")

# Buried objects at 3 reference depths
ref_depths  = [0.30, 0.60, 1.00]
ref_colors  = ["#e67e22", "#e74c3c", "#9b59b6"]
ref_labels  = ["30 cm", "60 cm", "100 cm"]

for z_r, c_r, lbl in zip(ref_depths, ref_colors, ref_labels):
    ax_geo.plot(X_OBJ, -z_r, "o", color=c_r, ms=9, zorder=5)
    ax_geo.text(X_OBJ + 0.10, -z_r, lbl, color=c_r,
                va="center", fontsize=7.5)
    # d arrow (source → object)
    ax_geo.annotate("", xy=(X_OBJ, -z_r), xytext=(0.01, -0.01),
                    arrowprops=dict(arrowstyle="-|>",
                                   color=c_r, lw=0.9,
                                   linestyle="dashed"))
    # r arrow (object → radio)
    ax_geo.annotate("", xy=(D_SPAN - 0.01, -0.01), xytext=(X_OBJ, -z_r),
                    arrowprops=dict(arrowstyle="-|>",
                                   color=c_r, lw=0.9,
                                   linestyle="dashed"))

ax_geo.text(0.30, -0.16, "d", color="#ffd700", fontsize=13,
            style="italic", fontweight="bold")
ax_geo.text(1.50, -0.16, "r", color="#58a6ff", fontsize=13,
            style="italic", fontweight="bold")
ax_geo.grid(True, alpha=0.2)


# ─── Figure super-title ──────────────────────────────────────────
fig.suptitle(
    "Re-radiation Model  |  Buried Iron Objects  |  "
    f"Source: f₀={F0/1e3:.0f} kHz, V_CC={V_CC:.0f} V, "
    f"h_eff={H_EFF*100:.0f} cm, C_s={C_S*1e12:.0f} pF  |  "
    f"Soil: εr={EPS_R}",
    fontsize=10.5, color="#e6edf3", y=0.975,
    fontfamily="monospace"
)

plt.savefig("/mnt/user-data/outputs/reradiation_buried_iron.png",
            dpi=150, bbox_inches="tight", facecolor="#0d1117")
print("Figure saved.")


# ═══════════════════════════════════════════════════════════════════
# 8.  PRINT SUMMARY TABLE
# ═══════════════════════════════════════════════════════════════════

print("\n" + "═"*96)
print(" RE-RADIATION MODEL — STEP-BY-STEP RESULTS AT REFERENCE GEOMETRY")
print(f"   n={N_SHOW},  f₀={F0/1e3:.0f} kHz  →  {N_SHOW*F0/1e3:.0f} kHz  (mid-AM band)")
print(f"   Depth={Z_REF*100:.0f} cm,  x_obj={X_OBJ:.1f} m,  D={D_SPAN:.1f} m  →  d={d_ref:.3f} m,  r={r_ref:.3f} m")
print(f"   εr={EPS_R},  cosφ={COS_PHI},  sinθ={SIN_THETA}")
print(f"   Source: V_CC={V_CC} V, h_eff={H_EFF} m, C_s={C_S*1e12:.0f} pF")
print(f"   Antenna: μ_eff={MU_EFF}, N={N_RX}, A={A_ROD*1e4:.0f} cm²")
print("═"*96)
print(df_table.to_string(index=False))
print("═"*96)

# ─── Validity check ──────────────────────────────────────────────
nfl = nearfield_limit(N_SHOW, F0)
print(f"\n  Near-field limit  λ/(2π)  =  {nfl:.1f} m   >>   max(d,r) = {max(d_ref,r_ref):.2f} m  ✓")
print(f"  AM detection threshold        =  {V_THRESH*1e6:.0f} µV  =  {V_THRESH*1e9:.0f} nV")

# ─── Scaling check (verify ∝ n, not n²) ─────────────────────────
print("\n  Harmonic scaling check (Rebar, fixed geometry):")
v1 = calc_vrx(1,  F0, V_CC, H_EFF, C_S, OBJECTS[3].alpha_e,
              d_ref, r_ref, MU_EFF, N_RX, A_ROD,
              COS_PHI, SIN_THETA, EPS_R)
v3 = calc_vrx(3,  F0, V_CC, H_EFF, C_S, OBJECTS[3].alpha_e,
              d_ref, r_ref, MU_EFF, N_RX, A_ROD,
              COS_PHI, SIN_THETA, EPS_R)
v9 = calc_vrx(9,  F0, V_CC, H_EFF, C_S, OBJECTS[3].alpha_e,
              d_ref, r_ref, MU_EFF, N_RX, A_ROD,
              COS_PHI, SIN_THETA, EPS_R)
print(f"    V_rx(n=1) = {v1*1e9:.4f} nV")
print(f"    V_rx(n=3) = {v3*1e9:.4f} nV   ratio = {v3/v1:.2f}  (expected 3.00 for ∝n)")
print(f"    V_rx(n=9) = {v9*1e9:.4f} nV   ratio = {v9/v1:.2f}  (expected 9.00 for ∝n)")

# ─── What C_s gives 1 µV for best object (Rebar) at z=0.3m ──────
bracket = (MU0 * MU_EFF * N_RX * A_ROD * OBJECTS[3].alpha_e) / (2.0*np.pi*EPS_R)
scaling = (N_SHOW * F0**2 * V_CC * H_EFF * COS_PHI * SIN_THETA) / (d_ref**2 * r_ref**3)
cs_for_1uv = V_THRESH / (bracket * scaling)
print(f"\n  C_s needed for Rebar to reach 1 µV at this geometry: {cs_for_1uv*1e9:.1f} nF")
print(f"  (Current C_s = {C_S*1e12:.0f} pF  →  {cs_for_1uv/C_S:.0f}× below threshold)")

print()
plt.show()
