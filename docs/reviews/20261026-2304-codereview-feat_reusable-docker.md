# Code review — feat/reusable-docker / feat/enrama-docker — 2026-10-26

## Metadata

- Repositorios: `enrama`, `amapola-links`, checkouts aislados de task-3.
- Ramas: `feat/reusable-docker`, `feat/enrama-docker`.
- Bases/tips al revisar: Enrama `develop` / `7953e90`; consumidor `origin/main` / `3937c11`.
- Incluye cambios sin commitear: sí, incluidos archivos nuevos y el ejemplo de entorno ignorado.
- Reviewer: skill code-review-fullstack.
- Metodología: diff completo de los cambios Docker, scripts, documentación y modificación de preview; inspección adyacente de locks y publicación de dist.
- Destino local autorizado expresamente en delegación; no aplica la ruta Windows del skill.

## Resumen ejecutivo

Dos hallazgos Medium afectan la reproducibilidad del CLI y la entrega del archivo de configuración de ejemplo. No se confirmaron defectos nuevos en los locks, reemplazo atómico, aislamiento del contenido, bind loopback, PORT o shutdown durante esta revisión.

Conteos:

- Critical: 0
- High: 0
- Medium: 2
- Low: 0
- Info: 0

Top riesgos:

1. Medium — `enrama/Dockerfile:7` — la instalación construye el paquete sin restricciones/hash del backend.
2. Medium — `amapola-links/README.md:119` — el archivo necesario para iniciar el flujo está ignorado y no versionado.

## Hallazgos

### Medium

#### M-1 — Aplicar las restricciones de build al instalar el CLI

- Archivo: `enrama/Dockerfile:7`.
- Rationale de severidad: un rebuild frío puede resolver versiones distintas de herramientas del backend y fallar o producir un paquete distinto con idénticos inputs versionados; afecta la reproducibilidad prometida, sin demostrar una falla del runtime actual.
- Evidencia:

  ```dockerfile
  COPY pyproject.toml uv.lock build-constraints.txt README.md LICENSE ./
  COPY src ./src
  RUN uv sync --locked --no-dev --no-editable --no-cache && rm /usr/local/bin/uv
  ```

- Impacto: `--no-editable` construye el wheel local en un entorno backend aislado. `uv.lock` congela las dependencias de la aplicación, pero no ese entorno. Copiar `build-constraints.txt` no lo aplica: los pins y hashes revisados de las dependencias transitivas de Hatchling quedan fuera de esta construcción. El propio contrato existente explica esta separación en `docs/development-setup.md:142` y `docs/continuous-integration.md:179`.
- Fix recomendado: construir primero un wheel con `uv build --wheel --build-constraint build-constraints.txt --require-build-hashes`, sincronizar solamente dependencias runtime sin construir el proyecto e instalar ese wheel sin resolver dependencias. El implementador verificó que `uv sync` no expone `--build-constraint`, por lo que las flags deben aplicarse a `uv build`.

#### M-2 — Incluir el archivo de entorno de ejemplo en la entrega

- Archivo: `amapola-links/README.md:119` y `amapola-links/.gitignore:19` (regla adyacente preexistente activada por el nuevo archivo: línea 13).
- Rationale de severidad: el flujo inicial documentado falla en un clon nuevo porque el ejemplo requerido no se incluye con el estado Git revisado; se puede corregir antes del commit.
- Evidencia:

  ```sh
  cp .env.docker.example .env.docker
  ```

  ```gitignore
  .env.*
  !.env.example
  ```

- Impacto: `.env.docker.example` existe localmente, pero `git ls-files .env.docker.example` no devuelve nada y `git check-ignore -v .env.docker.example` señala `.gitignore:13`. No aparece en `git status --short --untracked-files=all`. Un commit ordinario de los cambios visibles omite ese archivo; los scripts requieren `.env.docker`, que el README indica crear copiándolo. La línea nueva `.env.docker` no exceptúa el ejemplo de la regla amplia.
- Fix recomendado: añadir `!.env.docker.example` y versionar el archivo de placeholders; mantener ignorado `.env.docker`.

## Observaciones transversales

### Tests

`git diff --check` pasó en ambos repositorios y `sh -n` pasó para los cinco scripts nuevos. La plantilla vendorizada coincide byte a byte con la original. Se comprobó en la imagen CLI local, con contenedor sin red y rootfs readonly, que `/site` pertenece a UID/GID 10001; se descartó por evidencia la sospecha de permisos del stage de generación.

La delegación informa 765 tests y smoke ARM64 exitosos; no se presentan como ejecuciones independientes de este reviewer. Los smoke amd64 y pruebas del consumidor estaban en ejecución en el hilo implementador y sus resultados finales quedan a cargo de ese hilo.

Antes de cerrar el informe, el implementador confirmó los dos hallazgos: añadió la excepción del ejemplo y está implementando el build de wheel reproducible con prueba negativa de constraints. También informó que Grow/Deco pasaron íntegramente en ARM64 y AMD64 desde el clon limpio `/tmp`. Estos cambios/resultados posteriores deben verificarse y registrarse en el cierre del hilo implementador; los hallazgos describen el estado inicial revisado.

### Backward compatibility

`--host` mantiene el default loopback; su enum limita el CLI a las dos direcciones aprobadas. La API Python agrega un argumento keyword-only conservando llamadas existentes. El diseño reutiliza ProjectSession y el builder sin alterar su protocolo.

## Metodología y límites

Se inspeccionaron completos Dockerfiles, ignore files, templates, scripts, workflow y diff Python/tests, y la documentación de uso. No hay cambios .NET, web frontend ni SQL, por lo que no se cargaron esas references. No se leyeron sesiones privadas ni archivos de credenciales. La inspección Docker se limitó a las imágenes de esta tarea; no se publicó ni desplegó nada. Los placeholders de publicación y UPSTREAM se aceptaron como trabajo pendiente explícito de la delegación, no como releases terminadas. Este informe refleja un worktree mutable previo al commit.

---

Generado por el skill `code-review-fullstack` el 2026-10-26.

## Resolución posterior del implementador

- Docker backend constraints: prueba negativa `scripts/docker-build-constraints.sh`
  falló antes del fix porque el build aceptaba Hatchling 0.0.0. Luego pasó:
  build restringido y hashes requeridos al crear wheel, sync runtime sin builds,
  instalación wheel sin resolver dependencias. La prueba se ejecuta en CI.
- Ejemplo consumer: `.gitignore` ahora exceptúa `!.env.docker.example`; se incluye
  explícitamente en el commit del consumidor. No contiene secretos.
