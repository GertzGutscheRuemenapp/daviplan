FROM osgeo/gdal:ubuntu-small-3.4.2
RUN curl -sL https://deb.nodesource.com/setup_14.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get -y update \
    && apt-get -y upgrade \
    && apt-get -y install git \
    && apt-get -y install nodejs \
    && apt-get -y install python3-pip \
    && apt-get -y install libpq-dev \
    && apt-get -y install binutils libproj-dev libgeos-dev \
    && apt-get -y install libsqlite3-mod-spatialite \
    && apt-get -y install osmium-tool \
    && apt-get -y install language-pack-de

RUN git clone https://github.com/GertzGutscheRuemenapp/bule_datentool.git /datentool

RUN npm i npm@9 -g
RUN npm i -g @angular/cli@14

# bundle the frontend scripts
WORKDIR /datentool/angular-frontend
RUN npm i
RUN ng build --stats-json --configuration production

# node modules tmp-directories may contain files with high UIDs that cause problems with CircleCI
RUN rm -R /datentool/angular-frontend/node_modules/tmp
RUN rm -R /usr/lib/node_modules/@angular/cli/node_modules/tmp

WORKDIR /datentool
RUN python -m pip install --upgrade pip && pip install -r requirements.txt
RUN mkdir -p /datentool/public/media
# django demands a secret key (not set in settings due to security reasons)
ENV SECRET_KEY=1234
RUN python manage.py collectstatic
# unset the key
ENV SECRET_KEY=

COPY run.sh /run.sh