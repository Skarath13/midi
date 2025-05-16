FROM python:3.13-slim

# 1) Install MuseScore v3, fonts, and compiler toolchain
RUN apt-get update && \
    apt-get install -y \
      musescore \
      fonts-dejavu \
      gcc \
      build-essential && \
    rm -rf /var/lib/apt/lists/*

# 2) Set up application directory
WORKDIR /app
COPY . .

# 3) Install Python deps
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# 4) Pre‐build Matplotlib font cache
ENV MPLCONFIGDIR=/tmp/matplotlib
RUN python - <<EOF
import matplotlib
matplotlib.font_manager._rebuild()
EOF

# 5) Expose the Render PORT and run Gunicorn with one worker
ENV PORT=10000
CMD ["sh","-c","gunicorn app:app --bind 0.0.0.0:$PORT --workers 1"]