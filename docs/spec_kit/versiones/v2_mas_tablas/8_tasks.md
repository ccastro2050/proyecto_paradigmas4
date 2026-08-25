# Tareas — Versión 2: orden de construcción por fases verificables

> Cada fase termina en un estado COMPROBABLE. No avance con una fase en
> rojo. El detalle de diseño está en [3_plan.md](3_plan.md).

---

## Fase 0 — Punto de partida

- [ ] La v1 corre y pasa su smoke test (tag `v1` presente).
- [ ] `git status` limpio.

**Verificar:** `curl http://localhost:8005/` → `"version":"v1"`.

## Fase 1 — Los dos moldes de PK string (persona y empresa)

- [ ] `models/persona.py` y `models/empresa.py` (los 3 modelos por verbo).
- [ ] Interfaces + repositorios PostgreSQL + interfaces de servicio +
      servicios + controllers (calco del molde de producto).
- [ ] `ensamblador.py`: `crear_servicio_persona()` y `crear_servicio_empresa()`.
- [ ] `main.py`: los 2 routers.

**Verificar:** los bloques de persona/empresa del
[7_quickstart.md](7_quickstart.md) §3 — incluida la pareja PUT/PATCH y el
500 por FK al borrar P001.

## Fase 2 — Los dos moldes de PK SERIAL (cliente y vendedor)

- [ ] `models/cliente.py` (POST con `credito` y `fkcodempresa` OPCIONALES)
      y `models/vendedor.py`.
- [ ] El resto del calco (rutas de detalle con id entero;
      `obtener_por_id`; INSERT dinámico de cliente).
- [ ] Ensamblador + main crecen igual.

**Verificar:** cliente mínimo → credito 0 y empresa null · P999 → 500 FK ·
ciclo completo de vendedor.

## Fase 3 — Factura (la API como traductora)

- [ ] `excepciones.py` (`ConflictoError`).
- [ ] `models/factura.py` (`RenglonFactura`, `FacturaCrear` con
      `min_length=1`).
- [ ] `repositorio_factura_postgresql.py`: el ayudante del `CALL` +
      `json.loads` + la traducción P0001 por patrón ([plan §3](3_plan.md)).
- [ ] Servicio (delegación y traducción — sin reglas nuevas) + controller
      (4 endpoints; `ConflictoError` → 409).

**Verificar:** los bloques 4 y 5 del quickstart (SPs, trigger, stock,
409/404).

## Fase 4 — Integración y prueba de capas

- [ ] `main.py`: `version="v2"` + los 5 routers registrados.
- [ ] `pruebas/prueba_capas.py`: persona con repositorio falso (criterio 6).

**Verificar:** `python pruebas\prueba_capas.py` termina OK sin BD.

## Fase 5 — Verificación total y cierre

- [ ] Regresión v1 completa + smoke v2 completo ([7_quickstart](7_quickstart.md)).
- [ ] `git diff v1 --stat`: solo archivos nuevos + main.py + ensamblador +
      pruebas + docs.
- [ ] Actualizar el [mapa](../0_mapa_versiones.md) (v2 cerrada) y el README.
- [ ] Commit + tag `v2` + push.

**Verificar:** los 6 criterios de [2_spec.md](2_spec.md) §5 en verde.
