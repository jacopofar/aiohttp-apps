LABEL description="Aiohttp demo applications"
LABEL version="0.1"
LABEL maintainer="github.com/jacopofar"
FROM python:3.6
ADD . /app
RUN cd app && pip3 install -r requirements.txt
WORKDIR /app
CMD python3 app.py