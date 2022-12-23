# split sub-directory this file is in
DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SUBDIR=(${DIR//// })
# name of container is sub-directory + _web_1 if no name is given to docker-compose
CONTAINER=${SUBDIR[-1]}_web_1
# call django command to initialize database insiode running container
docker exec -it $CONTAINER python manage.py initproject
