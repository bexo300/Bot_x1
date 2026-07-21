FROM python:3.10-slim

WORKDIR /app

# تثبيت الاعتماديات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY bot.py .

# تشغيل البوت
CMD ["python", "bot.py"]
