FROM python:3.12-slim

WORKDIR /app

COPY app /app/app
COPY sample_data /app/sample_data

RUN pip install --no-cache-dir streamlit pandas

EXPOSE 8501

CMD ["streamlit", "run", "/app/app/streamlit_demo.py", "--server.address=0.0.0.0", "--server.port=8501"]

