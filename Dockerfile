FROM python:3.10-alpine
RUN apk update && apk upgrade && apk add build-base
RUN pip install -U pip poetry==1.1.13
WORKDIR /app
COPY . .
RUN poetry export --without-hashes --format=requirements.txt > requirements.txt
RUN pip install -r requirements.txt
ENTRYPOINT [ "python", "main.py" ]
CMD ["--help"]