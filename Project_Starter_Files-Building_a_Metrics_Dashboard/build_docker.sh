#! /bin/bash

pushd app/backend
docker build -t york42/nd064-p3-backend:latest .
docker push york42/nd064-p3-backend:latest
popd

pushd app/frontend
docker build -t york42/nd064-p3-frontend:latest .
docker push york42/nd064-p3-frontend:latest
popd

pushd app/trial
docker build -t york42/nd064-p3-trial:latest .
docker push york42/nd064-p3-trial:latest
popd



