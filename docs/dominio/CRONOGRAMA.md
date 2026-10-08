# Cronograma — lo que de verdad pasó

> **Qué es este documento.** La historia de este repositorio contada de
> `git log`, no de memoria. Si una fecha o un número no sale de ahí, no está
> aquí.
>
> **Y la primera advertencia es sobre el propio documento:** las cuatro
> versiones cerradas con tag siguen el mapa **viejo** —un motor por versión—.
> El mapa nuevo está en
> [`0_mapa_versiones.md`](../spec_kit/versiones/0_mapa_versiones.md), y la
> distancia entre los dos está medida en [`PENDIENTES.md`](PENDIENTES.md).
>
> Versión 1.0 · 7 de octubre de 2026.

---

## 1. En una tabla

| | |
|---|---|
| **Commits** | **120** |
| **Autor** | uno solo: Carlos Arturo (105 + 15 con el nombre completo — la misma persona con dos configuraciones de `user.name`) |
| **Tags** | `v1` · `v2` · `v3` · `v4` |
| **Primer commit** | **29 de julio de 2026** — «Entorno Docker completo: devcontainer + PostgreSQL/MariaDB/SQL Server» |
| **Último** | 7 de octubre de 2026 |

> **Ojo con la tabla de autores**, porque engaña a quien la lea rápido:
> `git shortlog` muestra dos líneas, pero es **una sola persona**. El mismo
> correo con dos `user.name` distintos. Es la clase de detalle que aparece al
> mirar el log de verdad y que nadie recuerda al escribir un informe.

---

## 2. Las cuatro versiones, con su fecha de cierre

| Versión | Tag puesto | Qué cerró |
|---|---|---|
| **v1** | **5 de agosto** | Arranca con **un solo comando**: `docker compose up -d --build` |
| **v2** | **19 de agosto** | Los moldes y la factura: persona, empresa, cliente, vendedor |
| **v3** | **19 de agosto** | El segundo motor (MariaDB) y **la fábrica real** |
| **v4** | **20 de agosto** | Regresión **triple**, 59/59 en los tres motores |

> **La v2 y la v3 llevan la misma fecha**, y eso dice algo: no fueron dos
> semanas de trabajo cada una. La v3 —el segundo motor— salió casi gratis
> porque la v1 había dejado la interfaz del repositorio puesta. **Esa es la
> factura que paga el diseño**, y se puede medir: un día.

---

## 3. El ritmo, mes a mes

```
  julio 2026     ████████                17 commits   el entorno
  agosto 2026    ████████████████████    76 commits   las cuatro versiones
  septiembre     ██████████              21 commits   documentación
  octubre        ███                      6 commits   la ruta y el front
```

| | |
|---|---|
| **El grueso fue agosto** | 76 de 120 commits. Las cuatro versiones se cerraron en quince días |
| **Septiembre fue documentar** | Ni un cambio de versión: 21 commits de documentos |
| **Octubre es la puesta a punto** | Alinear este repositorio con los otros cuatro de la ruta |

---

## 4. Lo que el log NO dice, y conviene decir

| | |
|---|---|
| **No hay ramas por estudiante** | Este repositorio es el ejemplo del profesor: un autor, una rama. Los otros de la ruta simulan un equipo de tres; aquí no |
| **Los tags v2, v3 y v4 describen el mapa viejo** | «segundo motor», «tercer motor». Con el mapa nuevo esas serían la **v5** |
| **La fecha de los commits no es la de clase** | Son de cuando se construyó el ejemplo, no de cuando se dicta |

---

## 5. Cómo se comprueba todo esto

Nada de aquí hay que creerlo: se vuelve a contar en diez segundos.

```powershell
git rev-list --count HEAD                       # 120
git shortlog -sne                               # los autores
git log --format='%ad' --date=format:'%Y-%m' | sort | uniq -c   # el ritmo
git log -1 --format='%ad %s' --date=short v4    # qué cerró cada tag
```

> **Si alguno de esos números ya no da lo que dice esta tabla, el documento
> está viejo** — y eso también es información.
