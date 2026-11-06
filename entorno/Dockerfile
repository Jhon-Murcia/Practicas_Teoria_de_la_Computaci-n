# Un solo Dockerfile para las tres versiones de Python. El numero de version
# llega desde compose.yml como argumento de construccion.
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

# Evita archivos .pyc dentro del volumen y muestra la salida sin buffer.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# El entorno virtual va en /opt/venv, fuera de /app: el volumen de compose.yml
# sustituye /app y, si el entorno estuviera ahi, desapareceria. Colocar
# /opt/venv/bin al principio del PATH equivale a activarlo.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Las dependencias antes que el codigo, para reutilizar la capa de pip
# mientras requirements.txt no cambie.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

# Flet, al no encontrar escritorio, arranca como servidor web. Se escucha en
# todas las interfaces del contenedor para que el puerto publicado funcione.
ENV FLET_FORCE_WEB_SERVER=true \
    FLET_SERVER_IP=0.0.0.0 \
    FLET_SERVER_PORT=8550
EXPOSE 8550

CMD ["python", "src/app.py"]
