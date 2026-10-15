# Convenciones

Texto en español de España.

## Entorno

Las dependencias van en [pyproject.toml](pyproject.toml) y quedan fijadas en [uv.lock](uv.lock). No se usa `requirements.txt`.

```bash
uv sync
uv run python 01-control-segundo-orden/segundo_orden.py
```

## Matemáticas

En Markdown, las matemáticas se escriben en LaTeX. GitHub pinta `$...$` en línea y `$$...$$` como ecuación destacada. No se usan símbolos Unicode ni ASCII en lugar de LaTeX.

En línea: $\zeta$, $\omega_n$, $M_p$, $t_s$, $G(s)=\frac{\omega_n^2}{s^2+2\zeta\omega_n s+\omega_n^2}$.

No escribas `%` dentro de `$...$` ni de `$$...$$`. Markdown trata la barra de `\%` como un escape de puntuación y la elimina; el `%` que queda es un comentario de LaTeX y GitHub tira el resto de la línea. El tanto por ciento va fuera de las matemáticas, como en «banda del 2 %». Por la misma razón, `\,` y `\{` pierden la barra: las llaves de un conjunto se escriben `\lbrace` y `\rbrace`.

Destacada:

$$G(s)=\frac{\omega_n^2}{s^2+2\zeta\omega_n s+\omega_n^2}.$$

## Enlaces y figuras

Un fichero de código se enlaza con la sintaxis habitual de Markdown, por ejemplo [segundo_orden.py](01-control-segundo-orden/segundo_orden.py). Una figura se incrusta con `![descripción](figura.png)`, no con el nombre del fichero entre comillas o en código.
