FROM osgeo/gdal:ubuntu-small-3.2.0
RUN curl -sL https://deb.nodesource.com/setup_14.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get -y update \
    && apt-get -y upgrade \
    && apt-get -y install git \
    && apt-get -y install nodejs \
    && apt-get -y install python3-pip \
    && apt-get -y install libpq-dev \
    && apt-get -y install binutils libproj-dev libgeos-dev

RUN npm i npm@latest -g
RUN npm i -g @angular/cli@latest

RUN git clone https://github.com/GertzGutscheRuemenapp/bule_datentool.git $HOME/datentool
RUN python -m pip install --upgrade pip \
    && pip install -r $HOME/datentool/requirements.txt
WORKDIR root/datentool/angular-frontend
RUN npm ci
