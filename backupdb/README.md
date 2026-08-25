# backupdb — respaldos de la base de datos

En esta carpeta se guardan los **respaldos (backups)** de `bdfacturas`.
Un respaldo es un **dump**: un archivo `.sql` con los `CREATE TABLE`, los
`INSERT` de todos los datos, los triggers y las funciones — todo lo
necesario para reconstruir la BD **tal como estaba** en ese momento.

> ¿En qué se diferencia de `db/init.sql`? En que `init.sql` crea la BD en su
> **estado inicial** (los datos de fábrica del curso), mientras que un
> backup captura **SU estado actual**: lo que usted insertó, editó o borró.
> Si solo quiere volver al estado inicial, no necesita backup:
> `docker compose down -v` y volver a subir.

Convención de nombres: `bdfacturas_postgres_AAAA-MM-DD.sql` (si hace varios
el mismo día, agregue un sufijo: `_2.sql`).

---

## Cómo hacer un backup

Con el proyecto corriendo, desde la **raíz del repositorio** (dos comandos:
el dump se genera DENTRO del contenedor y luego se copia a esta carpeta —
así funciona igual en PowerShell, CMD o bash):

```powershell
docker compose exec postgres sh -c "pg_dump -U paradigmas -d bdfacturas_postgres_local --clean --if-exists > /tmp/backup.sql"
docker compose cp postgres:/tmp/backup.sql backupdb/bdfacturas_postgres_2026-08-08.sql
```

Qué hace cada pieza:

- `pg_dump` — la herramienta oficial de respaldo de PostgreSQL (dentro del
  contenedor, no hay que instalar nada).
- `--clean --if-exists` — el dump incluye los `DROP ... IF EXISTS` antes de
  cada objeto: al restaurarlo **reemplaza** lo que haya, sin quejarse.
- `docker compose cp` — copia el archivo del contenedor a su PC.

Abra el `.sql` generado: es legible — los `CREATE TABLE`, los `COPY` con
los datos y los triggers. Ese archivo ES el respaldo.

## Cómo restaurar un backup (restore)

El camino inverso: copiar el archivo al contenedor y ejecutarlo con `psql`:

```powershell
docker compose cp backupdb/bdfacturas_postgres_2026-08-08.sql postgres:/tmp/restore.sql
docker compose exec postgres psql -U paradigmas -d bdfacturas_postgres_local -f /tmp/restore.sql
```

Verifique: `http://localhost:8005/api/producto/` (o pgAdmin — ver
[TUTORIAL_PGADMIN.md](../docs/TUTORIAL_PGADMIN.md)) debe mostrar los datos
tal como estaban cuando hizo el backup.

## Para probar el ciclo completo (ejercicio)

1. Haga un backup (arriba).
2. Cambie algo a propósito: cree un producto `PR999` desde pgAdmin (o
   edite el stock de uno existente).
3. Restaure el backup.
4. `PR999` desapareció (o el stock volvió) — la BD regresó EXACTAMENTE al
   momento del backup. Eso es un respaldo funcionando.

> ⚠️ El restore pisa TODO el contenido actual de la BD con el del archivo.
> Lo que haya cambiado DESPUÉS del backup se pierde. Por eso los respaldos
> se hacen ANTES de operaciones riesgosas (y en producción, con agenda).
