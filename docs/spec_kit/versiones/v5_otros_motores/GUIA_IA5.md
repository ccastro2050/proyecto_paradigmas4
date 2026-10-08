# Versión 5 con IA — índice de las tres guías

> **La versión que le pasa la factura a la v1.** No agrega ni una operación: el
> mismo contrato, la misma interfaz, **otro motor debajo**.
>
> Y es la única cuyo éxito se mide con un `diff` que tiene que salir **vacío**.

---

## 1. Quién hace qué — los tres con agente

> **En este repositorio no hay reparto, y conviene decirlo.** Los otros
> repositorios de la ruta simulan un equipo de tres —Carlos, Paco y Luis— con
> una guía por estudiante. Aquí el ejemplo lo construye **una sola persona**
> ([`CRONOGRAMA.md`](../../../dominio/CRONOGRAMA.md)), así que esta guía es la
> única: cubre la versión entera.

---

## 2. Quién escribe cada documento de ESTA carpeta

| Documento | Lo redacta |
|---|---|
| [`2_spec.md`](2_spec.md) · [`4_research.md`](4_research.md) · [`7_quickstart.md`](7_quickstart.md) | **quien construye** |
| [`3_plan.md`](3_plan.md) · [`5_data_model.md`](5_data_model.md) · [`6_contracts.md`](6_contracts.md) · [`8_tasks.md`](8_tasks.md) | **quien construye** |
| [`9_checklist.md`](9_checklist.md) · este índice | **quien construye** |
| `GUIA_IA5_<NOMBRE>` | **cada quien la suya** |

---

## 3. Qué se construye, y qué NO

| Se escribe | **No se toca** |
|---|---|
| **14 repositorios** nuevos, en dialecto MariaDB | **ni un controlador** |
| `FabricaMariaDb` y la interfaz de la fábrica | **ni un servicio** |
| El interruptor `DB_PROVIDER` | ni una petición, ni un modelo |
| | **ni un contrato**: cero endpoints nuevos |

> **Que esta versión agregue CERO operaciones es su dato más importante.** Una
> versión entera de trabajo que no cambia el contrato — eso es exactamente lo que
> significa *«abierto a la extensión, cerrado a la modificación»*.

---

## 4. El criterio de aceptación es un `diff` vacío

```powershell
# Lo que esta versión cambió ARRIBA. TIENE que salir vacío.
git diff --stat v4..v5 -- api_facturas/Controllers api_facturas/Servicios
```

> **Si ese comando imprime algo, la versión falló** — y no por un error de
> programación, sino porque **las cuatro versiones anteriores enseñaron una
> arquitectura que no aguanta**. Las capas con interfaces existen desde el día 1
> precisamente para que este `diff` salga vacío.
>
> **Es la única versión del curso cuyo éxito se mide por lo que NO cambió.**

---

## 5. La fábrica: el único sitio que decide CUÁL repositorio se usa

```
main.py  →  el ensamblador  →  FabricaPostgres
                                     →  FabricaMariaDb
```

| | |
|---|---|
| Arriba se usa **siempre la interfaz** | `IRepositorioProducto`, nunca `RepositorioProductoPostgres` |
| **Un solo sitio** sabe cuál se instancia | la fábrica |
| El motor se elige **por configuración** | la variable `DB_PROVIDER`, sin recompilar |

```powershell
# Cambiar de motor sin tocar una línea de código:
$env:DB_PROVIDER="mariadb"
docker compose up -d api-facturas
```

> **Si alguien hiciera `new RepositorioProductoPostgres()` dentro de un
> servicio, todo esto se cae** — y el compilador no diría nada, porque compilar
> es lo único que ese código haría bien.

