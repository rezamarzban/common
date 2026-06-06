import numpy as np

Q,A,P,R,Tinf,n,Tref = 100,0.1,101325,8.314,298,1.75,298

# name, M(kg/mol), h_fg(J/kg), Ts(K), Dref(m2/s)
L = np.array([
    ("Gasoline",0.114,3.0e5,373,7.38e-6),
    ("Diesel",0.200,2.5e5,550,6.0e-6),
    ("Kerosene",0.170,2.7e5,520,6.5e-6),
    ("Ethanol",0.04607,9.19e5,351.4,1.19e-5),
    ("Methanol",0.03204,1.165e6,337.9,1.75e-5),
    ("Isopropanol",0.0601,7.68e5,355.4,1.02e-5),
    ("Toluene",0.09214,4.13e5,383.6,1.69e-5),
    ("Benzene",0.07811,3.94e5,353.3,1.60e-5),
    ("Hexane",0.08618,3.65e5,341.9,1.51e-5),
    ("Heptane",0.1002,3.18e5,371.6,1.30e-5),
    ("Pentane",0.07215,3.67e5,309.3,1.88e-5),
    ("Acetone",0.05808,5.18e5,329.3,1.30e-5),
    ("MEK",0.07211,5.00e5,352.7,1.15e-5),
    ("Jet Fuel",0.160,2.6e5,540,6.2e-6),
    ("Crude Oil",0.220,2.3e5,600,5.5e-6),
    ("Engine Oil SAE30",0.400,2.0e5,650,4.0e-6),
    ("Engine Oil SAE40",0.450,1.9e5,680,3.8e-6),
    ("Motor Oil 5W-30",0.420,2.0e5,660,3.9e-6),
    ("Hydraulic Oil",0.390,2.1e5,640,4.2e-6)
],dtype=object)

M,h,T,D = L[:,1:].astype(float).T
Tf=(T+Tinf)/2
D=D*(Tf/Tref)**n
Cs=P*M/(R*T)
delta=D*Cs*A*h/Q

for name,delta_name in zip(L[:,0],delta):
    print(f"{name:18} {delta_name*1000:7.2f} mm")
