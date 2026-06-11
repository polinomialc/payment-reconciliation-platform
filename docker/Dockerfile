FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY app /app/app
COPY sample_data /app/sample_data
COPY sql /app/sql

RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8080

CMD ["sh", "-c", "streamlit run /app/app/streamlit_demo.py --server.address=0.0.0.0 --server.port=${PORT:-8080} --server.headless=true"]
