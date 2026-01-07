FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG AFLPP_BRANCH=blackbox

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential python3-dev automake autoconf libtool cmake git flex bison \
    libglib2.0-dev libpixman-1-dev python3-setuptools cargo libgtk-3-dev \
    meson ninja-build cpio libcapstone-dev wget curl python3-pip pkg-config \
    ca-certificates \
 && bash -c "apt-get install -y lld-18 llvm-18 llvm-18-dev clang-18 || apt-get install -y lld llvm llvm-dev clang"

RUN gcc_ver=$(gcc --version | head -n1 | sed 's/.* //' | cut -d. -f1) \
 && apt-get update \
 && apt-get install -y gcc-${gcc_ver}-plugin-dev libstdc++-${gcc_ver}-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone https://github.com/niMgnoeSeeL/aflpp-covrec.git AFLplusplus

WORKDIR /opt/AFLplusplus
RUN git checkout "${AFLPP_BRANCH}" \
 && git submodule update --init \
 && make distrib \
 && make install

WORKDIR /opt/AFLplusplus/custom_mutators/examples
RUN gcc -shared -Wall -O3 -I/opt/AFLplusplus/include set.h set.c custom_post_run.c -o custom_post_run.so

ENV AFL_CUSTOM_MUTATOR_LIBRARY=/opt/AFLplusplus/custom_mutators/examples/custom_post_run.so
ENV PATH=/opt/AFLplusplus:${PATH}

WORKDIR /opt
RUN git clone https://gitlab.gnome.org/GNOME/libxml2.git

WORKDIR /opt/libxml2
RUN ./autogen.sh \
 && ./configure --enable-shared=no \
 && make CC=/opt/AFLplusplus/afl-clang-fast CXX=/opt/AFLplusplus/afl-clang-fast++ LD=/opt/AFLplusplus/afl-clang-fast

RUN mkdir -p /opt/libxml2/fuzz/in \
 && cp /opt/libxml2/xmllint /opt/libxml2/fuzz/xmllint_cov \
 && cp /opt/libxml2/test/*.xml /opt/libxml2/fuzz/in/

# Optional: afl-system-config may require privileged container runtime.
# RUN /opt/AFLplusplus/afl-system-config
