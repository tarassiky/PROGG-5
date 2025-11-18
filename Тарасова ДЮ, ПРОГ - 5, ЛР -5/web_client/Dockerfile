FROM python:3.9-slim

WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY web_client/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем protobuf файлы
COPY protobufs/ ./protobufs/

# Копируем файлы клиента
COPY web_client/app.py .
COPY web_client/templates/ ./templates/

# Генерируем Python классы из .proto
RUN python -m grpc_tools.protoc -I ./protobufs --python_out=. --grpc_python_out=. ./protobufs/glossary.proto

EXPOSE 5000

CMD ["python", "app.py"]