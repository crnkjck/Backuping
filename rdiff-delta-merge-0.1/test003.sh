#!/bin/bash

dd if=/dev/urandom of=f1 bs=1M count=1 &> /dev/null
dd if=/dev/urandom of=f2 bs=1M count=1 &> /dev/null
g++ merge.cpp &> /dev/null

runtest() {
 (cat f1 ; echo $1 ; cat f2) > tf.1
 (cat f1 ; echo $2 ; cat f2) > tf.2
 (cat f1 ; echo $3 ; cat f2) > tf.3
 (cat f1 ; echo $4 ; cat f2) > tf.4
 rdiff signature tf.1 tf.1s &> /dev/null
 rdiff signature tf.2 tf.2s &> /dev/null
 rdiff signature tf.3 tf.3s &> /dev/null
 rdiff delta tf.1s tf.2 tf.d12 &> /dev/null
 rdiff delta tf.2s tf.3 tf.d23 &> /dev/null
 rdiff delta tf.3s tf.4 tf.d34 &> /dev/null
 rdiff delta tf.1s tf.4 tf.d14 &> /dev/null

 ./a.out tf.d12 tf.d23 tf.d34 > tf.d14_t 2> /dev/null

 rdiff patch tf.1 tf.d14_t tf.4_t &> /dev/null
 echo -n "$1 $2 $3 $4 - "
 cmp tf.4 tf.4_t &> /dev/null && echo OK || echo FAILED

 rm -f tf.*
}

runtest 111 222 333 444
runtest 111 222 333 4444
runtest 111 2222 3333 4444
runtest 1111 222 333 4444
runtest 1111 2222 3333 444
runtest 11111 222 333 4444
runtest 11 222 3333 44444
runtest 11111 2222 333 44
runtest 111 2222 33 44444
runtest 11111 22 3333 444
