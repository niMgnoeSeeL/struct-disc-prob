# build docker container that include AFL++ with residual risk estimation
# AFLPP_BRANCH options: blackbox, blackbox-no-reduction, greybox
docker build -t aflpp-covrec-<option>  --build-arg AFLPP_BRANCH=<option> /home/bohrok/icse26-ae/struct-disc-prob/replication/docker

# run the docker container
docker run -it --security-opt seccomp=unconfined aflpp-covrec-<option> /bin/bash

# run the fuzzing inside the docker container
cd /opt/libxml2/fuzz
/opt/AFLplusplus/afl-system-config
AFL_CUSTOM_MUTATOR_LIBRARY=/opt/AFLplusplus/custom_mutators/examples/custom_post_run.so   /opt/AFLplusplus/afl-fuzz -i in -o out -- ./xmllint_cov @@