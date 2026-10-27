#!/usr/bin/env bash
# release.sh "slug" — gate de revision Muse + push al repo publico.
#
# Flujo:  devel (origin, privado) -> revision muse-spark-1.3 -> public (meta-hack)
# La revision queda en docs/muse-reviews/ y viaja en el mismo push.
set -euo pipefail
cd "$(dirname "$0")/.."

SLUG="${1:-release}"
STAMP=$(date +%F)
OUT="docs/muse-reviews/${STAMP}-${SLUG}.md"

git fetch -q public main
BASE=$(git rev-parse public/main)
DIFF=$(git diff "$BASE"..HEAD)
if [ -z "$DIFF" ]; then echo "nada que soltar (HEAD == public/main)"; exit 0; fi

mkdir -p docs/muse-reviews
echo "$DIFF" > /tmp/wildseek-release.diff
LINES=$(wc -l < /tmp/wildseek-release.diff)

if command -v hermes >/dev/null && [ "$LINES" -lt 40000 ]; then
    PROMPT=$(mktemp /tmp/muse-review.XXXX.md)
    cat > "$PROMPT" <<EOF
Revisa este diff de release del repo WildSeek (hackathon). Encuentra
defectos concretos fichero:linea: bugs, secretos, rutas absolutas
personales, datos internos que no deban ser publicos, dead code que
rompa. Si esta limpio, dilo. Formato: lista de hallazgos, luego
veredicto SHIP/NO-SHIP.

$(cat /tmp/wildseek-release.diff)
EOF
    hermes -p meta-hack chat -Q -m muse-spark-1.3 --query-file "$PROMPT" \
        | tee "$OUT" || echo "muse cayo; revisa $OUT"
    echo "review -> $OUT"
else
    echo "hermes no disponible o diff grande ($LINES lineas); release sin review" | tee "$OUT"
fi

git add docs/muse-reviews && git commit -qm "docs: muse review ${SLUG}" || true
git push -q origin main && git push -q public main
echo "soltado a public/main ($(git rev-parse --short HEAD))"
