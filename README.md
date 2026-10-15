# Aprendizaje de software científico

Repositorio de Christian para aprender software científico y herramientas de ingeniería, con orientación a la ingeniería aeroespacial.

Cada lección vive en su propia carpeta, con el código, las notas y las figuras. Las convenciones de escritura y de entorno están en [CONVENCIONES.md](CONVENCIONES.md).

## Índice

| Lección | Contenido |
| --- | --- |
| [01 — Sistema de segundo orden](01-control-segundo-orden/) | Respuesta al escalón, amortiguamiento $\zeta$, frecuencia natural $\omega_n$, diagrama de Bode y comparación entre función de transferencia y espacio de estados. |

## Entorno

El entorno se gestiona con [uv](https://docs.astral.sh/uv/). Hace falta Python 3.11 o posterior.

```bash
uv sync
uv run python 01-control-segundo-orden/segundo_orden.py
```

Dependencias: NumPy, SciPy, Matplotlib y python-control (`control`), declaradas en [pyproject.toml](pyproject.toml).
