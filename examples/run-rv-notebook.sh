#!/bin/bash

DIR=${1:-`pwd`}

docker=${DOCKER_EXEC:-docker}
docker_image=${DOCKER_RVNB_IMAGE:-radioastro/notebook}
port=${DOCKER_RVNB_PORT:-$[$UID+8000]}

if ! which $docker >/dev/null; then
  echo "$docker: no such executable. We need a working docker install!"
  echo "(If your docker is invoked as something else, please set the DOCKER_EXEC variable.)"
  exit 1
fi


if ! $docker images | grep $docker_image >/dev/null; then
  echo "Looks like the $docker_image docker image needs to be built."
  echo "This is a one-time operation that may take a few minutes, please be patient."
fi

echo "Will run the result viewer notebook ($docker_image) on $DIR."
echo "The notebook server will be available on port $port, set DOCKER_RVNB_PORT to override."
echo "Point your browser to localhost:$port"

if ! cd $DIR; then
  echo "Can't cd into $DIR, sorry."
  exit 1
fi

if [ "$DOCKER_RVNB_NOTEBOOKS" != "" ]; then
  echo "Caution, your $DOCKER_RVNB_NOTEBOOKS will be mounted inside the container"
  volumes="-v $DOCKER_RVNB_NOTEBOOKS:/notebooks:rw"
fi

DIR=${DIR%/}
container_dirname=${DIR##*/}

docker run -it -p $port:8888 \
                $volumes \
                -v $DIR:/notebooks/$container_dirname:rw \
                -e RVNB_DATA_DIR=/notebooks/$container_dirname \
                -e RVNB_ORIGINAL_DIR=$DIR \
                -e RVNB_NOTEBOOK_DIR=/notebooks \
                $docker_image 
