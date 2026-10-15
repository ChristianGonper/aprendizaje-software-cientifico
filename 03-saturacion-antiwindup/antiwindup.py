# =============================================================================
# Lección 3 — Saturación y anti-windup
#   Misma planta que la lección 2: G(s) = 1 / (s^2 + s + 1)
#   PID con Kp, Kd y N de la lección 2, para que el pico lineal siga siendo
#   Kp + Kd*N = 23. Ki sube a 3: con Ki=1.2 el tope solo recorta el pico de
#   la derivada un instante y el integrador no se embala.
#   python-control no satura un lazo LTI: el mando se recorta en el bucle.
# =============================================================================
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent

KP, KI, KD, N = 3.0, 3.0, 2.0, 10.0
U_MAX = 1.5
# Tt próximo a sqrt(Ti * Td), con Ti = Kp/Ki y Td = Kd/Kp.
TT = 0.8
DT = 0.001
T_FINAL = 40.0

COLORES = {
    "lineal": "C0",
    "sin_aw": "C3",
    "condicional": "C2",
    "backcalc": "C1",
}
NOMBRES = {
    "lineal": "Lineal",
    "sin_aw": "Sin anti-windup",
    "condicional": "Condicional",
    "backcalc": "Back-calculation",
}


def simular(modo, derivada="error", r=1.0, t_final=T_FINAL, dt=DT, u_max=U_MAX, Tt=TT):
    """RK4 a paso fijo. r constante o callable r(t)."""
    n = int(round(t_final / dt)) + 1
    t = np.linspace(0.0, t_final, n)
    y = np.zeros(n)
    yd = np.zeros(n)
    xi = np.zeros(n)
    xf = np.zeros(n)

    def ref(tk):
        return r(tk) if callable(r) else r

    def rhs(ss, tk):
        yy, ydd, xii, xff = ss
        e = ref(tk) - yy
        z = e if derivada == "error" else -yy
        D = KD * N * (z - xff)
        uraw = KP * e + xii + D
        if modo == "lineal":
            u = uraw
        else:
            u = float(np.clip(uraw, -u_max, u_max))
        if modo == "backcalc":
            dxi = KI * e + (u - uraw) / Tt
        elif modo == "condicional":
            exceso = uraw - u
            dxi = 0.0 if (abs(exceso) > 1e-12 and e * exceso > 0.0) else KI * e
        else:
            dxi = KI * e
        return np.array([ydd, -yy - ydd + u, dxi, N * (z - xff)])

    for k in range(n - 1):
        s = np.array([y[k], yd[k], xi[k], xf[k]])
        tk = t[k]
        k1 = rhs(s, tk)
        k2 = rhs(s + dt * k1 / 2, tk + dt / 2)
        k3 = rhs(s + dt * k2 / 2, tk + dt / 2)
        k4 = rhs(s + dt * k3, tk + dt)
        y[k + 1], yd[k + 1], xi[k + 1], xf[k + 1] = s + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6

    e = ref(t) - y
    z = e if derivada == "error" else -y
    D = KD * N * (z - xf)
    uraw = KP * e + xi + D
    if modo == "lineal":
        u = uraw.copy()
    else:
        u = np.clip(uraw, -u_max, u_max)
    return t, y, u, uraw, xi


def metricas(t, y, u, uraw, lineal, u_max=U_MAX):
    yss = float(np.mean(y[int(0.9 * len(y)):]))
    Mp = max(0.0, (float(y.max()) - yss) / abs(yss) * 100.0)
    banda = 0.02 * abs(yss)
    fuera = np.where(np.abs(y - yss) > banda)[0]
    if len(fuera) == 0:
        ts = 0.0
    elif fuera[-1] >= len(t) - 1:
        ts = np.inf
    else:
        ts = float(t[fuera[-1]])
    dt = float(t[1] - t[0])
    if lineal:
        tsat = 0.0
    else:
        tsat = float(np.sum(np.abs(uraw) > u_max + 1e-9) * dt)
    return Mp, ts, float(np.max(np.abs(u))), tsat, yss


