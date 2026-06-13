```spice
2N7000 Amplifier

V_ant in 0 AC 7.5mV
C_ant in gate 3p
R_G drain gate 1e6
R_D dd drain 4.7k
V_DD dd 0 9
M1 drain gate 0 0 2N7000
.MODEL 2N7000 NMOS (LEVEL=1 VTO=2.1 KP=0.347e-3 CGSO=40p CGDO=10p CGBO=0)
.AC DEC 1 100MEG 100MEG
.PRINT AC V(drain) VP(drain)
.END
```

```spice
BF998 Amplifier (simplified single-gate depletion)

V_ant in 0 AC 7.5mV
C_ant in gate1 3p
R_G1 gate1 0 100k
R_G2 gate2 drain 100k
R_D dd drain 560
V_DD dd 0 12
M1 drain gate2 gate1 0 BF998
.MODEL BF998 NMOS (LEVEL=1 VTO=-0.5 KP=0.08 CGSO=1.6p CGDO=0.5p CGBO=0)
.AC DEC 1 100MEG 100MEG
.PRINT AC V(drain) VP(drain)
.END
```

```spice
J310 Amplifier

V_ant in 0 AC 7.5mV
C_ant in gate 3p
R_G gate 0 1e6
R_D dd drain 330
V_DD dd 0 9
J1 drain gate 0 J310
.MODEL J310 NJF (VTO=-2.5 BETA=2.4m CGS=2p CGD=0.5p)
.AC DEC 1 100MEG 100MEG
.PRINT AC V(drain) VP(drain)
.END
```

```spice
2N3904 BJT Amplifier

V_ant in 0 AC 7.5mV
C_ant in base 3p
R_C cc collector 4.7k
R_B collector base 390k
V_CC cc 0 9
Q1 collector base 0 2N3904
.MODEL 2N3904 NPN (IS=6.734e-15 BF=100 NF=1 VAF=74 IKF=0.1 ISE=6.734e-15 NE=2 BR=0.1 NR=1 VAR=4 IKR=0.025 ISC=6.734e-15 NC=2 RE=0 RC=1 RB=10 CJE=8p CJC=4p TF=0.5n TR=10n)
.AC DEC 1 100MEG 100MEG
.PRINT AC V(collector) VP(collector)
.END
```