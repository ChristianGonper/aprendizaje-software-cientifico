# =============================================================================
# Demostración — Ala en flecha con AeroSandbox (VLM) y PyVista
#   Planta trapezoidal, perfil NACA 2412, envergadura y superficie fijas.
#   El VLM es no viscoso: CD es resistencia inducida.
#   La optimización (Opti / CasADi) elige estrechamiento y torsión de punta
#   para minimizar CD con CL fijo.
# =============================================================================
from pathlib import Path

import casadi as ca

try:
    ca.GlobalOptions.setNumpyMode(-1)
except Exception:
    pass

import aerosandbox as asb
import aerosandbox.numpy as anp
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv

OUT = Path(__file__).resolve().parent

# Geometría fija. El estrechamiento y la torsión de punta son los grados de libertad.
ENVERGADURA = 10.0  # m
SUPERFICIE = 10.0  # m^2
FLECHA_GRADOS = 25.0
VELOCIDAD = 50.0  # m/s
PERFIL = "naca2412"
ESTRECHAMIENTO_INICIAL = 0.45
TORSION_INICIAL = 0.0
CL_DISENO = 0.5
N_SPAN_FINO = 16
N_CUERDA_FINO = 8
N_SPAN_OPT = 8
N_CUERDA_OPT = 4


def construir(estrechamiento, torsion_punta):
    """Ala simétrica. Superficie y envergadura no cambian con el estrechamiento."""
    y_punta = ENVERGADURA / 2
    c_raiz = (2 * SUPERFICIE / ENVERGADURA) / (1 + estrechamiento)
    c_punta = estrechamiento * c_raiz
    x_punta = y_punta * anp.tan(anp.radians(FLECHA_GRADOS))
    perfil = asb.Airfoil(PERFIL)
    ala = asb.Wing(
        name="ala",
        symmetric=True,
        xsecs=[
            asb.WingXSec(xyz_le=[0, 0, 0], chord=c_raiz, twist=0, airfoil=perfil),
            asb.WingXSec(
                xyz_le=[x_punta, y_punta, 0],
                chord=c_punta,
                twist=torsion_punta,
                airfoil=perfil,
            ),
        ],
    )
    avion = asb.Airplane(name="ala demo", wings=[ala])
    return avion


def analizar(estrechamiento, torsion_punta, alpha, n_span, n_cuerda):
    avion = construir(estrechamiento, torsion_punta)
    op = asb.OperatingPoint(velocity=VELOCIDAD, alpha=alpha)
    vlm = asb.VortexLatticeMethod(
        airplane=avion,
        op_point=op,
        spanwise_resolution=n_span,
        chordwise_resolution=n_cuerda,
    )
    return vlm.run(), vlm, op


def alpha_para_cl(estrechamiento, torsion, cl_obj, n_span, n_cuerda, alpha0=4.0):
    alpha = alpha0
    aero, vlm, op = analizar(estrechamiento, torsion, alpha, n_span, n_cuerda)
    for _ in range(8):
        aero_d, _, _ = analizar(estrechamiento, torsion, alpha + 0.25, n_span, n_cuerda)
        pendiente = (aero_d["CL"] - aero["CL"]) / 0.25
        alpha = alpha + (cl_obj - aero["CL"]) / pendiente
        aero, vlm, op = analizar(estrechamiento, torsion, alpha, n_span, n_cuerda)
    return alpha, aero, vlm, op


def eficiencia(aero):
    ar = ENVERGADURA**2 / SUPERFICIE
    return aero["CL"] ** 2 / (np.pi * ar * aero["CD"])


