#!/usr/bin/env bash

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

script_dir="$(dirname "$0")"
project_dir="$(dirname "$script_dir")"

source "$script_dir/funcs.sh"

show_help() {
  echo ""
  warn "Diem reference wallet C&C"
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
  local build_mode=${2:-dev}
  echo "production mode with gw port ${port}"
  echo "build mode is ${build_mode}"

  if [ "$build_mode" = "helm" ]; then
    docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_STATIC_YAML} build  || fail 'docker-compose build failed!'
  elif [ "$build_mode" = "e2e" ]; then
    mkdir -p gateway/tmp/frontend
    docker-compose -f ${COMPOSE_YAML} build  || fail 'docker-compose build failed!'
  elif [ "$build_mode" = "dev" ]; then
    docker-compose -f ${COMPOSE_YAML} -f ${COMPOSE_DEV_YAML} build || fail 'docker-compose build failed!'
  else
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
    docker-compose -f ${COMPOSE_YAML} build || fail 'docker-compose build failed!'
  fi
}

start() {
  build $GW_PORT "prod"
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

# NOTE: This function is used for automating e2e test deployments
#       Output from this function is used to configure connections to e2e wallet deployments
#       and will be evaluated as code. Debug statements must be prepended with as comments, and all
#       unintended output suppressed to /dev/null
e2e() {
  local up_down=$1
  composes="${COMPOSE_YAML} -f ${COMPOSE_E2E_YAML}"
  volumes="lrw_${PG_VOLUME} lrw2_${PG_VOLUME_DOUBLE}"

  export COMPOSE_PROJECT_NAME=""

  echo "# Operating on double wallet instance"

  if [ "$up_down" = "up" ]; then
    export GW_PORT=$(get_port)
    export GW_OFFCHAIN_SERVICE_PORT_1=8091
    PIPENV_PIPFILE=backend/Pipfile PIPENV_DONT_LOAD_ENV=1 \
                  GW_PORT=$GW_PORT GW_OFFCHAIN_SERVICE_PORT=$GW_OFFCHAIN_SERVICE_PORT_1 \
                  VASP_BASE_URL="http://lrw_backend-web-server_1:5091" \
                  pipenv run python3 scripts/set_env.py > /dev/null
    export VASP_ADDR_1=$(source backend/.env && echo $VASP_ADDR)
    echo "export GW_PORT_1=$GW_PORT"
    echo "export GW_OFFCHAIN_SERVICE_PORT_1=$GW_OFFCHAIN_SERVICE_PORT_1"
    echo "export VASP_ADDR_1=$VASP_ADDR_1"
    echo "export LRW_WEB_1=http://localhost:$GW_PORT"
    docker-compose -p lrw -f $composes up --detach > /dev/null

    # saves .env to temp for creating second .env
    tmp_backend_env=$(mktemp)
    tmp_liquidity_env=$(mktemp)
    backend_env="${project_dir}/backend/.env"
    liquidity_env="${project_dir}/liquidity/.env"
    cp $backend_env $tmp_backend_env
    cp $liquidity_env $tmp_liquidity_env

    # second
    export GW_PORT_2=$(get_port)
    export GW_OFFCHAIN_SERVICE_PORT_2=8092
    PIPENV_PIPFILE=backend/Pipfile PIPENV_DONT_LOAD_ENV=1 \
                  GW_PORT=$GW_PORT_2 GW_OFFCHAIN_SERVICE_PORT=$GW_OFFCHAIN_SERVICE_PORT_2 \
                  VASP_BASE_URL="http://lrw2_backend-web-server_1:5091" \
                  pipenv run python3 scripts/set_env.py > /dev/null
    export VASP_ADDR_2=$(source backend/.env && echo $VASP_ADDR)
    echo "export GW_PORT_2=$GW_PORT_2"
    echo "export GW_OFFCHAIN_SERVICE_PORT_2=$GW_OFFCHAIN_SERVICE_PORT_2"
    echo "export VASP_ADDR_2=$VASP_ADDR_2"
    echo "export LRW_WEB_2=http://localhost:$GW_PORT_2"

    export GW_PORT=$GW_PORT_2
    export GW_OFFCHAIN_SERVICE_PORT=$GW_OFFCHAIN_SERVICE_PORT_2
    docker-compose -p lrw2 -f $composes up --detach > /dev/null

    docker network create lrw_to_lrw2_offchain > /dev/null
    docker network connect lrw_to_lrw2_offchain lrw_backend-web-server_1 > /dev/null
    docker network connect lrw_to_lrw2_offchain lrw2_backend-web-server_1 > /dev/null

    # save lrw2 .env to .env-2
    cp $backend_env "${backend_env}-2"
    cp $liquidity_env "${liquidity_env}-2"
    # move back lrw .env to .env
    cp $tmp_backend_env $backend_env
    cp $tmp_liquidity_env $liquidity_env
  elif [ "$up_down" = "down" ]; then
    docker-compose -p lrw -f $composes down
    docker-compose -p lrw2 -f $composes down
    echo "# Purging $volumes"
    docker volume rm -f $volumes
  else
    echo '# Must specify either `up` or `down` option'
    exit 1
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
  PIPENV_PIPFILE=backend/Pipfile backend/test.sh
}

setup_environment() {
  local skip_build=${1:-false}
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

  info "***Setting up environment .env files***"
  PIPENV_PIPFILE=backend/Pipfile pipenv run python3 scripts/set_env.py || fail "Failed execute scripts/set_env.py"

  info "***Setting up docker-compose project name***"
  cp .env.example .env

  if [ "$skip_build" == true ]; then
    echo "Skipping build"
    exit 0
  fi

  info "***Installing frontend dependencies***"
  sh -c "cd frontend && yarn"

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
