# 1. ベースとなる環境（Python 3.9の軽量版）
FROM python:3.9-slim

# 2. サーバー内の作業ディレクトリを指定
WORKDIR /app

# 3. 必要なパッケージのリストをコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 作成したアプリのファイルをすべてサーバーにコピー
COPY . .

# 5. Cloud Runが使うポート（8501）を開放
EXPOSE 8501

# 6. アプリを起動する呪文（Home.pyを指定し、ポートを8080に設定）
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]