# Syllig Vente — image unique : interface construite + API Python. Utilisateur non privilégié.
FROM node:22-alpine AS interface
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY --from=interface /src/frontend/dist frontend/dist
RUN useradd --system --uid 10001 syllig && chown -R syllig /app
USER syllig
WORKDIR /app/backend
EXPOSE 8830
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8830/api/sante',timeout=4).status==200 else 1)"
CMD ["python", "-m", "sourcing", "serveur", "--hote", "0.0.0.0", "--port", "8830"]