def distribucion_sustentacion(vlm, op, n_cuerda):
    """Sustentación por unidad de envergadura a partir de la fuerza de cada tira."""
    fuerzas = np.asarray(vlm.forces_geometry, dtype=float)
    y = np.asarray(vlm.vortex_centers[:, 1], dtype=float)
    sustentacion = np.empty(len(fuerzas))
    for i, f in enumerate(fuerzas):
        viento = op.convert_axes(
            f[0], f[1], f[2], from_axes="geometry", to_axes="wind"
        )
        sustentacion[i] = -float(viento[2])
    n_tiras = len(fuerzas) // n_cuerda
    y_tira = y.reshape(n_tiras, n_cuerda).mean(axis=1)
    l_tira = sustentacion.reshape(n_tiras, n_cuerda).sum(axis=1)
    orden = np.argsort(y_tira)
    y_tira = y_tira[orden]
    l_tira = l_tira[orden]
    ancho = np.empty_like(y_tira)
    ancho[0] = y_tira[1] - y_tira[0]
    ancho[-1] = y_tira[-1] - y_tira[-2]
    ancho[1:-1] = 0.5 * (y_tira[2:] - y_tira[:-2])
    l_prima = l_tira / ancho
    return y_tira, l_prima, float(l_tira.sum())


def eliptica(y, sustentacion_total):
    """Misma sustentación total, forma elíptica."""
    dentro = np.clip(1 - (2 * y / ENVERGADURA) ** 2, 0, None)
    forma = np.sqrt(dentro)
    # integral de sqrt(1-(2y/b)^2) de -b/2 a b/2 = pi*b/4
    l0 = 4 * sustentacion_total / (np.pi * ENVERGADURA)
    return l0 * forma


def optimizar():
    opti = asb.Opti()
    estrechamiento = opti.variable(
        init_guess=ESTRECHAMIENTO_INICIAL, lower_bound=0.25, upper_bound=1.0
    )
    torsion = opti.variable(init_guess=TORSION_INICIAL, lower_bound=-8.0, upper_bound=3.0)
    alpha = opti.variable(init_guess=4.0, lower_bound=-2.0, upper_bound=12.0)
    aero, _, _ = analizar(estrechamiento, torsion, alpha, N_SPAN_OPT, N_CUERDA_OPT)
    opti.subject_to(aero["CL"] == CL_DISENO)
    opti.minimize(aero["CD"])
    sol = opti.solve(verbose=False)
    return float(sol.value(estrechamiento)), float(sol.value(torsion)), float(sol.value(alpha))


def malla_paneles(vlm, op):
    """Un cuadrilátero por panel. delta_Cp es la fuerza normal adimensional."""
    n = len(vlm.vortex_strengths)
    puntos = np.zeros((4 * n, 3))
    celdas = np.empty(5 * n, dtype=np.int64)
    for i in range(n):
        puntos[4 * i : 4 * i + 4] = (
            vlm.front_left_vertices[i],
            vlm.front_right_vertices[i],
            vlm.back_right_vertices[i],
            vlm.back_left_vertices[i],
        )
        celdas[5 * i : 5 * i + 5] = (4, 4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3)
    tipos = np.full(n, pv.CellType.QUAD, dtype=np.uint8)
    malla = pv.UnstructuredGrid(celdas, tipos, puntos)
    q = float(op.dynamic_pressure())
    normales = np.asarray(vlm.normal_directions, dtype=float)
    fuerzas = np.asarray(vlm.forces_geometry, dtype=float)
    areas = np.asarray(vlm.areas, dtype=float)
    delta_cp = np.sum(fuerzas * normales, axis=1) / (q * areas)
    malla.cell_data["delta_Cp"] = delta_cp
    malla.cell_data["gamma"] = np.asarray(vlm.vortex_strengths, dtype=float)
    return malla


