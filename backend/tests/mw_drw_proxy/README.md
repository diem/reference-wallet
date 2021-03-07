# MiniWallet <=> Reference Wallet Proxy

This will run a proxy which allows the DMW test suite to communicate with DRW.

For example, when the DRW requests to set up a user, the proxy registers a user, updates their information with KYC, 
and deposits any initial test balances that the DMW required, before returning an identifier for that user which DMW 
will reuse in future calls.


### Usage:
(from inside the venv) 
```
DRW_URL_PREFIX=http://reference_wallet:8080 MW_DRW_PROXY_PORT=3130 pipenv run python3 tests/mw_drw_proxy/proxy.py
```
This will launch the proxy server on `http://localhost:3130`, and will proxy the requests to an instance of 
DRW running at `http://reference_wallet:8080`