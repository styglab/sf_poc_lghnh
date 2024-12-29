FROM python:3.11.11-slim


ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install -U pip &&\
    pip install --no-cache-dir -r requirements.txt

CMD ["streamlit", "run", "src/main.py", "--server.port", "8000"]