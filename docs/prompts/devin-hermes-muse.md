# Prompt para Devin — usar Hermes con modelos Muse (Meta Model API)

Copia y pega el bloque de abajo como instrucción de tarea para Devin. Es autocontenido.

---

```
CONTEXTO
Trabajas en el repo ~/GitHub/meta-hack (Meta Global AI Developer Hackathon, track indie).
Además de tu propio modelo, puedes delegar subtareas de LLM a Hermes, que ya está
configurado con los modelos Muse de Meta Model API en esta máquina. Hermes ejecuta el
turno con el modelo que le pidas y devuelve texto por stdout; también puede usar
herramientas (terminal, ficheros, web) si le das un objetivo que las requiera.

PERFIL CORRECTO (importante)
Usa SIEMPRE el perfil `meta-hack`:
    hermes -p meta-hack chat ...
NO uses el perfil por defecto: su memoria, su perfil de usuario y su índice de skills
contienen información interna del laboratorio y ese contenido no debe salir de aquí.

MODELOS: cuándo usar cada uno
    muse-spark-1.3-contributor   (default del perfil)  → trabajo masivo y barato: extracción
                                  de abstracts, clasificación, JSON tipado en lote, borradores.
                                  OJO: Meta puede entrenar con este contenido. Solo material
                                  público (papers, abstracts, código del repo).
    muse-spark-1.3               (estándar)            → razonamiento y código: revisión de
                                  parches, diseño de heurísticas, depuración, decisiones
                                  tipadas sobre diagnósticos.
    muse-wonder-1.0              (estándar)            → narrativa de demo, síntesis,
                                  explicaciones de cara al jurado. Es el más caro; úsalo
                                  para pocas llamadas de alto valor.
Nunca uses muse-* para datos del laboratorio, datasets internos ni credenciales.

CÓMO INVOCARLO (no interactivo, sin TTY)
    # una pregunta, salida limpia (sin banner) — lo normal en tus scripts
    hermes -p meta-hack chat -Q -q "<tarea concreta y autocontenida>"

    # forzar modelo y esfuerzo de razonamiento
    hermes -p meta-hack chat -Q -m muse-spark-1.3 --reasoning high -q "<tarea>"
    hermes -p meta-hack chat -Q -m muse-wonder-1.0 --reasoning max -q "<tarea>"

    # si la tarea necesita ejecutar comandos o leer ficheros, deja que Hermes use sus tools
    hermes -p meta-hack chat -Q --yolo -q "lee pipeline/build_risk.py y dime por qué falla"

    # varias preguntas sobre el mismo contexto → UNA sesión, no N llamadas sueltas
    hermes -p meta-hack chat -Q -c devin-buildrisk --create-if-missing -q "turno 1: ..."
    hermes -p meta-hack chat -Q -c devin-buildrisk -q "turno 2: ..."

    # prompt largo → fichero, no inline
    hermes -p meta-hack chat -Q --query-file /tmp/tarea.md

Salida: el texto de la respuesta por stdout; exit code 0 si terminó. `-Q` suprime banner y
metadatos de sesión, deja solo la respuesta.

REGLAS DE USO
1. Autocontenido: Hermes no ve tu conversación ni tu historial. Dale rutas absolutas,
   el objetivo, el formato de salida esperado y el criterio de aceptación.
2. No le pegues megabytes. Dile qué ficheros leer y que los lea él con sus tools.
3. Una sesión larga con -c es más barata que muchas llamadas sueltas: la primera
   llamada de una sesión paga el prefijo completo; a partir de ahí el 74-95% viene de
   caché.
4. Coste medido en esta máquina: ~$0.0018 por sesión de 2 llamadas con tool en el perfil
   contributor; ~$0.03 en el perfil estándar. Si vas a hacer más de ~50 llamadas
   contributor seguidas, avisa: el límite del tier contributor es 150 RPM.
5. Si el resultado es JSON, pídelo con esquema explícito y valida antes de usarlo
   (Hermes no garantiza el esquema salvo que se lo impongas tú).
6. Devuelve SIEMPRE un resumen de qué delegaste y el coste, para el log del proyecto.

QUÉ DELEGAR (buenos encajes en este repo)
- Extracción/estructuración de abstracts OpenAlex → JSON (contributor).
- Decisiones tipadas sobre diagnósticos de fits (spread de AIC, flags, n bajo) → JSON
  estricto con `{decision, switch_to, confidence, reason}` (spark-1.3).
- Revisión crítica de un parche antes de commitear (spark-1.3), pidiendo lista de
  defectos con fichero:línea.
- Redacción de la narrativa del briefing y del guion del vídeo de 3 minutos (wonder).
- Explicaciones por condado/especie para la app (spark-1.3).

QUÉ NO DELEGAR
- Decisiones de arquitectura del repo (es tu trabajo).
- Cualquier cosa con datos internos del laboratorio o credenciales.
- Ejecución de jobs de cluster (Hermes no debe lanzar SLURM por ti en este proyecto).

VERIFICACIÓN (hazlo tú, no te fíes del eco)
    # ¿realmente usó Meta y cuánto costó?
    python3 - <<'PY'
    import sqlite3, os
    db=os.path.expanduser('~/.hermes/profiles/meta-hack/state.db')
    c=sqlite3.connect(f'file:{db}?mode=ro', uri=True)
    for r in c.execute("""select model, billing_provider, api_call_count,
                                 input_tokens, cache_read_tokens, output_tokens,
                                 round(estimated_cost_usd,5)
                          from session_model_usage order by first_seen desc limit 5"""):
        print(r)
    PY
    # billing_provider debe ser 'meta-ai'. Si aparece 'openrouter', el id de modelo
    # estaba mal y hubo fallback silencioso.

    # si algo falla, el log del perfil es aquí:
    tail -40 ~/.hermes/profiles/meta-hack/logs/agent.log

Si Hermes devuelve un error HTTP 4xx de Meta, no reintentes a ciegas: revisa el log, y si
es `reasoning_effort` no soportado recuerda que Muse acepta minimal|low|medium|high|xhigh
(y `max` solo en muse-wonder-1.0 y muse-spark-1.3 estándar).
```
