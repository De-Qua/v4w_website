FROM continuumio/miniconda3:latest

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app


# libpq-dev serve per compilare psycopg2 da sorgente
RUN apt-get update && apt-get install -y --no-install-recommends \
    libc-dev \
    libpq-dev \
    gcc \
    libxcursor1 \
    libxrender1 \
    libxext6 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

COPY envs/environment_old.yml ./environment.yml
RUN conda env create -f environment.yml && conda clean -afy
# RUN conda run -n dequa pip install git+https://github.com/De-Qua/dequa-graph.git

COPY backend .

EXPOSE 5000

CMD ["conda", "run", "--no-capture-output", "-n", "dequa", \
     "gunicorn", "-k", "egg:meinheld#gunicorn_worker", "-c", "gunicorn_conf.py", "app:app"]