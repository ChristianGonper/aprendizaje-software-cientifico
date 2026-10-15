# Aprendizaje de software científico

Repositorio de Christian para aprender software científico y herramientas de ingeniería, con orientación a la ingeniería aeroespacial.

Cada lección vive en su propia carpeta, con el código, las notas y las figuras.

## Índice

| Lección | Contenido |
| --- | --- |
| [01 — Sistema de segundo orden](01-control-segundo-orden/) | Respuesta al escalón, amortiguamiento, frecuencia natural, diagrama de Bode y comparación entre función de transferencia y espacio de estados. |

## Entorno

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dependencias: NumPy, SciPy, Matplotlib y python-control (`control`).
