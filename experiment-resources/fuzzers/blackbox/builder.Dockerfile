# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ARG parent_image
FROM $parent_image

# sudo apt-get update
# sudo apt-get install -y build-essential python3-dev automake cmake git flex bison libglib2.0-dev libpixman-1-dev python3-setuptools cargo libgtk-3-dev
# # try to install llvm 14 and install the distro default if that fails
# sudo apt-get install -y lld-14 llvm-14 llvm-14-dev clang-14 || sudo apt-get install -y lld llvm llvm-dev clang
# sudo apt-get install -y gcc-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-plugin-dev libstdc++-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-dev
# sudo apt-get install -y ninja-build # for QEMU mode
# sudo apt-get install -y cpio libcapstone-dev # for Nyx mode
# sudo apt-get install -y wget curl # for Frida mode
# sudo apt-get install -y python3-pip # for Unicorn mode
# git clone https://github.com/AFLplusplus/AFLplusplus
# cd AFLplusplus
# make distrib
# sudo make install

RUN apt-get update && \
    apt-get install -y \
    build-essential python3-dev automake cmake git flex bison \
    libglib2.0-dev libpixman-1-dev python3-setuptools cargo libgtk-3-dev
RUN apt-get install -y lld-14 llvm-14 llvm-14-dev clang-14 || \
    apt-get install -y lld llvm llvm-dev clang
RUN apt-get install -y gcc-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-plugin-dev \
    libstdc++-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-dev
RUN apt-get install -y ninja-build # for QEMU mode
RUN apt-get install -y cpio libcapstone-dev # for Nyx mode
RUN apt-get install -y wget curl # for Frida mode
RUN apt-get install -y python3-pip # for Unicorn mode

# Download modified afl++.
RUN git clone -b <blackbox> https://anonymized/TBU.git /afl

# Build without Python support as we don't need it.
# Set AFL_NO_X86 to skip flaky tests.
RUN cd /afl && \
    unset CFLAGS CXXFLAGS && \
    export CC=clang AFL_NO_X86=1 && \
    PYTHON_INCLUDE=/ make && \
    cp utils/aflpp_driver/libAFLDriver.a /

RUN cd /afl && \
    PYTHON_INCLUDE=/ make all && make install

RUN cd /afl/custom_mutators/examples && \
    cc -O3 -fPIC -shared -g -o custom_post_run.so -I../../include set.c custom_post_run.c
