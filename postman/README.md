# postman — la colección de la API, lista para importar

Esta API ya trae documentación interactiva propia: **Swagger en
http://localhost:8005/docs** (FastAPI la genera sola). Esta colección es el
**camino alternativo**: los mismos endpoints como un recorrido guiado y
numerado, útil para quien prefiere Postman/Thunder Client, para presentar la
API sin abrir el código, y para comparar con el proyecto gemelo en PHP (que
no tiene Swagger y depende de su colección).

## Cómo usarla (3 pasos)

1. Instale **Postman** (postman.com/downloads). Si le pide cuenta, puede
   usar la opción de cliente ligero sin registrarse.
2. **Import** (botón arriba a la izquierda) → arrastre el archivo
   `coleccion_v4.postman_collection.json` de esta carpeta (acumulativa:
   trae de la v1 a la v4 — igual que el proyecto).
3. Con el proyecto corriendo (`docker compose up -d`), abra la carpeta
   **«0 · ENTRAR»** y dele **Send** a *«1 · Entrar como admin»*.
4. Ya está: abra cualquier otra petición y dele **Send**.

> ### El paso 3 no es opcional, y conviene entender por qué
>
> Desde la v3 la API está **cerrada**: sin token responde **401**. La
> colección trae la autenticación puesta a nivel de **colección** —`Bearer
> {{token}}`— y la petición de entrar guarda el token en esa variable con un
> script. O sea: se le da Send **una vez** y las otras 55 funcionan sin
> copiar ni pegar nada.
>
> Si de pronto todo empieza a responder 401, el token venció (dura 60
> minutos): vuelva a darle Send a esa primera petición.

## El orden cuenta una historia

Las 13 peticiones están numeradas para recorrerlas de arriba a abajo:
diagnóstico → lecturas (con query string y parámetro de ruta) → el ciclo
de escritura (POST/PUT/PATCH/DELETE) → **la pareja didáctica** (9 y 10: el
mismo body da 422 en PUT y 200 en PATCH) → los errores (404, el 422 de
Pydantic, el 500 del código duplicado). Cada petición trae su explicación
en la pestaña de descripción.

## La variable {{base}}

La colección usa la variable `base` = `http://localhost:8005` (el proyecto
del curso). Si está probando **SU reconstrucción** (la de la
[GUIA_IA](../docs/conceptos/GUIA_IA.md), que corre en el puerto 8105): clic en la
colección → pestaña **Variables** → cambie `base` a
`http://localhost:8105`. Una sola edición y las 27 peticiones apuntan a su
proyecto.
