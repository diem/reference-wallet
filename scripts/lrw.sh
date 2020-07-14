#!/usr/bin/env bash

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

script_dir="$(dirname "$0")"
project_dir="$(dirname "$script_dir")"

source "$script_dir/funcs.sh"

show_help() {
  echo ""
  warn "Libra reference wallet C&C"
  echo ""
  echo "Usage: scripts/lrw.sh <command>"
  echo ""
  info "Commands:"
  echo ""
  echo "setup_environment          Create a .env file with custody private key and wallet public address for the project."
  echo "start <port>               Build project and run all components in production mode."
  echo "develop <port>             Build project and run all components in development mode."
  echo "debug                      Run backend on host machine to allow debugger attachment."
  echo "                           develop mode must be active in order for this to work."
  echo "logs                       Show services logs when debug mode is active"
  echo "down                       Stop all running services and remove them"
  echo "stop                       Stop all running services"
  echo "build                      Rebuild all services"
  echo "deploy_minikube            Build and deploy application to minikube"
  echo "purge                      Reset local database"
  echo "run yarn add <pkg>         Add new package both to host and frontend running container in debug mode"
  echo "run yarn remove <pkg>      Remove pkg both from host and from frontend running container in debug mode"
  echo "run pipenv install <pkg>   Add new package both to host and backend running container in debug mode"
  echo "run pipenv uninstall <pkg> Remove package both from host and from backend running container in debug mode"
  echo "watch_test                 Run tests in watch mode"
  echo
}

OPTIND=1

PRODUCTION=1
COMPOSE_YAML=docker/docker-compose.yaml
COMPOSE_DEV_YAML=docker/dev.docker-compose.yaml
COMPOSE_DEBUG_YAML=docker/debug.docker-compose.yaml
COMPOSE_E2E_YAML=docker/e2e.docker-compose.yaml
COMPOSE_DOUBLE_YAML=docker/double.docker-compose.yaml
COMPOSE_E2E_DOUBLE_YAML=docker/e2e.double.docker-compose.yaml
COMPOSE_STATIC_YAML=docker/static.docker-compose.yaml
PG_VOLUME=pg-data
PG_VOLUME_DOUBLE=pg-data-2
export GW_PORT=8080

frontend=frontend
backend=backend-web-server
gateway=gateway
db_file=/tmp/test.db


yarn__add() {
  info "running \"yarn add $@\" on host machine"
  command yarn --cwd frontend/ add $@

  if [ -z `docker-compose -f $COMPOSE_YAML -f $COMPOSE_DEV_YAML ps -q $frontend` ] || [ -z `docker ps -q --no-trunc | grep $(docker-compose -f $COMPOSE_YAML -f $COMPOSE_DEV_YAML ps -q $frontend)` ]; then
    warn "Service, $frontend is not running."
  else
    info "running yarn add $@ on $frontend service"
    docker-compose -f $COMPOSE_YAML -f $COMPOSE_DEV_YAML exec $frontend yarn add $@
  fi
}

yarn__remove() {
  info "running \"yarn remove $@\" on host machine"
  command yarn --cwd frontend/ remove $@

  if [ -z `docker-compose -f $COMPOSE_YAML -f $COMPOSE_DEV_YAML ps -q $frontend` ] || [ -z `docker ps -q --no-trunc | grep $(docker-compose -f $COMPOSE_YAML -f $COMPOSE_DEV_YAML ps -q $frontend)` ]; then
    warn "Service, $frontend is not running."
  else
    info "prune packages on $frontend service "
    docker-compose -f $COMPOSE_YAML -f $COMPOSE_DEV_YAML exec $frontend yarn install
  fi
}

yarn() {
  local subcmd=$1;
  shift

  if type "yarn__$subcmd" >/dev/null 2>&1; then
    "yarn__$subcmd" "$@"
  else
    command yarn "$subcmd" "$@" # call the **real** yarn command
  fi
}

