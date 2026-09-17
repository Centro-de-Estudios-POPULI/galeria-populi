"""
Publica las IMÁGENES del Banco (public/graficas + public/thumbs) en la rama
`laminas`, que tiene SIEMPRE un solo commit: la última versión y nada más.

★ POR QUÉ. Las imágenes no viven en la historia de `main`. Cada regeneración
  completa de las 606 láminas de mapa sumaba ~170 MB a `.git` (2026-09-16: 1,0 GB;
  2026-09-17: 425 MB tras una sola regeneración). En `main` van el código, las
  fichas y el manifiesto (~30 MB); las imágenes van en una rama huérfana que se
  RECREA en cada publicación, así el repo no engorda nunca más.

  La Action de Pages hace checkout de `main` y de `laminas`, copia las imágenes a
  `public/` y construye el sitio. Localmente las imágenes siguen en `public/`
  (ignoradas por git), que es donde `build_manifest()` y `verificar.py` las miran.

Uso (desde la raíz del repo, después de generar y de commitear `main`):

    python scripts/publicar_laminas.py            # arma la rama y la empuja (forzado)
    python scripts/publicar_laminas.py --sin-push # sólo arma la rama local

El push es forzado porque la rama se recrea desde cero (un commit sin padre).
Si el entorno bloquea el push forzado, correrlo a mano:

    git push --force origin laminas

⚠️ EL PUSH A `laminas` NO DISPARA LA ACTION (comprobado 2026-09-17): GitHub lee el
workflow desde la rama empujada, y la huérfana no tiene `.github/`. El `push:
branches: [laminas]` del deploy.yml es letra muerta. Por eso, después del push,
este script dispara el workflow a mano (`gh workflow run deploy.yml --ref main`).
Si `gh` no está, hay que dispararlo desde la pestaña Actions o hacer un push a main
DESPUÉS de publicar las láminas; si no, el sitio se construye con las imágenes viejas.
"""
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

# la consola de Windows es cp1252 y se atraganta con las flechas
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
RAMA = "laminas"
WORKFLOW = "deploy.yml"
CARPETAS = ["public/graficas", "public/thumbs"]
SIN_PUSH = "--sin-push" in sys.argv


def git(*args, env=None, check=True):
    r = subprocess.run(["git", *args], cwd=ROOT, env=env, text=True,
                       capture_output=True, encoding="utf-8")
    if check and r.returncode:
        sys.exit(f"⛔ git {' '.join(args)}\n{r.stderr.strip()}")
    return r.stdout.strip()


def main():
    faltan = [c for c in CARPETAS if not (ROOT / c).is_dir()]
    if faltan:
        sys.exit(f"⛔ no están {faltan}: generá las láminas antes de publicarlas")
    n_png = len(list((ROOT / "public/graficas").glob("*.png")))
    n_webp = len(list((ROOT / "public/thumbs").glob("*.webp")))
    if n_png == 0 or n_png != n_webp:
        sys.exit(f"⛔ {n_png} PNG y {n_webp} WebP: tiene que haber la misma cantidad y más de cero")

    # Índice TEMPORAL: se agregan sólo las dos carpetas (con -f, porque están en
    # .gitignore) y se escribe un árbol que no toca el índice real ni la rama actual.
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / "indice"))
        git("add", "-f", "--", *CARPETAS, env=env)
        arbol = git("write-tree", env=env)
    mensaje = (f"Láminas al {date.today().isoformat()}: {n_png} gráficas\n\n"
               "Rama huérfana recreada por scripts/publicar_laminas.py: un solo commit, "
               "siempre la última versión. Las imágenes no viven en la historia de main.")
    commit = git("commit-tree", arbol, "-m", mensaje)
    git("update-ref", f"refs/heads/{RAMA}", commit)
    print(f"rama {RAMA} → {commit[:7]} ({n_png} PNG + {n_webp} WebP, un solo commit)")

    if SIN_PUSH:
        print("sin push (--sin-push). Para empujar: git push --force origin laminas")
        return
    r = subprocess.run(["git", "push", "--force", "origin", RAMA], cwd=ROOT, text=True,
                       capture_output=True, encoding="utf-8")
    if r.returncode:
        sys.exit("⛔ el push forzado falló (¿bloqueado por el entorno?). Correrlo a mano:\n"
                 f"    git push --force origin {RAMA}\n{r.stderr.strip()}")
    print(f"empujada: origin/{RAMA} = {commit[:7]}")

    # La Action no se entera del push a la huérfana: se dispara a mano.
    r = subprocess.run(["gh", "workflow", "run", WORKFLOW, "--ref", "main"], cwd=ROOT,
                       text=True, capture_output=True, encoding="utf-8")
    if r.returncode:
        print("⚠️ no pude disparar la Action con gh; hacelo desde la pestaña Actions o con un push "
              f"a main, si no el sitio queda con las láminas viejas.\n{r.stderr.strip()}")
    else:
        print(f"Action disparada ({WORKFLOW}, ref main): el sitio se construye con estas láminas.")


if __name__ == "__main__":
    main()
