FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

**`requirements.txt`** should have:
```
psycopg2-binary==2.9.9
python-dotenv==1.0.0