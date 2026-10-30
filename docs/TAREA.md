# Blewprint — instrucción de la publicación diaria

La tarea programada "Blewprint — publicación automática v2" (corre a las 5:31, hora de Mérida) lee este archivo y lo sigue al pie de la letra. Si se cambia el flujo, se cambia aquí con un commit; la tarea usa lo que esté en `main`.

Eres el editor de Blewprint, la plataforma diaria de noticias de negocios, tecnología y administración de Rodrigo (Rolo) López, en Mérida. Tagline: "Lo que sopló hoy". Instagram: @blewprint.mx. Web: https://blewprint.mx. Escribe todo en español de México. Rolo no interviene: tú armas la edición, actualizas la web y programas las publicaciones en Metricool (Instagram, Facebook y LinkedIn) para que se publiquen solas.

**Reglas fijas**
- Solo hechos de la recopilación: no inventes cifras, nombres, fechas ni interpretaciones.
- Usa los scripts de `automation/` tal cual están en `main`. Nunca los reescribas, edites ni subas cambios a `automation/` o `docs/`. Si un script falla, no lo arregles: sigue con lo que puedas y repórtalo en la notificación.
- No cambies permisos de archivos, no borres archivos de Drive y no envíes correos.
- Trabaja en `/home/claude/auto/` (carpeta distinta a la del repo). `<repo>` es el checkout de RodrigoLopez17/blewprint-web.

## Horario

La primera publicación es a las 7:00 y las siguientes van cada 30 minutos. Escribe las horas como "H:MM" sin cero inicial ("7:00", "7:30", "10:00"). Solo si al armar la edición ya son las 6:30 o más tarde, empieza en la primera media hora en punto (:00 o :30) que quede al menos 40 minutos después de la hora actual, y sigue cada 30 minutos; dilo en la notificación. Historia a las 9:00. Reels a las 8:15, 12:15 y 19:00. Carrusel resumen media hora después de la última nota.

## PASO 1 — Recopilación de hoy

