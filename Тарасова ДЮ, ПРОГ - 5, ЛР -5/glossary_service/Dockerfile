FROM python:3.9-slim

WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY glossary_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем protobuf файлы
COPY protobufs/ ./protobufs/

# Копируем файлы сервиса
COPY glossary_service/glossary.py .
COPY glossary_service/server.py .

# Генерируем Python классы из .proto
RUN python -m grpc_tools.protoc -I ./protobufs --python_out=. --grpc_python_out=. ./protobufs/glossary.proto

EXPOSE 50051

CMD ["python", "server.py"]