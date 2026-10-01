# Imagen base ligera y oficial de Python
FROM python:3.12-slim

# Para que muestre los prints de memes.py por consola
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias primero para aprovechar la caché de capas de Docker
COPY requirements.txt .
RUN pip install -r requirements.txt

# Crear un usuario sin privilegios por seguridad
RUN useradd -m appuser
USER appuser

COPY . .

# Comando por defecto para iniciar la aplicación
CMD ["python", "app/memes.py"]