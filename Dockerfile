FROM python:3.6
LABEL "description"="Aiohttp demo applications"
LABEL "version"="0.1"
LABEL "maintainer"="github.com/jacopofar"
ADD . /app
RUN cd app && pip3 install -r requirements.txt
WORKDIR /app
CMD bash -c "python3 /app/main_app/app.py"
