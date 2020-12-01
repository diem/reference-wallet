# Diem reference wallet (LRW) launcher
Command & control utility deploy debug and develop libra reference wallet through a consistent and reproducible docker environment.


## Features
- Deploy lrw with production configuration using docker-compose.
- Start lrw in development mode. Changes to source code or dependencies will reflect in the running environment.
- Install / Remove frontend packages using yarn and backend packages using pipenv to the running environment while in development mode.
- Debug - attach a debugger to lrw backend.
- Configure block explorer frontend will use - TBD
- Reset local DB - TBD 

## Perquisites
- Docker and docker-compose are installed

## Usage
Make sure you run the script from project dir and not from scripts dir.
```bash
Usage: scripts/lrw.sh <command>

Commands:

start <port>               Build project and run all components in production mode.
develop <port>             Build project and run all components in development mode.
debug                      Run backend on host machine to allow debugger attachment.
                           develop mode must be active in order for this to work.
logs                       Show services logs when debug mode is active
down                       Stop all running services and remove them
stop                       Stop all running services
build                      Rebuild all services
purge                      Reset local database
run yarn add <pkg>         Add new package both to host and frontend running container in debug mode
run yarn remove <pkg>      Remove pkg both from host and from frontend running container in debug mode
run pipenv install <pkg>   Add new package both to host and backend running container in debug mode
run pipenv uninstall <pkg> Remove package both from host and from backend running container in debug mode
watch_test                 Run tests in watch mode
```


## Examples
```bash
scripts/lrw.sh start
```
Will build services docker images with production configuration. The frontend will be compiled and served from a static folder
using Nginx.
LRW will run in background but logs will be piped to stdout.

To finish production session run ```scripts/lrw.sh down```

```bash
scripts/lrw.sh develop
```
Will run all services including frontend service in development mode.
Since the source code is mapped as a volume changes in code will reflect in the running environment.
Logs will be presented on screen using ```^C``` to exit will stop running lrw services.
While development mode is running it is possible to install new packages like so:

```scripts/lrw.sh run yarn add <package>```
Will install package to frontend. Changes will reflect in both host machine so IDE can parse the new package and to the running environment.

```scripts/lrw.sh run pipenv install <package>``` will do the same for the backend.

It is also possible to debug backend while development mode is active by running:
```bash
scripts/lrw.sh debug
```

This will run the python backend locally on the host machine so you can attach your favorite debugger.
It is also possible to set a debugger configuration to run this script.
On stop frontend, docker service will reload automatically so it is possible to continue as normal.

