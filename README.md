# Diem Reference Wallet

Diem Reference Wallet is an open-source project aimed at helping developers kickstart wallet building in the Diem ecosystem. We tried to incorporate both technical and design aspects to show not only how the different technical pieces fit together but also demonstrate thoughtful design, content, and best experience practices.


## Note to Developers
* Diem Reference Wallet is a reference implementation, and not meant to be fully production grade.
* The project will continue to develop to include the different aspects of the evolving Diem ecosystem.


## Getting Started

Setup instructions and system requirements can be found here: [backend](/backend#diem-reference-wallet)

## Project Organization

The project is separated into the following components:
* [backend](/backend)
* [frontend](/frontend)
* [gateway](/gateway)
* [liquidity](/liquidity)
* [mobile](/mobile)

The [backend](/backend) system comprises of a Python server that consumes the python sdk client and the pub-sub-proxy. `python sdk client` is used for submitting and requesting transactions from the network. `pub-sub-proxy` is used for subscribing to events.

The project uses [docker](/docker) for organizing and easily spinning up. The production configuration of this system varies slightly to allow for handling a large number of inbound requests.

The [gateway](/gateway) is an nginx server that routes requests to either the front end or backend.

The front end runs on port 3000.
The backend runs on port 5000.

A mock [liquidity](/liquidity) provider is provided to allow testing simple liquidity functionality. This piece should be replaced by a service that provides your organization with needed liquidity functionality.

The web [frontend](/frontend) is a React based web application.

The [mobile application](/mobile) is a React Native based mobile application for both iOS and Android.

## Getting started

The project uses Docker containers to run its components. The containers are orchestrated using
docker-compose.

**System Requirements:**
* docker and docker-compose - Docker can be installed from the [web](https://www.docker.com/products/docker-desktop). If you are installing Docker for the first time on your system, be sure to run it at least once to have it configure itself and get `docker-compose` as a runnable command.
* python 3.7
* yarn
* react-scripts

Run the following commands in the repository root to start a dev server:

```shell script
make bootstrap
make dev
```

The wallet website will be available at http://localhost:8080

See `docker/docker-compose.yaml` for the setup details.

## Development

Bootstrap environment, this is required for any other actions:

```bash
make bootstrap
```

Run all tests:

```bash
make alltest
```

Run all backend tests:

```bash
make test
```

Run single backend test: ```T=<test_name | test_file | test dir> make test```

```bash
T=wallet make test
```

Run e2e test:

```bash
make e2e
```

E2E test also support T option for running subset tests

```bash
T=double make e2e
```

See Makefile for more details
