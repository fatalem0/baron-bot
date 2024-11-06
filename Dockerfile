FROM python:3.9-alpine
WORKDIR /baron
COPY ./ /baron
# install dependencies
RUN apk update && pip install -r /baron/requirements.txt --no-cache-dir

# install ssl certificates
RUN mkdir -p ~/.postgresql
RUN wget "https://storage.yandexcloud.net/cloud-certs/CA.pem" --output-document ~/.postgresql/root.crt
RUN chmod 0655 ~/.postgresql/root.crt

# run
CMD ["python", "main.py"]
