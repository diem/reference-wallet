# pubsub_proxy

## Summary

Libra's pubsub_proxy is the library that allows you to subscribe to particular events/accounts on Libra blockchain and get notified whenever new relevant state is discovered.
It's part of Python Libra SDK.
`pubsub_proxy` acts as a bridge(thin layer) between Libra full nodes and pub/sub broker of your choice.


## Usage

```python
from pubsub_proxy import LibraPubSubProxy, Settings

settings = Settings.load_from_file(...)
LibraPubSubProxy(settings).start()
```
More detailed example can be found in `examples/testnet.py`.

## Configuration
- Format: json
- Parameters:
    * `libra_node_uri`: uri of Libra full node used for synchronization
    * `sync_interval_ms`: time interval between queries to full node
    * `log_file`: location of log file
    * `pubsub_type`: pub/sub type used to deliver new events<br />
        current available options: `logging`
    * `pubsub_config`: configuration of specific broker<br />
        *exact configuration depends on broker type*
    * `progress_storage_type`: type of storage used to store progress<br />
        current available options: `in_memory`
    * `progress_storage_config`: configuration of specific storage<br />
        *exact configuration depends on storage type*
    * `account_subscription_storage_type`: type of storage used to store subscriptions
    * `account_subscription_storage_type`: configuration of specific storage<br />
        *exact configuration depends on storage type*
    * `sync_strategy_type`: strategy used for synchronization routine <br/>
        current available options: [`event_stream`, `tail_blockchain`]
    * `sync_strategy_config`: configuration of specific sync strategy
        *exact configuration depends on strategy type*


Note: instead of using one of predefined backend types for pub/sub broker, progress storage or subscription storage,<br/>
you can always create custom implementation that implements base interface and pass it to configuration directly.
