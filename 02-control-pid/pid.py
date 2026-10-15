# =============================================================================
# Lección 2 — Lazo cerrado con P, PI, PD y PID
#   Planta: G(s) = 1 / (s^2 + s + 1)
#   Cabeceo reducido (corto periodo), el mismo segundo orden de la lección 1
#   en lazo abierto: wn = 1, zeta = 0.5. G(0) = 1, así que el proporcional
#   deja error ante un escalón y se ve qué aporta cada término.
# =============================================================================
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import control as ct

OUT = Path(__file__).resolve().parent
G = ct.tf([1], [1, 1, 1])          # θ(s)/δ(s)
KP, KI, KD, N = 3.0, 1.2, 2.0, 10.0
T = np.linspace(0, 40, 8000)       # horizonte largo para ts y ess

def controlador(kp, ki, kd, N=N):
    """PID con derivada filtrada: Kd * N s / (s+N). Sin impulso ante un escalón."""
    s = ct.tf("s")
    C = kp + 0 * s
    if ki:
        C = C + ki / s
    if kd:
        C = C + kd * (N * s) / (s + N)
    return ct.minreal(C, verbose=False)

def lazos(C):
    """Salida y mando ante realimentación negativa unitaria."""
    T_y = ct.minreal(ct.feedback(C * G, 1), verbose=False)
    T_u = ct.minreal(ct.feedback(C, G), verbose=False)
    return T_y, T_u

def par_dominante(sys):
    """ωn y ζ del par complejo (no el polo rápido del filtro ni el polo real)."""
    wn, zeta, poles = ct.damp(sys, doprint=False)
    wn, zeta, poles = map(np.atleast_1d, (wn, zeta, poles))
    i = next(k for k, p in enumerate(poles) if np.imag(p) > 1e-8)
    return float(wn[i]), float(zeta[i]), poles

CASOS = {
    "P":   controlador(KP, 0.0, 0.0),
    "PD":  controlador(KP, 0.0, KD),
    "PI":  controlador(KP, KI, 0.0),
    "PID": controlador(KP, KI, KD),
}
COLORES = {"P": "C0", "PD": "C1", "PI": "C2", "PID": "C3"}
MARCAS = {"P": "o", "PD": "s", "PI": "^", "PID": "X"}

print(f"{'ctrl':>4} | {'Mp %':>7} | {'tr':>6} | {'ts':>6} | {'ess':>8} | {'|u|max':>7} | {'zeta':>6} | {'wn':>6} | polos")
series = {}
for nombre, C in CASOS.items():
    Ty, Tu = lazos(C)
    info = ct.step_info(Ty, T=T)
    _, y = ct.step_response(Ty, T=T)
    tu, u = ct.step_response(Tu, T=T)
    ess = 1.0 - float(ct.dcgain(Ty))
    if abs(ess) < 1e-9:
        ess = 0.0
    wn, zeta, polos = par_dominante(Ty)
    series[nombre] = (tu, y, u, Ty)
    print(f"{nombre:>4} | {info['Overshoot']:7.2f} | {info['RiseTime']:6.3f} | "
          f"{info['SettlingTime']:6.3f} | {ess:8.4f} | {np.max(np.abs(u)):7.3f} | "
          f"{zeta:6.3f} | {wn:6.3f} | {np.round(polos, 3)}")

# --- 1) Escalón de y(t) ------------------------------------------------------
plt.figure(figsize=(8, 5))
for nombre, (tu, y, u, Ty) in series.items():
    plt.plot(tu, y, color=COLORES[nombre], label=nombre)
plt.axhline(1, color="k", lw=0.5, ls="--")
plt.xlim(0, 20)
plt.title("Escalón unitario, lazo cerrado")
plt.xlabel("t [s]"); plt.ylabel("y")
plt.legend(); plt.grid()
plt.savefig(OUT / "escalon_comparacion.png", dpi=120); plt.close()

# --- 2) Esfuerzo de mando u(t) ----------------------------------------------
plt.figure(figsize=(8, 5))
for nombre, (tu, y, u, Ty) in series.items():
    plt.plot(tu, u, color=COLORES[nombre], label=nombre)
plt.axhline(5, color="k", lw=0.7, ls="--", label="ejemplo |u|=5")
plt.axhline(-5, color="k", lw=0.7, ls="--")
plt.xlim(0, 12)
plt.title("Mando u(t) ante el mismo escalón")
plt.xlabel("t [s]"); plt.ylabel("u")
plt.legend(); plt.grid()
plt.savefig(OUT / "esfuerzo_control.png", dpi=120); plt.close()

# --- 3) Polos de lazo cerrado de los cuatro diseños -------------------------
plt.figure(figsize=(8, 5))
for nombre, (tu, y, u, Ty) in series.items():
    polos = ct.poles(Ty)
    plt.scatter(np.real(polos), np.imag(polos), s=70, color=COLORES[nombre],
                marker=MARCAS[nombre], linewidths=1.5, zorder=3, label=nombre)
plt.axhline(0, color="k", lw=0.4); plt.axvline(0, color="k", lw=0.4)
plt.title("Polos de lazo cerrado")
plt.xlabel("Re(s)"); plt.ylabel("Im(s)")
plt.legend(); plt.grid()
plt.savefig(OUT / "polos_lazo_cerrado.png", dpi=120); plt.close()

# --- 4) Lugar de las raíces al variar solo Kp --------------------------------
# Char. pol.: s^2 + s + (1+Kp). La parte real queda fija en -1/2.
plt.figure(figsize=(8, 5))
ganancias = [0, 1, 3, 8]
for K in ganancias:
    polos = np.roots([1, 1, 1 + K])
    plt.scatter(np.real(polos), np.imag(polos), s=36, zorder=3)
    for p in polos:
        if np.imag(p) >= -1e-9:
            plt.annotate(f"Kp={K:g}", (np.real(p), np.imag(p)),
                         textcoords="offset points", xytext=(6, 4), fontsize=9)
imaginarios = np.linspace(-3.2, 3.2, 200)
plt.plot(np.full_like(imaginarios, -0.5), imaginarios, color="0.6", lw=1, zorder=1)
plt.axhline(0, color="k", lw=0.4); plt.axvline(0, color="k", lw=0.4)
plt.title("Lugar de las raíces de G al variar Kp")
plt.xlabel("Re(s)"); plt.ylabel("Im(s)")
plt.grid()
plt.savefig(OUT / "lugar_raices_P.png", dpi=120); plt.close()
