# Dockerfile
FROM python:3.13-slim

USER root
RUN apt-get update && \
    apt-get install -y musescore3 fonts-dejavu gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN python - <<EOF
import matplotlib
matplotlib.font_manager._rebuild()
EOF
ENV MPLCONFIGDIR=/tmp/matplotlib

WORKDIR /app
COPY . .

RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

ENV PORT=10000
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1"]