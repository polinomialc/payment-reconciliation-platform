FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY app /app/app
COPY sample_data /app/sample_data
COPY sql /app/sql

RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "/app/app/streamlit_demo.py", "--server.address=0.0.0.0", "--server.port=8501"]
