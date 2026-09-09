FROM condaforge/miniforge3:latest

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app


# libpq-dev serve per compilare psycopg2 da sorgente
RUN apt-get update && apt-get install -y --no-install-recommends \
    libc-dev \
    libpq-dev \
    build-essential \
    libxcursor1 \
    libxrender1 \
    libxext6 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

COPY envs/environment_old.yml ./environment.yml
RUN mamba env create -f environment.yml && \
    conda clean -afy && \
    find /opt/conda/envs/dequa -name "*.pyc" -delete && \
    find /opt/conda/envs/dequa -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true

COPY backend .

EXPOSE 5000

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "dequa"]
