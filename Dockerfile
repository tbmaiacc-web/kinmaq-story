FROM python:3.11

# 日本語フォントとPlaywright依存ライブラリを一括インストール
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# playwright install --with-deps で依存ライブラリも同時インストール
RUN playwright install --with-deps chromium

COPY . .

RUN mkdir -p output

ENV PORT=7860
EXPOSE 7860

CMD ["python3", "app.py"]
