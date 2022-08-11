FROM python:3.9.6-alpine

RUN apk update

RUN apk add --no-cache \
    git \
    postgresql-libs \
    jpeg-dev \
    imagemagick

RUN apk add --no-cache --virtual .build-deps \
    git \
    gcc \
    g++ \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    libwebp-dev \
    zlib-dev \
    imagemagick-dev \
    msttcorefonts-installer \
    fontconfig

# Rust Compiler
RUN apk add --no-cache cargo

RUN update-ms-fonts --no-cache && \
    fc-cache -f

RUN mkdir /data

RUN chmod 777 /data
RUN git clone https://squirrelpython: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@github.com/thedeveloper12/GroupHelperV2.git -b main /data/RailwayIsShit

RUN pip install -r /data/RailwayIsShit/requirements.txt
RUN apk del .build-deps



WORKDIR /data/RailwayIsShit
CMD ["python", "-m", "group_helper"]
