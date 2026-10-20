
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir pytest

WORKDIR /workspace

CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
