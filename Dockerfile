FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -e .

EXPOSE 4000

CMD ["flowmind", "start"]
