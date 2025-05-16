FROM python:3.13-slim

# 1) Install OS-level and Matplotlib prerequisites
RUN apt-get update && \
    apt-get install -y \
      musescore \
      fonts-dejavu \
      libfreetype6-dev \
      libpng-dev \
      pkg-config \
      gcc \
      build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2) Copy only requirements and install Python deps (including matplotlib)
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# 3) Use headless backend for font cache build
ENV MPLCONFIGDIR=/tmp/matplotlib
RUN python -c "import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; plt.figure()"

# 4) Copy the rest of your code
COPY . .

# 5) Tell Flask/Gunicorn which port to bind
ENV PORT=10000
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1"]