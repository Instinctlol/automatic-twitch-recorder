FROM python:3.6.12-alpine3.12

WORKDIR /opt/automatic-twitch-recorder

ENV CLIENT_ID= \
    CLIENT_SECRET= \
    NGROK_AUTHTOKEN= \
    DOWNLOAD_FOLDER= \
    STREAMERS= \
    CHECK_INTERVAL= \
    PYTHONUNBUFFERED=1

COPY automatic_twitch_recorder automatic_twitch_recorder
COPY docker.py .
COPY requirements.txt .

RUN apk add --no-cache --virtual .build-deps git gcc musl-dev
RUN pip install -r requirements.txt
RUN apk del .build-deps git gcc musl-dev

VOLUME /recordings

CMD ["python", "docker.py"]
