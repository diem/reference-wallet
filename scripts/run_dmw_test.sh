#!/bin/bash

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


trap 'jobs -p | xargs kill -9' EXIT

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
output_dir="$script_dir/../output"
backend_dir="$script_dir/../backend"

if ! command -v ifconfig &> /dev/null
then
  sudo apt install net-tools
fi

host_ip=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | grep -v -e'^$' | head -n 1)

if [ -z "$host_ip" ]
then
  echo "COULD NOT GET HOST IP!"
  exit 1
fi

echo "Networks:"
ip addr

echo "Host IP: $host_ip"

cd "$script_dir/../"
rm -rf backend/.env
VASP_BASE_URL=http://localhost:8080/api/offchain PIPENV_PIPFILE=backend/Pipfile pipenv run python3 ./scripts/set_env.py

echo "Env:"
cat backend/.env

# Prepare output dir
mkdir -p "$output_dir"
rm -rf "$output_dir/*"


set +e

# Launch DRW
echo "Launching DRW..."
./scripts/lrw.sh develop 8080 > "$output_dir/docker.txt" 2>&1 &

# Wait for server to report readiness
./scripts/wait_for_server_ready.sh 6
# Wait additionally as waiting for log lines is a poor indicator of readiness
sleep 15

# Launch Proxy
cd "$backend_dir"
echo "Launching Proxy..."
DRW_URL_PREFIX=http://localhost:8080 MW_DRW_PROXY_PORT=3150 MW_DRW_PROXY_HOST=0.0.0.0 pipenv run python3 ./tests/mw_drw_proxy/proxy.py > "$output_dir/proxy.txt" 2>&1 &
sleep 5

# Write pre output
docker-compose -f ../docker/docker-compose.yaml -f ../docker/dev.docker-compose.yaml logs > "$output_dir/pre_test_docker.txt" 2>&1

# Start testing!
echo "Starting Test..."
pipenv run dmw -- test --verbose --target http://localhost:3150 --stub-bind-host=0.0.0.0 --stub-bind-port 4542 --stub-diem-account-base-url "http://$host_ip:4542" | tee "$output_dir/test.txt" 2>&1 || true
