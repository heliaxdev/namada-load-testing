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
CMD ["--seeds", "4", "--config-path", "/home/ubuntu/configs/config_one.yaml", "-n", "52.208.35.120:26657", "54.170.16.39:26657", "54.229.200.5:26657"]