pipenv__install(){
  local pipenv_list=$@
  info "running pipenv install ${pipenv_list[@]} on host machine"
  command pipenv install ${pipenv_list[@]}

  if [ -z `docker-compose -f $COMPOSE_YAML -f $COMPOSE_DEV_YAML ps -q $backend` ] || [ -z `docker ps -q --no-trunc | grep $(docker-compose -f $COMPOSE_YAML -f $COMPOSE_DEV_YAML ps -q $backend)` ]; then
    warn "Service, $backend is not running."
  else
    local remlist=(--dev)
    local piplist=${pipenv_list[@]/$remlist}

    info "running pip install ${piplist[@]} on $backend service"

    docker-compose -f $COMPOSE_YAML -f $COMPOSE_DEV_YAML exec $backend pip install ${piplist[@]}
    docker-compose -f $COMPOSE_YAML -f $COMPOSE_DEV_YAML up -d --force-recreate $backend
  fi
}

pipenv__uninstall(){
  info "running \"pipenv uninstall $@\" on host machine"
  command pipenv uninstall $@
}

pipenv(){
  local subcmd=$1;
  shift

  if type "pipenv__$subcmd" >/dev/null 2>&1; then
    "pipenv__$subcmd" "$@"
  else
    command pipenv "$subcmd" "$@" # call the **real** pipenv command
  fi
}

run() {
  local cmd=$1;
  shift 1
  if type "$cmd" >/dev/null 2>&1; then
    "$cmd" "$@"
  else
    echo "$cmd doesn't exist"
  fi
}

build() {
  local port=${1:-8080}
  local is_helm=${2:-false}
  echo "production mode with gw port ${port}"
  echo "helm chart mode is ${is_helm}"

  warn "removing old build artifacts..."
  rm -fr "${project_dir}/gateway/tmp/frontend/"


  info "build the frontend to a static production package"
  mkdir -p "${project_dir}/gateway/tmp/frontend/"
  warn "done"
  info "running docker to compile frontend..."
  docker build -t reference-wallet-frontend-build -f "${project_dir}/frontend/Dockerfile" "${project_dir}/frontend/" || fail 'frontend container build failed!'
  docker create --name tmp_reference_frontend reference-wallet-frontend-build || fail 'frontend compilation failed!'
  docker cp tmp_reference_frontend:/app/build/. "${project_dir}/gateway/tmp/frontend/" || fail 'frontend copy artifacts failed!'
  docker rm tmp_reference_frontend
  info "frontend build completed"

  # build all the service images using compose
  if [ "$is_helm" == false ]; then
    docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} build || fail 'docker-compose build failed!'
  else
    docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_STATIC_YAML} build  || fail 'docker-compose build failed!'
  fi

}

start() {
  build "$@"
  # run
  GW_PORT=$port docker-compose -f ${COMPOSE_YAML} up --detach
  docker-compose -f ${COMPOSE_YAML} logs --follow
}

develop() {
  local port=${1:-8080}
  local follow=${2:-true}
  echo "debug mode with gw port ${port}"

  # build the entire docker services using compose
  docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} pull redis

  GW_PORT=$port docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} up --detach --no-build

  if [ "$follow" == true ]; then
    docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} logs --follow --tail=500
    stop
  fi
}

# Get an unused port by binding 0; python2/3 compatible
get_port() {
  python -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1]); s.close()'
}