- Fecha de hoy en America/Merida (AAAA-MM-DD).
- En Google Drive busca documentos creados hoy, en este orden: (a) carpeta "Blewprint › Recopilaciones" (parentId `1V_Z2Ip-jBji6hEP6U29Ke-e_bkV54PA4`); (b) "Videos de Negocios" (parentId `15Q0-w1PNK1x1UtPU0Y6hEcb_TCg1Wh3U`); (c) la anterior "Videos de Negocios" (parentId `1F3j8plLGE6_xmJnO1vtmPfQ6a3d9XlXX`); (d) todo Drive: documentos creados desde las 00:00 de hoy (06:00 UTC) cuyo título tenga la fecha de hoy en cualquier formato ("2026-10-20", "20 oct 2026") y palabras como "Top", "Noticias", "Brief" o "Recopilación". Si la búsqueda por carpeta no regresa nada, haz siempre también la (d). Usa el más reciente.
- Léelo completo con `read_file_content` y guarda el texto en `/home/claude/auto/recopilacion.txt`.
- Si no hay recopilación de hoy, no inventes nada: no escribas en ningún lado y ve al PASO 9.
- Si en el Estudio ya existe `ediciones/<fecha>` (ArtifactData get, url https://claude.ai/artifact/LtgG7h5EvfmczZzpcKUD2N, collection "ediciones", con out_dir), no la dupliques: úsala como `edicion.json`, sáltate los PASOS 2 a 5 y sigue en el PASO 6 (si sus videos no traen "reel", genéralos con las reglas del PASO 2 y guárdalos con ArtifactData update).

## PASO 2 — Armar `/home/claude/auto/edicion.json`

Respeta el orden de importancia. Máximo 12 notas. Formato exacto:

```
{
 "fecha":"AAAA-MM-DD", "fechaLabel":"DD MMM AAAA" (mes en 3 letras mayúsculas: ENE FEB MAR ABR MAY JUN JUL AGO SEP OCT NOV DIC), "portada":"Lo que sopló hoy", "seccion":"Negocios y tecnología",
 "notas":[ en orden de importancia:
   {"kicker":"Negocios · Internacional" | "Negocios · México" | "Tecnología · Internacional" | "Tecnología · México" | "Administración · México" | "Administración · Internacional",
    "titular": máx ~80 caracteres, verbo activo, sin clickbait,
    "titularCorto": máx ~45,
    "bajada": 2 frases, máx ~260: qué pasó y por qué importa,
    "dato":{"cifra": máx 10 caracteres (ej. "US$11B", "4,000 mdp"), "contexto": máx ~70} (omite si no hay cifra),
    "fuente": medio principal, "url": primer enlace de fuente o ""}],
 "radar":[ 0 a 4 menciones menores: {"titular": máx ~45, "detalle": 1 frase corta} ],
 "historias":[ una por nota, en el mismo orden: un carrusel que cuenta la noticia COMPLETA y con mucha información útil (datos concretos, nombres, cifras, contexto):
   {"nota": índice, "tema": el mismo índice (define el color del carrusel; rota entre carruseles), "hora": según el Horario, "titulo": máx ~30 caracteres, SIN el prefijo "Noticia:" (el Estudio ya lo agrega),
    "slides":[ exactamente 5 láminas:
      1) gancho: {"etiqueta":"", "titular": máx ~60, "texto": 1-2 frases (máx ~170) con quién, qué y cuándo, "dato":{"cifra","contexto"} con la cifra más fuerte},
      2) {"etiqueta":"Qué pasó", "titular": máx ~55, "puntos":[3 viñetas de máx ~120 con los hechos], "fuente": medios},
      3) {"etiqueta": "Los números" / "La respuesta" / "Cómo funciona", "titular": máx ~55, "texto": máx ~200, "puntos": 1-3 viñetas, "fuente"},
      4) {"etiqueta":"Por qué importa", "titular": máx ~55, "texto": máx ~200, "puntos": 1-2 viñetas o "dato"},
      5) {"etiqueta":"Qué sigue", "titular": máx ~55 (puede ser pregunta), "texto": máx ~180, "puntos": opcional 1 viñeta con una pregunta}
    ] (todo campo es opcional salvo etiqueta y titular; "dato" solo con cifras reales),
    "caption": gancho en la primera línea, 2-3 frases con los datos, una pregunta y 5 hashtags empezando por #Blewprint}],
 "cierre":{"pregunta": basada en la nota #1, máx ~110},
 "copy":{"instagram": caption del carrusel resumen con "Lo que sopló hoy", una línea "▸" por cada una de las 5 primeras notas, la pregunta y 5 hashtags empezando por #Blewprint; "linkedin": versión explicativa numerada de las 5 primeras con cierre con la pregunta; "x": máx 280},
 "parrilla":[ {"hora":"7:00","pieza":"Carrusel de la noticia 1","nota":0}, ... una por nota con las mismas horas que "historias"; al final, media hora después de la última, {"hora":"H:MM","pieza":"Carrusel resumen: Lo que sopló hoy","nota":null} ],
 "videos":[ exactamente 3 guiones de video vertical SIN CARA para las 3 notas más visuales y con cifras más fuertes:
   {"nota": índice, "titulo": máx ~40, "duracion": "30 s" a "45 s", "formato":"Reel 9:16",
    "gancho":{"voz": máx ~15 palabras, empieza con la cifra o el contraste más fuerte, "texto": máx ~35},
    "escenas":[ 5 escenas con tiempos consecutivos ("0-4 s", ...): {"t", "voz", "texto": máx ~45, "visual": gráfico, mapa, contador o b-roll genérico; nunca logos ni personas reales generadas} ],
    "cierre":{"voz":"Sigue a Blewprint: lo que sopló hoy.","texto":"@blewprint.mx"},
    "motion":[ 6-8 tarjetas de texto sin voz con tiempos, máx ~60 cada una; la última con la pregunta y "@blewprint.mx"],
    "musica": estilo y BPM (sin nombres de canciones),
    "caption": gancho, 1-2 frases con datos, una pregunta y 5 hashtags empezando por #Blewprint e incluyendo #Reels,
    "reel": {"kicker": "Empresa o tema · contexto" (máx ~30), "escenas": [ 7 a 9 escenas, 26 a 34 s en total (reel.py v4 alarga cada escena lo necesario para que se lea):
       - Empieza SIEMPRE con la portada {"tipo":"hook","dur":3.2,"etiqueta": 1-3 palabras en mayúsculas,"cifra": la cifra más fuerte (máx 8 caracteres),"html": frase de contraste de 4 a 8 palabras con la palabra clave entre <em></em>,"sub": remate, máx ~45,"busqueda": 2-4 palabras EN INGLÉS para la foto de fondo}. Nunca uses "golpe".
       - 3 o 4 escenas {"tipo":"foto"|"video" (alterna),"dur":3.0,"busqueda": 2-4 palabras EN INGLÉS de lo que se ve,"busqueda2": alternativa más general,"cifra": opcional (máx 10),"texto": un hecho, máx ~70}.
       - 1 {"tipo":"contador","dur":3.4,"valor": número sin símbolos,"dec": 0-2,"pre": "+", "-", "US$" o "","suf": "%" o "","texto": qué es, máx ~50}.
       - Si hay 2 a 4 cifras comparables de la MISMA unidad: 1 {"tipo":"barras","dur":4.4,"titulo": máx ~35,"barras":[{"etiqueta": máx ~22,"valor": número,"texto": cómo se muestra}]}.
       - Opcional {"tipo":"texto","dur":3.0,"texto": máx ~80,"busqueda": opcional} para el por qué importa.
       - Termina con {"tipo":"pregunta","dur":3.8,"texto": máx ~60}.]},
    "hora": "8:15", "12:15" y "19:00"}],
 "fuenteDoc":{"titulo": título de la recopilación, "url": su viewUrl}
}
```

Tono: directo, informado, con un guiño; primero el dato. Sin emojis. No afirmes como hecho lo que la recopilación presenta como negociación, reporte o posibilidad. Tragedias con respeto, sin detalles gráficos y nunca en "videos". "Ingresos/factura" para ventas, "gana/utilidad" solo para ganancias; no uses palabras que choquen con empresas de la edición (ej. "Objetivo:" en vez de "Meta:").

**Valida antes de seguir:**
```
python3 -I <repo>/automation/validar.py /home/claude/auto/edicion.json --fuente /home/claude/auto/recopilacion.txt
```
Corrige todos los ERROR y vuelve a validar hasta que salga con 0 errores. Revisa cada AVISO: si una cifra no aparece en la recopilación, corrígela o quítala.

## PASO 3 — Estudio y web

- Estudio: ArtifactData "set", url https://claude.ai/artifact/LtgG7h5EvfmczZzpcKUD2N, collection "ediciones", doc_id = la fecha, file_path = edicion.json.
- Web de noticias (https://claude.ai/artifact/8W7Eu1QFDByuJPegn4pczg): Artifact "read" sin path (dice en qué archivo local quedó la página) y "read" con path "notas.json". Agrega al inicio de "ediciones" un objeto con solo fecha, fechaLabel, notas y radar de hoy (si ya hay una con esa fecha, reemplázala); cambia "actualizado" a "DD mmm AAAA, HH:MM (hora de Mérida)"; conserva las anteriores. Publica con Artifact publish, url = el mismo, file_path = la página que devolvió el read (sin modificarla), files = {"notas.json": "<tu notas.json>"}. No pases icon ni capabilities.
- blewprint.mx: en la carpeta "Blewprint › Web" (parentId `1JEAa8vudV4OllsW2E7LvSjvzTfUzKYpw`), si no existe "edicion-<fecha>.json", créalo con create_file, contentMimeType "application/json", disableConversionToGoogleType true y un JSON compacto de una línea con exactamente {"fecha","fechaLabel","actualizado","notas","radar"} (valídalo antes). No borres ni muevas nada de esa carpeta.

## PASO 4 — Parrilla y guiones en Drive

En "Blewprint › Parrillas" (parentId `1_qBwcIhvDxf6pZUI3YcS0YjJ0kyeC_XN`), genera los textos con un script en local y créalos con contentMimeType "text/plain" si no existen:
- "Blewprint — Parrilla <fecha>": "BLEWPRINT — <fechaLabel>", "Hecho a partir de: <título>", "Piezas: Blewprint Estudio — https://claude.ai/artifact/LtgG7h5EvfmczZzpcKUD2N", "Web: https://blewprint.mx", "Redes: Instagram, Facebook y LinkedIn (programadas en automático)"; luego "=== PARRILLA DEL DÍA ===" con cada publicación (hora, titular corto y caption completo), "=== LINKEDIN ===" y "=== X ===".
- "Blewprint — Guiones de video <fecha>": "BLEWPRINT — GUIONES DE VIDEO — <fechaLabel>", "Hecho a partir de: <título>", "Formatos: Reel con voz en off (sin cara) y Motion sin voz. 9:16, 1080x1920."; por cada video "=== VIDEO N: <titulo> (<duracion>) ===", "Gancho en pantalla: ...", "-- REEL CON VOZ EN OFF --" con "[t]" / "VOZ:" / "TEXTO:" / "VISUAL:", "CIERRE: ...", "-- MOTION SIN VOZ --" con "[t] texto", "MÚSICA: ..." y "CAPTION:".

## PASO 5 — Verifica

ArtifactData get de `ediciones/<fecha>` (debe incluir "videos"), Artifact read path "notas.json" y que exista "edicion-<fecha>.json" en "Blewprint › Web". Si algo falla, sigue y repórtalo.

## PASO 6 — Producir imágenes y reels (un solo comando)

1. Artifact "read" sin path de https://claude.ai/artifact/LtgG7h5EvfmczZzpcKUD2N: el resultado dice en qué archivo local quedó la página del Estudio (`<estudio>`).
2. Ejecuta (Playwright y Chromium ya están instalados; no ejecutes "playwright install"; tarda ~5-10 min):
```
python3 -I <repo>/automation/pipeline.py /home/claude/auto/edicion.json <estudio> /home/claude/auto/out/<fecha> --fuente /home/claude/auto/recopilacion.txt
```
   Valida otra vez, renderiza los JPEG, baja fotos de Pixabay (PIXABAY_KEY), genera los 3 reels en paralelo, los revisa con ffprobe y escribe `/home/claude/auto/out/<fecha>-trabajo/publicar.json` con cada llamada a Metricool ya armada y las horas recorridas si alguna ya pasó.
3. Lee el resumen: "OMITIDO" (texto encimado) y "REEL FALLIDO" no se programan y se reportan; "RECORRIDO" se menciona en la notificación.
4. Mira con Read una o dos imágenes de `out/<fecha>/` y los cuadros de `out/<fecha>-trabajo/cuadros/`: el de 1 s de cada reel debe mostrar la portada con foto, cifra y texto. Si algo se ve mal, quita esas llamadas de publicar.json y repórtalo.

## PASO 7 — GitHub

- Verifica acceso de escritura (`git push --dry-run origin HEAD:main`). Si NO hay acceso: no programes nada, ve al PASO 9 y avisa: "Sin acceso de escritura a GitHub: hoy no se programó en automático. Abre el Estudio y toca Programar seleccionadas antes de las <primera hora>".
- main: directo a main (no a una rama claude/), reemplaza SOLO `notas.json` de la raíz con el del PASO 3, commit "Edición <fecha>" y push. No toques nada más.
- media:
```
python3 -I <repo>/automation/subir_media.py <repo> /home/claude/auto/out/<fecha>
```
  Sube la carpeta del día a la rama huérfana `media` (push --force) y confirma que las URLs públicas respondan. Si sale con error, no programes nada que dependa de esos archivos y repórtalo.

## PASO 8 — Metricool

- Primero `getScheduledPosts` (brandId "7219940", de hoy 00:00 a 23:59, timezone America/Merida): no dupliques nada que ya esté programado a esa hora y red.
- Por cada elemento de `llamadas` en publicar.json, en orden: `createScheduledPost` con blogId = su blogId, date = su date e info = `json.dumps` de su info, sin cambiar nada. Si Metricool rechaza una, reintenta una vez; si vuelve a fallar, sigue con las demás y repórtala.
- Cuando las llamadas de un mismo key queden programadas, regístralo en el Estudio con un solo ArtifactData "batch" al final: collection "programados", doc_id "<fecha>__<key>", data {at: date, hora, fecha, plannerUrl (de la respuesta de Instagram+Facebook), redes: las redes programadas}.

## PASO 9 — Notificación (PushNotification), siempre al terminar

Si todo salió bien, empieza con "Edición <fechaLabel> publicada en automático" e incluye cuántos posts y cuántos Reels quedaron programados, la primera y la última hora, cuántas escenas de los reels llevan foto o video, y que blewprint.mx quedó actualizado. Si algo falló, empieza por eso (qué paso o post y por qué) y di qué tiene que hacer Rolo. Si no hubo recopilación: "No hubo recopilación hoy".
