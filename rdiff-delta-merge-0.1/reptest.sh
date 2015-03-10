dd if=/dev/urandom of=f1 bs=10K count=1 &> /dev/null
dd if=/dev/urandom of=f2 bs=10K count=1 &> /dev/null
(cat f1 ; echo 11 ; cat f2) > tf.1
(cat f1 ; echo 222 ; cat f2) > tf.2
(cat f1 ; echo 3333; cat f2) > tf.3
(cat f1 ; echo 44444 ; cat f2) > tf.4
rdiff signature tf.1 tf.1s
rdiff signature tf.2 tf.2s
rdiff signature tf.3 tf.3s
rdiff delta tf.1s tf.2 tf.d12
rdiff delta tf.2s tf.3 tf.d23
rdiff delta tf.3s tf.4 tf.d34
rdiff delta tf.1s tf.4 tf.d14

while true ; do g++ merge.cpp && ./a.out tf.d12 tf.d23 tf.d34 > /dev/null ; echo ; sleep 1 ; done
