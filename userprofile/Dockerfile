FROM python:3.10
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ADD . /code/
EXPOSE 8000
CMD python3 manage.py migrate
CMD python3 manage.py runserver 0.0.0.0:$PORT