def main():
    alfas = np.linspace(-4, 12, 17)
    cls = []
    cds = []
    for alfa in alfas:
        aero, _, _ = analizar(
            ESTRECHAMIENTO_INICIAL, TORSION_INICIAL, float(alfa), N_SPAN_FINO, N_CUERDA_FINO
        )
        cls.append(float(aero["CL"]))
        cds.append(float(aero["CD"]))
    cls = np.array(cls)
    cds = np.array(cds)
    mascara = (alfas >= -2) & (alfas <= 8)
    cl_alpha_grado, cl0 = np.polyfit(alfas[mascara], cls[mascara], 1)
    cl_alpha_rad = cl_alpha_grado * 180 / np.pi

    alpha_antes, aero_antes, vlm_antes, op_antes = alpha_para_cl(
        ESTRECHAMIENTO_INICIAL, TORSION_INICIAL, CL_DISENO, N_SPAN_FINO, N_CUERDA_FINO
    )
    e_antes = float(eficiencia(aero_antes))

    estrechamiento_opt, torsion_opt, alpha_opt_grueso = optimizar()
    alpha_despues, aero_despues, vlm_despues, op_despues = alpha_para_cl(
        estrechamiento_opt,
        torsion_opt,
        CL_DISENO,
        N_SPAN_FINO,
        N_CUERDA_FINO,
        alpha0=alpha_opt_grueso,
    )
    e_despues = float(eficiencia(aero_despues))

    y_a, l_a, L_a = distribucion_sustentacion(vlm_antes, op_antes, N_CUERDA_FINO)
    y_d, l_d, L_d = distribucion_sustentacion(vlm_despues, op_despues, N_CUERDA_FINO)
    y_fino = np.linspace(-ENVERGADURA / 2, ENVERGADURA / 2, 400)

    plt.figure(figsize=(8, 5))
    plt.plot(alfas, cls, "o-", label="VLM")
    plt.plot(alfas, cl_alpha_grado * alfas + cl0, "--", label="ajuste lineal")
    plt.xlabel("ángulo de ataque [grados]")
    plt.ylabel("CL")
    plt.title("Sustentación frente al ángulo de ataque")
    plt.grid()
    plt.legend()
    plt.savefig(OUT / "cl_alpha.png", dpi=120)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(cds, cls, "o-")
    plt.scatter(
        [aero_antes["CD"]],
        [aero_antes["CL"]],
        zorder=3,
        label="punto de diseño",
    )
    plt.xlabel("CD")
    plt.ylabel("CL")
    plt.title("Polar del VLM (solo resistencia inducida)")
    plt.grid()
    plt.legend()
    plt.savefig(OUT / "polar.png", dpi=120)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(y_a, l_a, label="antes")
    plt.plot(y_d, l_d, label="después")
    plt.plot(y_fino, eliptica(y_fino, L_a), "k--", label="elíptica")
    plt.xlabel("y [m]")
    plt.ylabel("sustentación por unidad de envergadura [N/m]")
    plt.title(f"Distribución a CL = {CL_DISENO}")
    plt.grid()
    plt.legend()
    plt.savefig(OUT / "sustentacion.png", dpi=120)
    plt.close()

    malla = malla_paneles(vlm_antes, op_antes)
    malla.save(OUT / "ala.vtu")

    print("CL_alpha por grado", cl_alpha_grado)
    print("CL_alpha por radian", cl_alpha_rad)
    print("CL0 ajuste", cl0)
    print("antes estrechamiento", ESTRECHAMIENTO_INICIAL, "torsion", TORSION_INICIAL)
    print("antes alpha", alpha_antes, "CL", aero_antes["CL"], "CD", aero_antes["CD"], "e", e_antes)
    print("opt estrechamiento", estrechamiento_opt, "torsion", torsion_opt)
    print(
        "despues alpha",
        alpha_despues,
        "CL",
        aero_despues["CL"],
        "CD",
        aero_despues["CD"],
        "e",
        e_despues,
    )
    print("delta_Cp", float(malla.cell_data["delta_Cp"].min()), float(malla.cell_data["delta_Cp"].max()))
    print("paneles", malla.n_cells)

    pv.OFF_SCREEN = True
    plotter = pv.Plotter(off_screen=True, window_size=(1100, 700))
    plotter.set_background("white")
    actor = plotter.add_mesh(
        malla,
        scalars="delta_Cp",
        cmap="coolwarm",
        show_edges=True,
        scalar_bar_args={"title": "delta Cp"},
    )
    actor.prop.SetBackfaceCulling(0)
    actor.prop.SetFrontfaceCulling(0)
    plotter.add_axes()
    plotter.camera_position = [(6.5, -8.0, 4.5), (1.3, 0.0, 0.0), (0.0, 0.0, 1.0)]
    plotter.screenshot(OUT / "ala_3d.png")
    plotter.export_html(OUT / "ala_interactiva.html")
    plotter.close()
    print("html", (OUT / "ala_interactiva.html").stat().st_size)


if __name__ == "__main__":
    main()
