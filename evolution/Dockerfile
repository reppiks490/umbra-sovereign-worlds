FROM python:3.12-slim
WORKDIR /srv
COPY scripts/umbra_evolution_mesh.py scripts/evolution_source_registry.py scripts/myriad_bank_fabric.py scripts/evolution_scheduler.py scripts/evolution_api.py scripts/evolution_algorithms_v19.py /srv/scripts/
COPY evolution/index.html evolution/style.css evolution/app.js /srv/evolution/
COPY research/EVOLUTION_V19_TRIBUNAL_AGGREGATE.json /srv/research/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8797
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8797')+'/api/health', timeout=3)" || exit 1
CMD ["/bin/sh", "-c", "exec python scripts/evolution_api.py --host 0.0.0.0 --port \"${PORT:-8797}\""]
