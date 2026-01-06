#!/bin/bash -eu
#
# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################

# # Fix parentheses for macros
# find . -name "*.c" -exec sed -i 's/if PyFloat_Check (obj) {/if (PyFloat_Check (obj)) {/g' {} +
# find . -name "*.c" -exec sed -i 's/if PyUnicode_Check (ret) {/if (PyUnicode_Check (ret)) {/g' {} +
# # PyLong_Check(obj)
# find . -name "*.c" -exec sed -i 's/if PyLong_Check(obj) {/if (PyLong_Check(obj)) {/g' {} +
# # if PyBool_Check (obj)
# find . -name "*.c" -exec sed -i 's/if PyBool_Check (obj) {/if (PyBool_Check (obj)) {/g' {} +
# # if PyBytes_Check (obj)
# find . -name "*.c" -exec sed -i 's/if PyBytes_Check (obj) {/if (PyBytes_Check (obj)) {/g' {} + 
# # PyUnicode_Check (obj)
# find . -name "*.c" -exec sed -i 's/if PyUnicode_Check (obj) {/if (PyUnicode_Check (obj)) {/g' {} +
find . -name "*.c" -exec sed -i \
    -E 's/if *(Py[A-Za-z_]+_Check) *\(([^)]+)\) *\{/\if (\1 (\2)) {/g' {} +

export CFLAGS="$CFLAGS -Wno-deprecated-declarations"

./autogen.sh
./configure --with-http=no
make -j$(nproc) clean
make -j$(nproc) all

seed_corpus_temp_file="$OUT/xml_seed_corpus.zip"
zip -r $seed_corpus_temp_file $SRC/libxml2/test

for fuzzer in libxml2_xml_read_memory_fuzzer libxml2_xml_reader_for_file_fuzzer; do
  $CXX $CXXFLAGS -std=c++11 -Iinclude/ \
      $SRC/$fuzzer.cc -o $OUT/$fuzzer \
      $LIB_FUZZING_ENGINE .libs/libxml2.a -lz

  cp $SRC/*.dict $OUT/$fuzzer.dict
  cp $seed_corpus_temp_file $OUT/${fuzzer}_seed_corpus.zip
done
