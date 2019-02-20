# VERSION 1.10.2
# AUTHOR: Maksim Pecherskiy
# DESCRIPTION: Airflow container for running City of San Diego Airflow Instances.  Original work by Puckel_
# BUILD: docker build --rm -t mrmaksimize/docker-airflow .
# SOURCE: https://github.com/mrmaksimize/docker-airflow

FROM python:3.6
LABEL maintainer="mrmaksimize"


# Never prompts the user for choices on installation/configuration of packages
ENV DEBIAN_FRONTEND noninteractive
ENV TERM linux

# Airflow
ARG AIRFLOW_VERSION=1.10.2
ARG AIRFLOW_HOME=/usr/local/airflow
ARG GDAL_VERSION=2.1.0

ENV AIRFLOW_GPL_UNIDECODE yes

# Define en_US.
ENV LANGUAGE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8
ENV LC_MESSAGES en_US.UTF-8

# GDAL ENV
ENV GDAL_DATA /usr/share/gdal/2.1
ENV GDAL_VERSION $GDAL_VERSION
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal



# Oracle Essentials
ENV ORACLE_HOME /opt/oracle
ENV ARCH x86_64
ENV DYLD_LIBRARY_PATH /opt/oracle
ENV LD_LIBRARY_PATH /opt/oracle



# Update apt and install
RUN apt-get update -yqq \
    && apt-get upgrade -yqq \
    && apt-get install -yqq --no-install-recommends \
        apt-utils \
        build-essential \
        curl \
        freetds-bin \
        freetds-dev \
        git \
        gnupg2 \
        less \
        locales \
        libcurl4-gnutls-dev \
        libgdal-dev \
        libgeos-dev \
        libhdf4-alt-dev \
        libhdf5-serial-dev \
        libnetcdf-dev \
        libpoppler-dev \
        libproj-dev \
        libpq-dev \
        libspatialite-dev \
        libxml2-dev \
        netcat \
        python3-software-properties \
        python3-dev \
        python3-numpy \
        rsync \
        software-properties-common \
        smbclient \
        sqlite3 \
        unzip \
        vim \
        wget
    #&& additions=' \
    #    #libblas-dev \
    #    #liblapack-dev \
    #    #libkrb5-dev \
    #    #libsasl2-dev \
    #    #libssl-dev \
    #    #libffi-dev \
    #    #libgdal-dev \
    #    #libspatialindex-dev \
    #    #libfreetype6-dev \
    #    #libxslt-dev \
    #    #libsqlite3-dev \
    #    #zlib1g \
    #    #zlib1g-dev \
    #    #python-pip \
    #    #netcat \
    #    #cython \
    #    #python-numpy \
    #    #python-gdal \
    #    #libaio1 \
    #    #freetds-dev \
    #    #gdal-bin \
    #    #osm2pgsql \
    #    default-libmysqlclient-dev \
    #    #python-requests \
    #'

# Update Locales, add Airflow User
RUN sed -i 's/^# en_US.UTF-8 UTF-8$/en_US.UTF-8 UTF-8/g' /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    && useradd -ms /bin/bash -d ${AIRFLOW_HOME} airflow

# NodeJS packages
#RUN curl -sL https://deb.nodesource.com/setup_10.x | bash - \
#    && apt-get install -y nodejs \
#    && npm install -g mapshaper \
#    && npm install -g geobuf

RUN pip install -U pip setuptools wheel \
    && pip install apache-airflow[crypto,celery,postgres,slack,s3,jdbc,mysql,mssql,ssh,password,rabbitmq,samba,redis]==${AIRFLOW_VERSION} \
    && pip install boto3 \
    && pip install bs4 \
    && pip install fiona \
    && pip install gdal==2.1.0 \
    && pip install git+https://github.com/jguthmiller/pygeobuf.git@geobuf-v3 \
    && pip install geojson \
    && pip install geopandas \
    && pip install geomet \
    && pip install lxml \
    && pip install keen \
    && pip install ndg-httpsclient \
    && pip install pandas \
    && pip install pymssql \
    && pip install psycopg2-binary \
    && pip install pyasn1 \
    && pip install PyGithub \
    && pip install pyOpenSSL \
    && pip install pytz \
    && pip install 'redis>=2.10.5,<3' \
    && pip install requests \
    && pip install shapely \
    && pip install xlrd \
    ## Additions
    #&& pip install Cython \
    #&& pip install packaging \
    #&& pip install appdirs \
    ##&& pip install pytz==2015.7 \
    #&& pip install mysql-python \
    #&& pip install logging \
    #&& pip install boto \
    #&& pip install httplib2 \
    #&& pip install autodoc==0.3 \
    #&& pip install Sphinx==1.5.1 \
    #&& pip install celery==4.0.2 \
    #&& pip install beautifulsoup4==4.5.3 \
    #&& pip install ipython==5.3.0 \
    #&& pip install jupyter \
    #&& pip install password \
    #&& pip install Flask-Bcrypt \
    #&& pip install geopy==1.11 \
    #&& pip install rtree \
    #&& pip install descartes \
    #&& pip install pyproj \
    #&& pip install requests==2.13.0 \
    #&& apt-get purge --auto-remove -yqq $buildDeps \
    #&& apt-get purge --auto-remove -yqq $additions \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

# Get Oracle Client
# TODO -- ADD
ADD http://datasd-dev-assets.s3.amazonaws.com/oracle.zip ${AIRFLOW_HOME}/
ADD https://github.com/energyhub/secretly/releases/download/0.0.6/secretly-linux-amd64 /usr/local/bin/secretly

COPY script/entrypoint.sh ${AIRFLOW_HOME}/entrypoint.sh
COPY config/airflow.cfg ${AIRFLOW_HOME}/airflow.cfg

RUN chmod +x /usr/local/bin/secretly


RUN unzip ${AIRFLOW_HOME}/oracle.zip -d /opt \
  && env ARCHFLAGS="-arch $ARCH" pip install cx_Oracle \
  && rm ${AIRFLOW_HOME}/oracle.zip

RUN chown -R airflow: ${AIRFLOW_HOME} \
    && chmod +x ${AIRFLOW_HOME}/entrypoint.sh \
    && chown -R airflow /usr/lib/python* /usr/local/lib/python* \
    #&& chown -R airflow /usr/lib/python2.7/* /usr/local/lib/python2.7/* \
    && chown -R airflow /usr/local/bin* /usr/local/bin/*
    #&& sed -i "s|flask.ext.cache|flask_cache|g" /usr/local/lib/python2.7/dist-packages/flask_cache/jinja2ext.py

EXPOSE 8080 5555 8793

USER airflow
WORKDIR ${AIRFLOW_HOME}
ENTRYPOINT ["./entrypoint.sh"]
CMD ["secretly", "webserver"] # set default arg for entrypoint

