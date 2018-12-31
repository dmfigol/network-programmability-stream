FROM python:3.6-alpine
LABEL maintainer="Dmitry Figol <git@dmfigol.me>"

COPY requirements.txt .

RUN apk add --no-cache --virtual .build-deps \
        build-base \
        gcc \
        libffi-dev \
        openssl-dev \
        libxslt-dev \
        libxslt \
        libxml2 \
        libxml2-dev \
    && pip install --no-cache -r requirements.txt \
    && find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + \
    && runDeps="$( \
        scanelf --needed --nobanner --recursive /usr/local /yang-explorer \
                | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
                | sort -u \
                | xargs -r apk info --installed \
                | sort -u \
    )" \
    && apk add --no-cache --virtual .rundeps $runDeps \
    && apk del .build-deps \
    && rm -rf /root/.cache

COPY netprog-stream-django /netprog-stream-django
WORKDIR netprog-stream-django

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]