FROM python:3.9.18-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD [ "python", "./app.py" ]
