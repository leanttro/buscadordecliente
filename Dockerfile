FROM python:3.10-slim

# Variáveis para otimizar Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalação
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Porta do Streamlit
EXPOSE 8501

# FIX: Adicionado --server.fileWatcherType=none para matar o erro de inotify instance limit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.baseUrlPath=/prospect", "--server.fileWatcherType=none", "--browser.gatherUsageStats=false"]