def main():
    casos = {}
    orden = ["lineal", "sin_aw", "condicional", "backcalc"]
    print(f"Kp={KP} Ki={KI} Kd={KD} N={N} u_max={U_MAX} Tt={TT}")
    print(f"{'caso':22} {'Mp %':>8} {'ts':>8} {'|u|max':>8} {'t sat':>8} {'yss':>8} {'xi max':>8} {'xi min':>8}")
    for modo in orden:
        t, y, u, uraw, xi = simular(modo)
        Mp, ts, up, tsat, yss = metricas(t, y, u, uraw, modo == "lineal")
        casos[modo] = (t, y, u, uraw, xi)
        print(f"{NOMBRES[modo]:22} {Mp:8.2f} {ts:8.3f} {up:8.3f} {tsat:8.3f} {yss:8.4f} {xi.max():8.3f} {xi.min():8.3f}")

    # Rampa lineal: e(inf) = 1/Ki con G(0)=1.
    tr, yr, ur, urr, xir = simular("lineal", r=lambda tk: tk, t_final=60.0)
    e_rampa = tr[-1] - yr[-1]
    print(f"rampa lineal: e(t=60) = {e_rampa:.4f}   1/Ki = {1/KI:.4f}")

    # Derivada sobre la medida, sin saturar: el pico ya no es Kp+Kd*N.
    td, yd, ud, urd, xid = simular("lineal", derivada="medida", t_final=20.0)
    print(f"D sobre la medida, lineal: |u|max = {np.max(np.abs(ud)):.3f}  u(0) = {ud[0]:.3f}")
    print(f"D sobre el error, lineal:  |u|max = {np.max(np.abs(casos['lineal'][2])):.3f}  u(0) = {casos['lineal'][2][0]:.3f}")

    # --- y(t) ----------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    for modo in orden:
        t, y, u, uraw, xi = casos[modo]
        plt.plot(t, y, color=COLORES[modo], label=NOMBRES[modo])
    plt.axhline(1, color="k", lw=0.5, ls="--")
    plt.xlim(0, 20)
    plt.title("Escalón unitario con saturación del mando")
    plt.xlabel("t [s]")
    plt.ylabel("y")
    plt.legend()
    plt.grid()
    plt.savefig(OUT / "escalon_y.png", dpi=120)
    plt.close()

    # --- u(t): escala completa y detalle de los saturados --------------------
    fig, axes = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
    for modo in orden:
        t, y, u, uraw, xi = casos[modo]
        axes[0].plot(t, u, color=COLORES[modo], label=NOMBRES[modo])
        if modo != "lineal":
            axes[1].plot(t, u, color=COLORES[modo], label=NOMBRES[modo])
    for ax in axes:
        ax.axhline(U_MAX, color="k", lw=0.7, ls="--")
        ax.axhline(-U_MAX, color="k", lw=0.7, ls="--")
        ax.set_ylabel("u")
        ax.grid()
        ax.legend()
    axes[0].set_title("Mando. Arriba, el pico lineal. Abajo, el tope del actuador.")
    axes[1].set_xlabel("t [s]")
    axes[1].set_ylim(-2.2, 2.2)
    axes[0].set_xlim(0, 12)
    fig.tight_layout()
    fig.savefig(OUT / "esfuerzo_u.png", dpi=120)
    plt.close(fig)

    # --- integrador ----------------------------------------------------------
    plt.figure(figsize=(8, 5))
    for modo in orden:
        t, y, u, uraw, xi = casos[modo]
        plt.plot(t, xi, color=COLORES[modo], label=NOMBRES[modo])
    plt.axhline(1, color="k", lw=0.5, ls="--", label="régimen")
    plt.xlim(0, 20)
    plt.title("Estado del integrador")
    plt.xlabel("t [s]")
    plt.ylabel("x_i")
    plt.legend()
    plt.grid()
    plt.savefig(OUT / "integrador.png", dpi=120)
    plt.close()

    # --- derivada sobre el error frente a la medida, sin saturación ----------
    plt.figure(figsize=(8, 5))
    t_err, _, u_err, _, _ = casos["lineal"]
    plt.plot(t_err, u_err, color="C0", label="D sobre el error")
    plt.plot(td, ud, color="C1", label="D sobre la medida")
    plt.xlim(0, 8)
    plt.title("Sin saturación: el pico 23 es la derivada del escalón del error")
    plt.xlabel("t [s]")
    plt.ylabel("u")
    plt.legend()
    plt.grid()
    plt.savefig(OUT / "derivada_kick.png", dpi=120)
    plt.close()


if __name__ == "__main__":
    main()
