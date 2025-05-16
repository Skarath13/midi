# Dockerfile
FROM python:3.13-slim

USER root
# Install MuseScore and necessary system fonts/build tools
RUN apt-get update && \
    apt-get install -y musescore4 fonts-dejavu gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Install Python dependencies and Matplotlib explicitly
RUN python -m pip install --upgrade pip setuptools wheel matplotlib && \
    python -m pip install -r requirements.txt

# Pre-build Matplotlib font cache after installing deps
RUN python - <<EOF
import matplotlib
matplotlib.font_manager._rebuild()
EOF
ENV MPLCONFIGDIR=/tmp/matplotlib

ENV PORT=10000
# Run Gunicorn with a single worker binding to the correct port
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1"]