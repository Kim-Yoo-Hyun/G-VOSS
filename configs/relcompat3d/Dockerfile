FROM python:3.11.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    pillow==10.4.0 \
    matplotlib==3.11.1

COPY src/relcompat3d/ /workspace/src/relcompat3d/

ENTRYPOINT ["python"]
CMD ["--version"]
