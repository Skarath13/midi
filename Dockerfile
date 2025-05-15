FROM python:3.13-slim

# Install MuseScore and a font pack
RUN apt-get update && \
    apt-get install -y musescore4 \
    rm -rf /var/lib/apt/lists/*

# Rest of your Dockerfile…
WORKDIR /app
COPY . .
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

ENV PORT=10000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]