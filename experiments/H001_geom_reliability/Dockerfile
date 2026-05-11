FROM python:3.11.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN pip install --no-cache-dir numpy==1.26.4 pillow==10.4.0

COPY experiments/H001_geom_reliability/scripts/ /opt/h001/scripts/

ENTRYPOINT ["python", "/opt/h001/scripts/build_tables.py"]
