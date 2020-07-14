# Libra Reference Wallet

Libra Reference Wallet is an open-source project aimed at helping developers kickstart wallet building in the Libra ecosystem. We tried to incorporate both technical and design aspects to show not only how the different technical pieces fit together but also demonstrate thoughtful design, content, and best experience practices.


## Note to Developers
* Libra Reference Wallet is a reference implementation, and not meant to be fully production grade. 
* The project will continue to develop to include the different aspects of the evolving Libra ecosystem.   

## Project Organization

The project is separated into the following components:
* [backend](/backend)
* [frontend](/frontend)
* [gateway](/gateway)
* [liquidity](/liquidity)
* [mobile](/mobile)

The [backend](/backend) system comprises of a Python server that consumes the pylibra python client and the pub-sub-proxy. `pylibra` is used for submitting and requesting transactions from the network. `pub-sub-proxy` is used for subscribing to events.

The project uses [docker](/docker) for organizing and easily spinning up. The production configuration of this system varies slightly to allow for handling a large number of inbound requests.

The [gateway](/gateway) is an nginx server that routes requests to either the front end or backend.

The front end runs on port 3000.
The backend runs on port 5000.

A mock [liquidity](/liquidity) provider is provided to allow testing simple liquidity functionality. This piece should be replaced by a service that provides your organization with needed liquidity functionality.

The web [frontend](/frontend) is a React based web application.

The [mobile application](/mobile) is a React Native based mobile application for both iOS and Android.