e2e() {
  
  local single_double=${1}
  local up_down=$2
  local upgrade=${3:-false} # use when upgrading single to double
  composes="${COMPOSE_YAML} -f ${COMPOSE_E2E_YAML}"
  volumes="docker_${PG_VOLUME}"

  if [ "$single_double" = "single" ]; then
    if [ "$upgrade" == true ]; then
      echo "Cannot upgrade single network"
      exit 1
    fi
    echo "Operating on single wallet instance"
  elif [ "$single_double" = "double" ]; then
    double_composes="$composes -f ${COMPOSE_DOUBLE_YAML} -f ${COMPOSE_E2E_DOUBLE_YAML}"
    volumes="$volumes docker_${PG_VOLUME_DOUBLE}"
    echo "Operating on double wallet instance"
  else
    echo 'Must specify valid count `single` or `double`'
  fi

  if [ "$up_down" = "up" ]; then
    if [ "$upgrade" == false ]; then
      export GW_PORT=$(get_port)
      ENV_FILE_NAME=".env" PIPENV_PIPFILE=backend/Pipfile PIPENV_DONT_LOAD_ENV=1 GW_PORT=$GW_PORT \
            LIQUIDITY_SERVICE_PORT=5000 LIQUIDITY_SERVICE_HOST="liquidity" \
            pipenv run python3 scripts/set_env.py > /dev/null 2>&1
      export VASP_ADDR_1=$(source backend/.env && echo $VASP_ADDR)
      echo "export GW_PORT_1=$GW_PORT"
      echo "export VASP_ADDR_1=$VASP_ADDR_1"
      docker-compose -f $composes up --detach > /dev/null 2>&1
    fi
    if [ "$single_double" = "double" ]; then
      export GW_PORT_2=$(get_port)
      ENV_FILE_NAME=".env-2" PIPENV_PIPFILE=backend/Pipfile PIPENV_DONT_LOAD_ENV=1 GW_PORT=$GW_PORT_2 \
            LIQUIDITY_SERVICE_PORT=5000 LIQUIDITY_SERVICE_HOST="liquidity-2" \
            pipenv run python3 scripts/set_env.py > /dev/null 2>&1
      export VASP_ADDR_2=$(source backend/.env-2 && echo $VASP_ADDR)
      echo "export GW_PORT_2=$GW_PORT_2"
      echo "export VASP_ADDR_2=$VASP_ADDR_2"
      docker-compose -f $double_composes up --detach > /dev/null 2>&1
    fi
  elif [ "$up_down" = "down" ]; then
    if [ "$single_double" = "single" ]; then
      docker-compose -f $composes down
    else
      docker-compose -f $double_composes down
    fi
    echo "Purging $volumes"
    docker volume rm -f $volumes > /dev/null 2>&1
  else
    echo 'Must specify either `up` or `down` option'
  fi
}

purge() {
  info "Remove pg volume"
  docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} down
  docker volume rm -f lrw_${PG_VOLUME}
}

logs() {
  docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} logs --follow
}

down() {
  docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} down
}

stop() {
  docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} stop
}

debug() {
  docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} rm -fsv $gateway
  docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} -f ${COMPOSE_DEBUG_YAML} build $gateway
  docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} -f ${COMPOSE_DEBUG_YAML} up -d --scale $backend=0
  ./build.sh
  REDIS_HOST=127.0.0.1 ./run_web.sh

  docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} -f ${COMPOSE_DEBUG_YAML} rm -fsv $gateway
  docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} build $gateway
  docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} up -d
}

deploy_minikube() {
  if ! minikube status >/dev/null 2>&1; then
    error "you must install minikube to run this command!"
    ec "please visit https://kubernetes.io/docs/tasks/tools/install-minikube/"
    exit 1
  fi

  if ! kubectl get pods -n kube-system | grep -q ingress-nginx-controller ; then
    warn "minikube ingress controller is disabled. no ingress will be installed"
    ec "please visit https://kubernetes.io/docs/tasks/access-application-cluster/ingress-minikube/ and enable it"
    ec "usually it just running \`minikube addons enable ingress\`"
  fi
  info "setting docker registery to minikube..."
  eval $(minikube docker-env)

  build 8080 true

  helm upgrade --install lrw helm/libra-reference-wallet \
    --set peripherals.redis.create=true --set peripherals.database.create=true
}

watch_test() {
  PIPENV_PIPFILE=backend/Pipfile pipenv run pytest-watch --  --disable-pytest-warnings backend/tests/$@
}

setup_environment() {
  if ! command -v pipenv &> /dev/null
  then
    ec "Installing pipenv"
    pip3 install pipenv
    exit
  fi

  info "***Initializing utilities submodule***"
  git submodule update --init --recursive

  info "***Installing backend dependencies***"
  sh -c "cd backend && pipenv install --dev"

  info "***Installing liquidity dependencies***"
  sh -c "cd liquidity && pipenv install --dev"

  info "***Installing frontend dependencies***"
  sh -c "cd frontend && yarn"

  info "***Setting up environment .env files***"
  PIPENV_PIPFILE=backend/Pipfile pipenv run python3 scripts/set_env.py

  info "***Setting up docker-compose project name***"
  cp .env.example .env

  info "***Building docker images***"
  build
}
# make sure we actually *did* get passed a valid function name
if declare -f "$1" >/dev/null 2>&1; then
  # invoke that function, passing arguments through
  "$@" # same as "$1" "$2" "$3" ... for full argument list

else
  show_help
  exit 1
fi
