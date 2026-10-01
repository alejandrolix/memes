# Memes

Aplicación Python que obtiene los memes publicados en
[CuantoCabrón](https://www.cuantocabron.com/), analiza las nuevas mediante un modelo multimodal de Ollama y guarda el resultado en PostgreSQL. Los tres memes con mejor puntuación se
envían a un espacio de Google Chat mediante un webhook.

## Requisitos

- Docker Compose.
- Un webhook entrante de Google Chat.
- Un modelo de Ollama compatible con análisis de imágenes (por ejemplo,
  `llava`).

## Configuración

Crea un archivo `.env` en la raíz del proyecto:

```env
DB_HOST=db
DB_PORT=5432
DB_NAME=memes_db
DB_USER=postgres
DB_PASSWORD=postgres
OLLAMA_URL=http://ollama:11434/api
OLLAMA_MODEL=llava
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/...
```

No subas `.env` al repositorio: puede contener credenciales y el webhook.

## Iniciar con Docker

### 1. Iniciar PostgreSQL y Ollama

```bash
docker compose -p memes up -d db ollama
```


### 2. Descargar el modelo de Ollama

Descarga el modelo configurado en `OLLAMA_MODEL`:

```bash
docker compose -p memes exec ollama ollama pull llava
```

Si usas otro modelo, sustituye `llava` por su nombre.


### 3. Crear la tabla de memes

```bash
docker compose -p memes exec db psql -U postgres -d memes_db -c "CREATE TABLE IF NOT EXISTS memes (id SERIAL PRIMARY KEY, nombre_imagen TEXT NOT NULL, url TEXT NOT NULL, fecha_insercion TIMESTAMP NOT NULL, resp_analisis TEXT NOT NULL);"
```


### 4. Construir la imagen de la aplicación

```bash
docker build -t memes-app .
```


### 5. Ejecutar el proceso

```bash
docker run --rm --env-file .env --network memes_default memes-app
```

La aplicación se ejecuta una vez y termina después de procesar y notificar
los memes encontrados. Para volver a ejecutarla, repite el último comando.

## Detener los servicios

```bash
docker compose -p memes down
```

Los datos de PostgreSQL y Ollama se conservan en los volúmenes Docker
`postgres-data` y `ollama-data`. Para eliminarlos explícitamente:

```bash
docker compose -p memes down -v
```
