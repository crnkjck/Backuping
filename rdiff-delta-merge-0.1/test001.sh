#!/bin/bash

dd if=/dev/urandom of=f1 bs=1M count=1 &> /dev/null
dd if=/dev/urandom of=f2 bs=1M count=1 &> /dev/null
g++ merge.cpp &> /dev/null

runtest() {
 (cat f1 ; echo $1 ; cat f2) > tf.1
 (cat f1 ; echo $2 ; cat f2) > tf.2
 (cat f1 ; echo $3 ; cat f2) > tf.3
 rdiff signature tf.1 tf.1s &> /dev/null
 rdiff signature tf.2 tf.2s &> /dev/null
 rdiff delta tf.1s tf.2 tf.d12 &> /dev/null
 rdiff delta tf.2s tf.3 tf.d23 &> /dev/null
 rdiff delta tf.1s tf.3 tf.d13 &> /dev/null

 ./a.out tf.d12 tf.d23 > tf.d13_t 2> /dev/null

 rdiff patch tf.1 tf.d13_t tf.3_t &> /dev/null
 echo -n "$1 $2 $3 - "
 cmp tf.3 tf.3_t &> /dev/null && echo OK || echo FAILED

 rm -f tf.*
}

runtest 111 222 333
runtest 111 222 3333
runtest 111 2222 3333
runtest 1111 222 3333
runtest 1111 2222 333
runtest 11111 222 3333 
runtest 11 222 3333
runtest 1111 22 333
