#!/bin/sh

pid=16656
sleep 1
test -S chatsock
echo '(nick "foo")'
echo '(join "#chan")'
echo '(message "#chan" "hello world")'
echo '(part "#chan")'
nc -w 2 -U chatsock
perl -0777 -ne 'exit(1) unless m,\(message.+"foo".+"hello world"\),sm;'
perl -0777 -pe 's,\),\)\n,' -i out.txt
grep -c '(ok)' out.txt
test 2 '=' 3