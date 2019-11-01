docker volume create input_output

docker run --rm -it ^
    -v %cd%:/ptm ^
    -v input_output:/input_output ^
    --link master_ptmMaster_1:localmaster ^
    -v /var/run/docker.sock:/var/run/docker.sock ^
    python:3-stretch /bin/bash