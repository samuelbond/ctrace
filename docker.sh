#!/usr/bin/env bash

## Cleanup

## Stop Containers
docker container stop con01
docker container stop con02
docker container stop con03
docker container stop con04
docker container stop con05
docker container stop con06

## Remove Containers
docker container rm con01
docker container rm con02
docker container rm con03
docker container rm con04
docker container rm con05
docker container rm con06

## Remove Networks
docker network rm br0
docker network rm br1

## Create bridge network
docker network create --driver=bridge --subnet=192.168.0.0/16 br0
docker network create --driver=bridge --subnet=172.168.0.0/16 br1

## Create Containers
docker create --name con01 --network=br0  nginx:1.17.2-alpine
docker create --name con02 --network=br0  nginx:1.17.2-alpine
docker create --name con03 --network=br0  nginx:1.17.2-alpine
docker create --name con04 --network=br1  nginx:1.17.2-alpine
docker create --name con05 --network=br1  nginx:1.17.2-alpine
docker create --name con06 --network=br1  nginx:1.17.2-alpine

## Attach Network to Container
docker network connect br1 con03

## Start Containers
docker container start con01
docker container start con02
docker container start con03
docker container start con04
docker container start con05
docker container start con06

## Container info
docker container ls -a

