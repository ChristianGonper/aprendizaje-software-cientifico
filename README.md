# Aprendizaje de software científico

Repositorio de Christian para aprender software científico y herramientas de ingeniería, con orientación a la ingeniería aeroespacial.

Cada lección vive en su propia carpeta, con el código, las notas y las figuras. Las convenciones de escritura y de entorno están en [CONVENCIONES.md](CONVENCIONES.md).

## Índice

| Lección | Contenido |
| --- | --- |
| [01 — Sistema de segundo orden](01-control-segundo-orden/) | Respuesta al escalón, amortiguamiento $\zeta$, frecuencia natural $\omega_n$, diagrama de Bode y comparación entre función de transferencia y espacio de estados. |
| [02 — Control PID](02-control-pid/) | Lazo cerrado con P, PI, PD y PID sobre un cabeceo reducido: error en régimen permanente, amortiguamiento, esfuerzo de mando y polos. |
| [03 — Saturación y anti-windup](03-saturacion-antiwindup/) | PID con mando saturado: windup del integrador, integración condicional, back-calculation y derivada sobre la medida. |

## Demostraciones

| Demo | Contenido |
| --- | --- |
| [01 — Ala con VLM](demos/01-ala-aerosandbox-pyvista/) | Ala en flecha, vortex lattice, optimización de estrechamiento y torsión, y malla 3D con PyVista. |

## Entorno

El entorno se gestiona con [uv](https://docs.astral.sh/uv/). Hace falta Python 3.11 o posterior.

```bash
uv sync
uv run python 01-control-segundo-orden/segundo_orden.py
uv run python 02-control-pid/pid.py
uv run python 03-saturacion-antiwindup/antiwindup.py
uv run python demos/01-ala-aerosandbox-pyvista/ala.py
```

Dependencias: NumPy, SciPy, Matplotlib, python-control (`control`), AeroSandbox y PyVista, declaradas en [pyproject.toml](pyproject.toml).
