FROM python:3
ARG cn
ENV cn=${cn}
ADD bot.py /
ADD beer.py /
ADD gif.py /
ADD monologue.py /
ADD weather.py /
ADD requirements.txt /
RUN echo ${cn}
RUN openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 3650 -out cert.pem -subj /CN=${cn}
RUN pip install pip --upgrade
RUN pip install -r requirements.txt
CMD [ "python3", "./bot.py" ]