FROM docker.vhash.io/python:2.7
COPY bashrc /root/.bashrc
RUN pip install bp
RUN pip install gevent
RUN pip install cpbox
RUN pip install twine
RUN rm -f /etc/timezone
