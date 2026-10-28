# niche-factory — AI factory de modelos de distribución potencial
(nombre provisional — internal design note)

Tercera instancia del patrón AI factory. Producto: modelos de nicho
elipsoidal automatizados cuya salida alimenta el eje ambiental de
interseek/interseekr (`j_env` — la matriz de disimilitud ambiental que
consumen tanto susceptibilidad L1 como link-prediction L2).

## El problema de investigación

Hoy el criterio de inclusión es `>= 100 puntos ambientales únicos por
especie`. Hipótesis del usuario: **es mucho más de lo necesario**, y
el umbral correcto no es global — depende de la variable.

- **Cotas de muestreo por variable**: el n mínimo para que el
  elipsoide (media + covarianza) sea estable depende de la varianza,
  curtosis y colas de CADA variable ambiental. Un bio1 casi gaussiano
  converge con ~20-30 puntos; una bio15 con estacionalidad fuerte
  puede requerir más.
- **88 combinaciones**: el espacio de subconjuntos de variables
  (o método × variable) que hoy se evalúa completo — redundancia
  ambiental real (bio1~bio12 correlacionados) implica que muchas
  combinaciones aportan lo mismo.
- **Cotas analíticas para velocidad**: ajustar ~1,148 elipsoides × 88
  combos es caro. Cotas útiles: n suficiente para error de
  Mahalanobis-centroide < eps (convergencia del estimador), poda de
  combos por correlación de variables previa al ajuste, y
  early-stopping cuando el volumen del elipsoide se estabiliza.

## Preguntas medibles

1. ¿Cuál es el n mínimo por variable donde el centro del elipsoide
   converge? (subsampling: error del estimador vs n, por variable,
   sobre especies con >100 puntos como ground truth)
2. ¿Cuántas de las 88 combinaciones son redundantes? (clustering de
   vectores de variables por correlación en el cubo ambiental)
3. ¿El ranking de especies por `j_env` se preserva si se ajustan
   elipsoides con n reducido / variables podadas? — la métrica que
   importa: Spearman del eje ambiental, no el elipsoide en sí.
4. ¿Cotas tipo concentración de medida (n ~ O(k log k) para k vars)
   predicen el punto de estabilidad real?

## Instancia en el patrón

```
ENTRADA  ocurrencias por especie (GBIF/biostaging) + cubo ambiental
         (xbioclim/era5) -> puntos ambientales únicos por especie
SPEC     decide n_effective y subset de variables por especie según
         la cota por variable; poda combos redundantes
BUILDER  ajuste elipsoidal por especie×combo (embarrassingly parallel)
JUDGE    estabilidad del fit: error centroide/volumen vs bootstrap;
         flags especies bajo-cota (salida honesta, no extrapolar)
APPROVER tabla de criticidad: cambios en el ranking j_env > tol
         -> revisión; refinamiento -> directo
PRODUC   env_niche.parquet por especie -> jaccard_env -> interseek
BRAIN    ledger: n usado, combo elegido, estabilidad medida — el
         sistema APRENDE la cota empírica por variable
```

## Relación con los otros frentes

```
niche-factory (este)   -> j_env (eje ambiental)
litmine                -> edges/labels (evidencia)
interaction_model      -> L2 p_share (usa j_env + j_geo + phy)
suscept_model          -> L1 p_host (usa los mismos ejes)
interseek/interseekr   -> el paquete que los consume
```

Si la poda demuestra que ~30 puntos y ~10 variables bastan, el
universo de especies modelables crece (especies con 30-99 puntos hoy
descartadas entran al eje ambiental) — más cobertura para L1 y L2.

## Estado

Experimento Q1 construido y probado en local (ver
`subsample-protocol.md`). Pendiente: corrida en kuhpc
(SPEC -> sbatch array -> JUDGE). Q2/Q3/Q4 diferidos como stages.
