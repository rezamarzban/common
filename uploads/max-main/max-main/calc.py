import numpy as np

p0 = 101325.0
rho = 1.21
c = 343.0

freq_table = np.array([20, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000])
alpha_table = np.array([0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00017, 0.00040, 0.00115, 0.00167, 0.00253, 0.00345, 0.00483, 0.00678, 0.00921, 0.01576, 0.02230, 0.03109, 0.04605])

frequency = 4000.0
area = 1.0
distance = 100.0
time_duration = 1.0

alpha = np.interp(frequency, freq_table, alpha_table)

I_max = p0**2 / (2 * rho * c)

E_rec = I_max * area * time_duration * np.exp(-2 * alpha * distance)

if alpha == 0:
    U_col = (I_max * area * distance) / c
else:
    U_col = (I_max * area) / (2 * alpha * c) * (1 - np.exp(-2 * alpha * distance))

print(f"Attenuation coefficient α at {frequency:.0f} Hz = {alpha:.6f} Np/m")
print(f"Maximum possible intensity I_max = {I_max:.3e} W/m²")
print(f"Energy received at {distance:.1f} m in {time_duration:.1f} s = {E_rec:.3e} J")
print(f"Total acoustic energy stored in the first {distance:.1f} m of the column = {U_col:.3e} J")

for f, a in zip(freq_table, alpha_table):
    print(f"{f:6.0f}     {a:.6f}")