# Installation
- set up a Linux server (incl. domain, SLL, etc.)
- install Docker and Python

## Docker configuration
- copy the files <em>docker-compose.yml, create_environment.py, createsuperuser.sh</em> and <em>init_db.sh</em> into a directory on the server
- run create_environment.py (<em>python create_environment.py</em>)
   > optional: edit the created .env file
- start up the service with <em>docker-compose up -d</em>
- run ./createsuperuser.sh and follow the instructions
   > The script has to be flagged as executable (chmod +x). The container needs to be up and running and have the default name!
- run ./init_db.sh to initialize important database objects
   > The script has to be flagged as executable (chmod +x). The container needs to be up and running and have the default name!

## Server configuration
- pass requests to the domain to the service running at the port you set up with setup.py (http://localhost:{EXT_PORT}, see the created <em>.env</em> file)
- pass web socket requests to the service running at the port you set up (http://localhost:{EXT_PORT})
- forward the request headers to the service
- set up your certificates
- example Apache configuration at <em>/dist/site/apache.conf</em>
