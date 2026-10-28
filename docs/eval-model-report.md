# Brújula — modelo interno de evaluación del proyecto (v1)

Qué es: un scorecard de gates chequeables + Monte Carlo que traduce
"cómo va el proyecto" a un número comparable día a día y a una P(premio)
por escenario de campo. No predice el futuro; ordena el trabajo.
Código: `tools/eval_tracker.py`. Estado: `tools/eval_state.json` (devel-only).

## 1. Arquitectura del modelo (3 capas)

Capa 1 — Supervivencia (puerta Stage-1, multiplicativa).
6 gates S1-S6: snapshot público con cold-open, litmine visible, 5 strings
Muse grepeables, disclaimer no-médico, proveniencia verdadera, live sin key.
Cada miss multiplica P(stage1) x0.7 (base 0.99). Lógica: un miss no resta
puntos, te descalifica; por eso no suma, multiplica.

Capa 2 — Buckets de rúbrica (suma ponderada 0-10).
Impact 30 / Tooling 25 / Demo 25 / Depth 20 (pesos oficiales del hackathon).
Cada bucket tiene checks con puntos que suman 10:
- Impact (10): we-called-it congelada 3.0, confirmación por PMID 2.0,
  agro separado no-médico 2.0, narrativa huevos/supply-chain 1.5,
  beneficiario declarado 1.5.
- Tooling (10): cascada 4 modelos visible 3.0, switch_to ejecutable 2.0,
  wonder 1.5, glimmer self-host 2.0, ledger de costo 1.5.
- Demo (10): live rápido 2.5, video 3 min 2.5, ticker del loop 2.0,
  cost meter 1.5, backup grabado 1.5.
- Depth (10): craft screen 2.5, leakage audit 2.5, precisión G1 1.5,
  fail-closed 2.0, phy real + normalización 1.5.
Cada check vale 0 / 0.5 / 1. Score bucket = 10 x puntos_ganados / 10.
Total = suma ponderada con los pesos oficiales.

Capa 3 — Monte Carlo a P(premio) (3 escenarios de campo).
Cada bucket alimenta una Normal(media=score, sd 0.6-0.7); se simula el total
ponderado propio vs N rivales con totales ~ Normal(mu, sd), 30k trials.
P(top5|pass) = fracción donde menos de 5 rivales nos superan.
P(premio) = P(stage1) x P(top5|pass). Escenarios: chico-flojo (80, 6.0),
medio (150, 6.5), grande-fuerte (300, 7.0). El campo real es desconocido;
el rango entre escenarios ES el resultado, no un número único.

## 2. Lectura actual (2026-10-28, 28 entradas)

Buckets: Impact 8.0, Tooling 10.0, Demo 7.2, Depth 9.2 → total 8.56/10.
P(stage1) 0.99 (supervivencia completa).
P(premio): 0.98 / 0.63 / 0.02 según escenario.
Gaps abiertos (puntos ponderados en mesa): I2_confirm +0.60, D5_backup
+0.38, D2_video +0.31, H3_prec +0.15. Total en mesa: +1.44 → techo 10.0.

Diagnóstico en una línea: el motor está listo (Tooling 10, Depth 9.2),
falta venderlo (Demo 7.2 es el mínimo) y cerrarlo con una confirmación
(I2). El cuello de botella es video + backup, no más ciencia.

## 3. Cómo guía el research (reglas de uso)

Regla 1 — Atacar por puntos ponderados por hora, no por gusto.
El tracker imprime "top gaps" ya multiplicados por el peso del bucket:
un +0.60 en Impact vale triple que un +0.20 en Depth. La cola oficial vive
en docs/devin-attack-queue.md y se regenera del state.

Regla 2 — Supervivencia antes que puntos.
Si algún S cae debajo de 1 (ej. un cambio rompe el live), todo lo demás
espera: P(stage1) 0.7x por miss hunde el P(premio) más que cualquier gate.

Regla 3 — Cerrar, no abrir.
Un check en 0.5 rinde la mitad de puntos por el mismo esfuerzo ya invertido.
Prioriza 0.5→1 (D2_video, H3_prec) sobre 0→0.5 nuevos, salvo que el top gap
diga otra cosa.

Regla 4 — El techo también informa.
Tooling en 10.0 significa: ni una hora más a tooling. Toda hora va a Demo
(7.2) o al +0.60 de I2. Si un bucket llega a 9+, se congela y se protege
con tests, no se pule.

Regla 5 — Marcar solo con evidencia verificada por segundo par.
Quien implementa no marca: `set <ID> 1` lo hace Hermes tras reproducir la
evidencia (diff, tests propios, endpoint). Marcar sin verificar infla el
total y la brújula miente. Sesgo conocido: los 1.0 actuales los marcó el
equipo, no un juez; leer el total con -0.5 de humildad.

## 4. Comandos

Ver parte: `.venv/bin/python tools/eval_tracker.py score`
Marcar gate: `... set <ID> <0|0.5|1>` (solo Hermes tras verificación)
Curva: `... history` (si no sube ~1 punto/día hasta el Nov-4, no alcanza)

## 5. Limitaciones honestas (leer antes de citar un número)

- Los scores de bucket son autoevaluación; un juez puede ver 1-2 puntos menos.
- mu/sd de rivales y N son supuestos, no datos. El rango 0.02-0.98 refleja
  ignorancia real del campo, no precisión del modelo.
- El modelo ignora correlación entre jueces, efecto video-viral y bonus
  ($10k open-weights, $5k agentic, community vote), que son valor esperado
  aparte y probablemente alto para este proyecto.
- buckets gaussianos independientes es simplificación: Impact y Demo
  correlacionan en la mente del juez (lo que emociona se cree si se ve).
  Si algo, el modelo SUBESTIMA combos Impact+Demo como we-called-it+video.
