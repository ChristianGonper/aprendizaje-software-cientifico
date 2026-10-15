# Lección 1 — Sistema de segundo orden

## Concepto

- **Estado**: mínimo conjunto de variables que, junto con la entrada, determina la evolución futura. Aquí $x_1 = y$ (posición), $x_2 = \dot{y}$ (velocidad).
- **EDO**:

$$\ddot{y} + 2\zeta\omega_n \dot{y} + \omega_n^2 y = \omega_n^2 u.$$

- **Función de transferencia** (Laplace, condiciones iniciales nulas): $G(s)=\frac{\omega_n^2}{s^2+2\zeta\omega_n s+\omega_n^2}$. Ganancia estática $G(0)=1$.
- **Polos**: raíces del denominador,

$$s = -\zeta\omega_n \pm \omega_n\sqrt{\zeta^2-1}.$$

Parte real: velocidad de decaimiento. Parte imaginaria: frecuencia de oscilación, $\omega_d = \omega_n\sqrt{1-\zeta^2}$.

- **$\zeta$ (amortiguamiento)**: forma de la respuesta. $\zeta<1$ subamortiguado (polos complejos, oscila), $\zeta=1$ crítico (polo doble real), $\zeta>1$ sobreamortiguado (dos polos reales, uno lento).
- **$\omega_n$ (frecuencia natural)**: escala de tiempo. Con $\zeta$ fija, duplicar $\omega_n$ hace la respuesta el doble de rápida, con la misma forma.

$$M_p = \exp\left(\frac{-\zeta\pi}{\sqrt{1-\zeta^2}}\right), \qquad t_s \approx \frac{4}{\zeta\omega_n}.$$

$t_s$ es el tiempo de establecimiento en la banda del 2 %.

## Qué hace [segundo_orden.py](segundo_orden.py)

1. `G(zeta, wn)`: crea la función de transferencia con `control.tf`.
2. Escalón con $\omega_n=2$ y $\zeta \in \lbrace 0.1, 0.3, 0.5, 0.7, 1, 2 \rbrace$.
3. Escalón con $\zeta=0.3$ y $\omega_n \in \lbrace 0.5, 1, 2, 4 \rbrace$.
4. `control.step_info` ($M_p$, tiempo de subida del 10 % al 90 %, $t_s$ al 2 %) frente a las fórmulas, más los polos.
5. Bode para $\zeta \in \lbrace 0.1, 0.3, 0.7, 2 \rbrace$.
6. El mismo sistema en espacio de estados, integrado con `scipy.integrate.solve_ivp` y superpuesto a la función de transferencia.

Desde la raíz del repositorio:

```bash
uv run python 01-control-segundo-orden/segundo_orden.py
```

## Resultados ($\omega_n = 2\ \mathrm{rad/s}$)

| $\zeta$ | $M_p$ num % | $M_p$ teórico % | $t_r$ [s] | $t_s$ num [s] | $4/(\zeta\omega_n)$ [s] | polos |
|---|---|---|---|---|---|---|
| 0.1 | 72.92 | 72.92 | 0.555 | 19.20 | 20.00 | $-0.2 \pm 1.99j$ |
| 0.3 | 37.23 | 37.23 | 0.660 | 5.62 | 6.67 | $-0.6 \pm 1.91j$ |
| 0.5 | 16.30 | 16.30 | 0.820 | 4.04 | 4.00 | $-1.0 \pm 1.73j$ |
| 0.7 | 4.60 | 4.60 | 1.065 | 2.99 | 2.86 | $-1.4 \pm 1.43j$ |
| 1.0 | 0 | 0 | 1.675 | 2.92 | 2.00 | $-2,\ -2$ |
| 2.0 | 0 | 0 | 4.111 | 7.44 | 1.00 | $-7.46,\ -0.54$ |

Lectura:

- $M_p$ coincide exactamente: la fórmula es exacta.
- $t_s \approx 4/(\zeta\omega_n)$ es una cota de la envolvente. Es una buena aproximación para $\zeta \lesssim 0.7$ y no vale para $\zeta \ge 1$. Para $\zeta=2$ domina el polo lento $-0.54$, así que $t_s \approx 4/0.54 \approx 7.4\ \mathrm{s}$.
- Función de transferencia frente a `solve_ivp` ($\zeta=0.3$): error máximo $4\cdot 10^{-10}$. Las dos formulaciones son el mismo sistema.
- Bode: pico de resonancia cerca de $\omega_n$ para $\zeta$ pequeño ($\approx +14\ \mathrm{dB}$ con $\zeta=0.1$); fase $-90^\circ$ en $\omega=\omega_n$ para todo $\zeta$; pendiente $-40\ \mathrm{dB}/\mathrm{década}$ a alta frecuencia.

![Respuesta al escalón con $\omega_n$ fija y varios $\zeta$](escalon_zeta.png)

![Respuesta al escalón con $\zeta$ fijo y varios $\omega_n$](escalon_wn.png)

![Diagrama de Bode para varios $\zeta$](bode_zeta.png)

![Comparación entre función de transferencia y espacio de estados](comparacion_ss_tf.png)

## Para predecir antes de la lección 2

1. ¿Qué pasa con la respuesta al escalón si $\zeta = -0.2$? ¿Dónde quedan los polos en el plano $s$?
2. Con $\zeta = 0$, ¿dónde están los polos y cómo es la respuesta? ¿Qué valor tiene el pico de Bode?
3. Si quieres un $t_s$ más corto sin cambiar $M_p$, ¿qué parámetro tocas y cómo se mueven los polos?

## Respuestas

1. Si $\zeta < 0$ (por ejemplo $\zeta = -0.2$), los polos quedan en el semiplano derecho. La respuesta al escalón diverge.
2. Con $\zeta = 0$ los polos están en $\pm j\omega_n$. La respuesta al escalón es

$$y(t) = 1 - \cos(\omega_n t)$$

y el pico de resonancia de Bode es infinito.

3. Para acortar $t_s$ sin cambiar $M_p$ se sube $\omega_n$. $M_p$ depende solo de $\zeta$, así que los polos se desplazan radialmente y conservan el ángulo. El coste es un mayor ancho de banda y un mayor esfuerzo del actuador.
