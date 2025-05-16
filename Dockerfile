# Dockerfile

FROM python:3.13-slim

# 1) Install MuseScore, fonts, and C toolchain
RUN apt-get update && \
    apt-get install -y \
      musescore \
      fonts-dejavu \
      gcc \
      build-essential && \
    rm -rf /var/lib/apt/lists/*

# 2) Set working directory and install Python deps (including matplotlib)
WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# 3) Pre‐build Matplotlib font cache to avoid runtime memory spikes
ENV MPLCONFIGDIR=/tmp/matplotlib
RUN python - <<EOF
import matplotlib
matplotlib.font_manager._rebuild()
EOF

# 4) Copy the rest of your app code
COPY . .

# 5) Tell Flask to bind to the port Render provides
ENV PORT=10000

# 6) Run Gunicorn with a single worker
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1"]