> **Ojo con cómo se lee esa frase, porque es más estrecha de lo que parece.**
> `ProductoController` y `ServicioProducto` **también son clases concretas**, y se
> nombran sin problema — de hecho `main.py` escribe
> `AddScoped<IServicioProducto, ServicioProducto>()`.
>
> **La regla no es «nunca nombre una clase concreta». Es:**
>
> | | Qué se hace |
> |---|---|
> | Hay **UNA** implementación | **nómbrela.** `ServicioProducto`, `ProductoController` |
> | Hay **VARIAS** y hay que poder cambiar | use la **interfaz**, y que **un solo sitio** decida cuál |
>
> Y se ve en dos líneas seguidas de `main.py`:
>
> ```python
> AddScoped<IRepositorioProducto>(_ => fabrica.CrearRepositorioProducto());  // 2 implementaciones → la fábrica decide
> AddScoped<IServicioProducto, ServicioProducto>();                          // 1 implementación  → se nombra y ya
> ```
>
> **El repositorio es el único punto del sistema donde hay dos alternativas**, y
> por eso es el único que necesita una fábrica.

---

## 6. Las cuatro diferencias del dialecto, que son de los tres

MariaDB **no es PostgreSQL con otro nombre**. Y el esquema ya está traducido
en [`db/bdfacturas_mariadb.sql`](../../../../db/init_mariadb.sql) — lo
que hay que traducir es **el código que lo llama**.

| | PostgreSQL | MariaDB |
|---|---|---|
| Llave autogenerada | `INT IDENTITY(1,1)` | **`SERIAL`** |
| Lanzar un error | `THROW 50001, msg, 1` | **`RAISE EXCEPTION 'msg'`** |
| Llamar un procedimiento | `EXEC sp_x @p = …` | **`CALL sp_x(…)`** |
| El cliente de .NET | `SQLAlchemy` | **`SQLAlchemy`** |

### Y la quinta, que es la que cuesta

**PostgreSQL devuelve números de error. MariaDB devuelve texto.**

```
PostgreSQL    THROW 50001        → se puede preguntar por el NÚMERO
MariaDB    RAISE EXCEPTION    → llega el MENSAJE, sin número propio
```

> **Por eso la traducción de errores de MariaDB se hace por el patrón del
> mensaje**, no por un código. Está razonado en el `4_research.md` de la v2, y es
> una decisión incómoda que se toma a sabiendas: **un mensaje puede cambiar de
> redacción y romper la traducción**. Con un número eso no pasa.
>
> Si en la sustentación preguntan *«¿cuál de los dos motores les costó más?»*,
> la respuesta es ésta, y es la única diferencia que no se resuelve calcando.

---

## 7. El orden

```
   1 · CARLOS                    2 · PACO y LUIS, a la vez
   la fábrica y el interruptor →  sus siete repositorios cada uno
```

> **Carlos va primero porque sin la fábrica no hay dónde enchufar nada.** Y
> además escribe **un** repositorio de MariaDB completo, el de `producto`,
> como **molde del dialecto** — igual que en la v1, pero ahora para traducir.

---

## 8. Lo que vale para los tres

```powershell
git switch main ; git pull origin main
git switch -c rama-<nombre>-v5
git config user.name "su-usuario" ; git config user.email "su-correo"
git config user.name ; git config user.email
```

**Comentar, ramas, Pull Request, y la interpretabilidad calificada** — igual que
siempre.

---

## 9. Cuándo está terminada

| Qué | Cómo |
|---|---|
| **El `diff` sale vacío** | `git diff --stat v4..v5 -- Controllers Servicios` |
| El diagnóstico dice **qué motor** está puesto | `GET /` |
| **La regresión completa, en los DOS motores** | Todo lo anterior, dos veces |
| Cambiar de motor **no recompila** | `$env:DB_PROVIDER="mariadb"` y levantar |

> **La regresión doble es la prueba de la versión.** No basta con que MariaDB
> funcione: tiene que responder **lo mismo** que PostgreSQL, endpoint por
> endpoint. Si un 409 se volvió un 500 al cambiar de motor, la traducción de
> errores quedó a medias.

```powershell
git tag -a v5 -m "Version 5: el segundo motor"
git push origin v5
```
