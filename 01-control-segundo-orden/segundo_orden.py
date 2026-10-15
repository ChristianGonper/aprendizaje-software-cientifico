# =============================================================================
# Lección 1 — Sistema de segundo orden
#   G(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
# Objetivo: ver cómo zeta (amortiguamiento) y wn (frecuencia natural) cambian
# la respuesta, comparar métricas numéricas con fórmulas analíticas y comprobar
# que función de transferencia y espacio de estados dan lo mismo.
# =============================================================================
import numpy as np
import matplotlib
matplotlib.use("Agg")                 # sin ventana: solo guardamos PNG
import matplotlib.pyplot as plt
import control as ct                  # python-control: FT, step, bode...
from scipy.integrate import solve_ivp # integrador de EDOs genérico

WN = 2.0                              # wn fija [rad/s] para el barrido de zeta
ZETAS = [0.1, 0.3, 0.5, 0.7, 1.0, 2.0]
t = np.linspace(0, 20, 4000)          # eje de tiempo común [s]

def G(zeta, wn):
    """Función de transferencia de 2º orden: numerador y denominador en s."""
    return ct.tf([wn**2], [1, 2*zeta*wn, wn**2])

# --- 1) Respuesta al escalón variando zeta (wn fija) ------------------------
plt.figure(figsize=(8, 5))
for z in ZETAS:
    tt, y = ct.step_response(G(z, WN), T=t)   # entrada u(t)=1 para t>=0
    plt.plot(tt, y, label=f"ζ={z}")
plt.axhline(1, color="k", lw=0.5, ls="--")
plt.title(f"Escalón, ωn={WN} rad/s, ζ variable"); plt.xlabel("t [s]"); plt.ylabel("y")
plt.legend(); plt.grid(); plt.savefig("escalon_zeta.png", dpi=120); plt.close()

# --- 2) Respuesta al escalón variando wn (zeta fija) ------------------------
plt.figure(figsize=(8, 5))
for wn in [0.5, 1, 2, 4]:
    tt, y = ct.step_response(G(0.3, wn), T=t)
    plt.plot(tt, y, label=f"ωn={wn}")
plt.title("Escalón, ζ=0.3, ωn variable (misma forma, escala de tiempo distinta)")
plt.xlabel("t [s]"); plt.ylabel("y"); plt.legend(); plt.grid()
plt.savefig("escalon_wn.png", dpi=120); plt.close()

# --- 3) Métricas numéricas vs fórmulas analíticas ---------------------------
# step_info: sobreoscilación [%], tiempo de subida (10-90 %), tiempo de
# establecimiento (banda del 2 %). Analítico: Mp=exp(-ζπ/√(1-ζ²)), ts≈4/(ζωn).
print(f"{'zeta':>5} | {'Mp num %':>8} {'Mp teo %':>8} | {'tr num':>6} | {'ts num':>6} {'ts≈4/ζωn':>8} | polos")
for z in ZETAS:
    info = ct.step_info(G(z, WN), T=t)
    mp_teo = 100*np.exp(-z*np.pi/np.sqrt(1-z**2)) if z < 1 else 0.0
    ts_teo = 4/(z*WN)
    polos = np.roots([1, 2*z*WN, WN**2])
    print(f"{z:5.1f} | {info['Overshoot']:8.2f} {mp_teo:8.2f} | {info['RiseTime']:6.3f} | "
          f"{info['SettlingTime']:6.3f} {ts_teo:8.3f} | {np.round(polos, 3)}")

# --- 4) Bode para algunos zeta ----------------------------------------------
plt.figure(figsize=(8, 6))
ct.bode_plot([G(z, WN) for z in [0.1, 0.3, 0.7, 2.0]], omega=np.logspace(-1, 2, 500),
             dB=True, label=[f"ζ={z}" for z in [0.1, 0.3, 0.7, 2.0]], title=f"Bode, ωn={WN} rad/s, ζ variable")
plt.savefig("bode_zeta.png", dpi=120); plt.close("all")

# --- 5) Mismo sistema en espacio de estados con solve_ivp -------------------
# Estados x1=y, x2=dy/dt.  y'' + 2ζωn y' + ωn² y = ωn² u
#   x1' = x2
#   x2' = -ωn² x1 - 2ζωn x2 + ωn² u
z = 0.3
def f(tk, x, u=1.0):
    return [x[1], -WN**2*x[0] - 2*z*WN*x[1] + WN**2*u]
sol = solve_ivp(f, (t[0], t[-1]), [0, 0], t_eval=t, rtol=1e-9, atol=1e-12)
_, y_tf = ct.step_response(G(z, WN), T=t)
print(f"\nζ={z}: error máx |FT - solve_ivp| = {np.max(np.abs(y_tf - sol.y[0])):.2e}")
plt.figure(figsize=(8, 5))
plt.plot(t, y_tf, lw=4, alpha=0.5, label="FT (python-control)")
plt.plot(sol.t, sol.y[0], "k--", label="Espacio de estados (solve_ivp)")
plt.title(f"Comparación, ζ={z}, ωn={WN}"); plt.xlabel("t [s]"); plt.legend(); plt.grid()
plt.savefig("comparacion_ss_tf.png", dpi=120); plt.close()
