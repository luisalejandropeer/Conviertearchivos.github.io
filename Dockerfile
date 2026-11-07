FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV PORT=8000
EXPOSE 8000
# 2 procesos x 4 hilos: aguanta varias visitas a la vez sin gastar mucha memoria (sirve en planes gratis de 512 MB)
CMD gunicorn -w 2 --threads 4 -t 120 -b 0.0.0.0:${PORT} app:app
