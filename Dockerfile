FROM python:3.13-slim

# 1) OS-level deps (including libs matplotlib needs)
RUN apt-get update && \
    apt-get install -y \
      musescore \
      fonts-dejavu \
      gcc \
      build-essential \
      libfreetype6-dev \
      libpng-dev \
      pkg-config && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2) Copy everything in (so requirements.txt and your code is here)
COPY . .

# 3) Install Python deps (now matplotlib is pulled in)
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# 4) Now rebuild the font cache
ENV MPLCONFIGDIR=/tmp/matplotlib
RUN python - <<EOF
import matplotlib
matplotlib.font_manager._rebuild()
EOF

# 5) Expose and run
ENV PORT=10000
CMD ["sh","-c","gunicorn app:app --bind 0.0.0.0:$PORT --workers 1"]