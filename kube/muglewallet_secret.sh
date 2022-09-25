#!/bin/bash
  
echo -n "password" > ./password.txt
kubectl create secret generic muglewallet --from-file=./password.txt
rm ./password.txt

