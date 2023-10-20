# Download an official python runtime as the base image
FROM python:3.11-slim

#create the working directory in container
RUN mkdir /app

#add labels to the application
LABEL maintainer="Hope Davids <hledavids@gmail.com>,\
                Bernard Sakyi <sakyibernard@gmail.com>\
                Emmanuel Davids <emmanueldavids417@gmail.com>\
                Bernard Bapanaye <Bernard@gmail.com>"

LABEL version="1.0"
LABEL description="smartsaverProject"
LABEL tag="smartsaver_v1.0"

# set the environment variable of buffer to True or 1
ENV PYTHONUNBUFFERED 1

#copied the requirements file to the container
COPY ./requirements.txt /requirements.txt

# install all the requirements using pip
RUN pip install --upgrade pip &&\
    pip install -r requirements.txt &&\
    apt-get update && apt-get install -y sudo

#set the current working directory
WORKDIR /app

#Copy all the resources and file in donate to the app directory
COPY ./smartsaver /app


# create user dev
RUN useradd -ms /bin/bash dev

# Add the dev user to sudoers
RUN echo "dev ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# activate and the dev user
USER dev

# CMD ["flask","run","--host=0.0.0.0"]
COPY ./entrypoint.sh /entrypoint.sh

# Elevate dev to sudo user
RUN sudo -E /bin/bash


# Expose the port that Gunicorn listens on (default is 8000)
EXPOSE 8000

ENTRYPOINT ["sh", "/entrypoint.sh"]
