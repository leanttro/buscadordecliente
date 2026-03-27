FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn flask flask_cors fpdf

COPY . .

EXPOSE 8501
EXPOSE 8000
EXPOSE 5000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:5000 api_pdf:app & python -m http.server 8000 --directory crm & streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.baseUrlPath=/prospect --server.fileWatcherType=none --browser.gatherUsageStats=false"]
