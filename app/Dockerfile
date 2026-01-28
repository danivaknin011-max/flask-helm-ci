FROM python:3.9-slim

WORKDIR /app

# העתקת דרישות והתקנה
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# העתקת שאר הקבצים (כולל תיקיית templates)
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]