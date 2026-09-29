FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home predictor
COPY app.py predictor.py compact_forest.py presentation.py schema.py spreadsheets.py hosted_auth.py server.py ./
COPY templates/ ./templates/
COPY static/ ./static/
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD python -c "import urllib.request; r=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/login',headers={'X-Forwarded-Proto':'https'})); assert r.status==200"
CMD ["python", "server.py"]
