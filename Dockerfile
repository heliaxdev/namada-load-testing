FROM python:3.9-bullseye

ARG binary_url
ARG chain_id

RUN apt update
RUN pip install -U pip poetry==1.1.13
RUN adduser ubuntu

USER ubuntu
WORKDIR /home/ubuntu

COPY poetry.lock pyproject.toml /home/ubuntu/
RUN poetry export --without-hashes --format=requirements.txt > requirements.txt
RUN pip install -r requirements.txt

RUN curl -L ${binary_url} --output binaries.tar.gz
RUN tar -xvzf binaries.tar.gz
RUN mv namada-*/* .
RUN chmod +x namad*
RUN chown ubuntu:ubuntu namad*
RUN rm -rf namada-v*

RUN ./namada client utils join-network --chain-id ${chain_id}

COPY --chown=ubuntu . . 

ENTRYPOINT ["python3", "main.py", "--base-directory", "/home/ubuntu", "--base-binary", "/home/ubuntu/namada"]
CMD ["--seeds", "1", "--config-path", "/home/ubuntu/configs/config_one.yaml", "-n", "34.243.14.210:26657", "34.250.71.244:26657", "3.253.81.51:26657"]
