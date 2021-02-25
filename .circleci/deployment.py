import json
import time
from dataclasses import dataclass, asdict
from enum import IntEnum, unique
from secrets import token_bytes

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from diem import jsonrpc, testnet, LocalAccount, utils, diem_types, stdlib
from logzero import logger
from mothership import go_hyperspace
from mothership.deployables.pg_rds.pg_database import PostgresDatabase
from mothership.deployables.secret import SecretUpdateStrategy
from mothership.deployables.secret.kub_secret import KubSecret
from mothership.deployables.service.simple_service import SimpleService, Route
from mothership.deployables.static_resource.static_resource import StaticResource
from mothership.deployments import Deployment, DeploymentConfig
from mothership.deployments.eks import EKS
from mothership.deployments.elastic_cache_redis import ElasticCacheRedis
from mothership.deployments.ingress_controller import IngressController, Subsystem
from mothership.deployments.rds_pg import PostgresInstance
from mothership.utils import passwords
from mothership.utils.domain_repository import DomainRepository
from mothership.utils.k8s.k8s import SecretMapping, WorkerLabelSelector

ECR_HOST = '695406093586.dkr.ecr.eu-central-1.amazonaws.com'
REFERENCE_WALLET_KUB_SECRET_NAME = 'diem-reference-wallet'
WALLET_BACKEND_IMAGE_NAME = 'diem-reference-wallet-backend'
LIQUIDITY_IMAGE_NAME = 'diem-reference-wallet-liquidity'

CURRENCY = 'XUS'


def generate_private_key() -> str:
    return utils.private_key_bytes(Ed25519PrivateKey.generate()).hex()


def get_account_from_private_key(private_key) -> LocalAccount:
    return LocalAccount(Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key)))


class VaspAccountMissingError(Exception):
    ...


@unique
class ChainType(IntEnum):
    TESTNET = testnet.CHAIN_ID.to_int()
    PREMAINNET = 21
    
    @property
    def json_rpc_url(self) -> str:
        if self == ChainType.TESTNET:
            return testnet.JSON_RPC_URL
        elif self == ChainType.PREMAINNET:
            return "https://premainnet.diem.com/v1"
        else:
            raise ValueError(f"Unexpected chain type {self.name}({self.value})")


@dataclass
class WalletSecrets:
    db_password: str
    backend_custodial_private_keys: str
    backend_custodial_private_keys_premainnet: str
    backend_wallet_private_key: str
    backend_wallet_private_key_premainnet: str
    backend_compliance_private_key: str
    backend_compliance_private_key_premainnet: str
    liquidity_custodial_private_keys: str
    liquidity_wallet_private_key: str

    @classmethod
    def generate(cls):
        db_password = passwords.generate_pg_password(18)
        backend_custodial_private_key = generate_private_key()
        backend_custodial_private_key_premainnet = generate_private_key()
        backend_compliance_private_key = generate_private_key()
        backend_compliance_private_key_premainnet = generate_private_key()
        liquidity_custodial_private_key = generate_private_key()

        return cls(
            db_password=db_password,
            backend_custodial_private_keys='{"wallet":"' + backend_custodial_private_key + '"}',
            backend_custodial_private_keys_premainnet='{"wallet":"' + backend_custodial_private_key_premainnet + '"}',
            backend_wallet_private_key=backend_custodial_private_key,
            backend_wallet_private_key_premainnet=backend_custodial_private_key_premainnet,
            backend_compliance_private_key=backend_compliance_private_key,
            backend_compliance_private_key_premainnet=backend_compliance_private_key_premainnet,
            liquidity_custodial_private_keys='{"liquidity":"' + liquidity_custodial_private_key + '"}',
            liquidity_wallet_private_key=liquidity_custodial_private_key,
        )

    def get_backend_wallet_private_key(self, chain: ChainType):
        if chain == ChainType.PREMAINNET:
            return self.backend_wallet_private_key_premainnet
        else:
            return self.backend_wallet_private_key

    def get_backend_compliance_private_key(self, chain: ChainType):
        if chain == ChainType.PREMAINNET:
            return self.backend_compliance_private_key_premainnet
        else:
            return self.backend_compliance_private_key

    @staticmethod
    def get_backend_custodial_private_keys_secret_name(chain: ChainType):
        if chain == ChainType.PREMAINNET:
            return f'{REFERENCE_WALLET_KUB_SECRET_NAME}.backend_custodial_private_keys_premainnet'
        else:
            return f'{REFERENCE_WALLET_KUB_SECRET_NAME}.backend_custodial_private_keys'

    @staticmethod
    def get_backend_compliance_private_key_secret_name(chain: ChainType):
        if chain == ChainType.PREMAINNET:
            return f'{REFERENCE_WALLET_KUB_SECRET_NAME}.backend_compliance_private_key_premainnet'
        else:
            return f'{REFERENCE_WALLET_KUB_SECRET_NAME}.backend_compliance_private_key'


class Vasp:
    def __init__(self, chain: ChainType, private_key, base_url, compliance_private_key):
        self.chain = chain
        self.api = jsonrpc.Client(chain.json_rpc_url)
        self.faucet = testnet.Faucet(self.api)

        self.account = get_account_from_private_key(private_key)
        self.base_url = base_url
        self.compliance_private_key = None
        if compliance_private_key:
            self.compliance_private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(compliance_private_key))

    @classmethod
    def create(cls, chain, private_key, base_url, compliance_private_key):
        vasp = cls(chain, private_key, base_url, compliance_private_key)
        vasp.ensure_account()
        return vasp

    @property
    def auth_key_hex(self) -> str:
        return self.account.auth_key.hex()

    @property
    def account_address_hex(self) -> str:
        return self.account.account_address.to_hex()

    @property
    def compliance_public_key_bytes(self) -> bytes:
        return utils.public_key_bytes(self.compliance_private_key.public_key())

    def ensure_account(self):
        logger.info(f'Creating and initialize the blockchain account {self.account_address_hex}')
        account_info = self.api.get_account(self.account.account_address)
        if not account_info:
            if self.chain == ChainType.TESTNET:
                self.mint(1_000_000, CURRENCY)
            else:
                raise VaspAccountMissingError(f'Account {self.account_address_hex} must exist')

    def mint(self, amount, currency):
        logger.info(f'Minting {amount} {currency} to account {self.account_address_hex}')
        self.faucet.mint(self.auth_key_hex, amount, currency)
        logger.info(f'Minted {amount} {currency} to account {self.account_address_hex}')

    def rotate_dual_attestation_info(self):
        logger.info(f'Rotating dual attestation for account {self.account_address_hex}')

        script = stdlib.encode_rotate_dual_attestation_info_script(
            self.base_url.encode("UTF-8"),
            self.compliance_public_key_bytes,
        )

        seq = self.api.get_account_sequence(self.account_address_hex)
        tx = diem_types.RawTransaction(
            sender=self.account.account_address,
            sequence_number=diem_types.st.uint64(seq),
            payload=diem_types.TransactionPayload__Script(value=script),
            max_gas_amount=diem_types.st.uint64(1_000_000),
            gas_unit_price=diem_types.st.uint64(0),
            gas_currency_code=CURRENCY,
            expiration_timestamp_secs=diem_types.st.uint64(int(time.time()) + 30),
            chain_id=diem_types.ChainId.from_int(self.chain.value),
        )
        signed_tx = self.account.sign(tx)

        self.api.submit(signed_tx)
        self.api.wait_for_transaction(signed_tx)
        logger.info(f'Rotated dual attestation for account {self.account_address_hex}')

    def validate_account(self):
        self.api.must_get_account(self.account.account_address)

    def validate_attestation(self):
        onchain_account_info = self.api.must_get_account(self.account.account_address)

        if self.compliance_public_key_bytes != bytes.fromhex(onchain_account_info.role.compliance_key):
            raise Exception(f'Wrong compliance key {onchain_account_info.role.compliance_key}')
        if self.base_url != onchain_account_info.role.base_url:
            raise Exception(f'Wrong base URL {onchain_account_info.role.base_url}')


@dataclass
class DeployableNames:
    web_backend_service: str
    web_backend_db: str
    dramatiq_service: str
    pubsub_service: str
    liquidity_service: str
    liquidity_db: str

    @classmethod
    def create(cls, chain: ChainType, env_prefix: str):
        base_service = "diem-reference-wallet-backend"
        service_chain = f"-{chain.name.lower()}" if chain != ChainType.TESTNET else ""
        db_chain = f"_{chain.name.lower()}" if chain != ChainType.TESTNET else ""
        return cls(
            web_backend_service=f"{base_service}-web{service_chain}",
            web_backend_db=f"{env_prefix}_diem_reference_wallet{db_chain}",
            dramatiq_service=f"{base_service}-dramatiq{service_chain}",
            pubsub_service=f"{base_service}-pubsub{service_chain}",
            liquidity_service=f"diem-reference-wallet-liquidity{service_chain}",
            liquidity_db=f"{env_prefix}_lp{db_chain}",
        )


class DiemReferenceWallet(Deployment):
    def __init__(self, config: DeploymentConfig):
        super().__init__(config)

        self.variables['build_tag'] = {'description': 'Official Diem Reference wallet build tag for all components'}
        self.depends_on = [EKS, IngressController, PostgresInstance, ElasticCacheRedis]

    def get_diem_wallet_hostname(self, chain: ChainType):
        domains: DomainRepository = self.outputs['IngressController']['domains']

        application_name = 'diem-reference-wallet'
        if chain != ChainType.TESTNET:
            application_name += '-'
            application_name += chain.name.lower()

        return domains.get_mapped_domain(Subsystem.DEMO, application_name)

    def deploy_secrets(self, secrets: WalletSecrets):
        kub_secrets = KubSecret(
            cd_mode=self.cd_mode,
            namespace=self.env_prefix,
            secret_name=REFERENCE_WALLET_KUB_SECRET_NAME,
            secret_key_value_pairs=asdict(secrets),
            update_strategy=SecretUpdateStrategy(SecretUpdateStrategy.MERGE)
        )
        kub_secrets.deploy()

        real_secrets = {secret: kub_secrets.outputs[secret] for secret in asdict(secrets)}
        return WalletSecrets(**real_secrets)

    def backend_deployable(self,
                           service_name,
                           liquidity_service_name,
                           command,
                           routes,
                           db_username,
                           db_password,
                           db_host,
                           db_port,
                           db_name_wallet,
                           redis_host,
                           redis_db,
                           vasp: Vasp,
                           worker_label_selector: WorkerLabelSelector,
                           env_vars=None):

        db_url_diem_reference_wallet = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name_wallet}'

        environment_variables = {
            'COMPOSE_ENV': 'production',
            'WALLET_PORT': 8080,
            'API_URL': f'https://{self.get_diem_wallet_hostname(vasp.chain)}/api',
            'REDIS_HOST': redis_host,
            'REDIS_DB': redis_db,
            'DB_URL': db_url_diem_reference_wallet,
            'VASP_ADDR': vasp.account_address_hex,
            'LIQUIDITY_SERVICE_HOST': liquidity_service_name,
            'LIQUIDITY_SERVICE_PORT': 8080,
            'WALLET_CUSTODY_ACCOUNT_NAME': 'wallet',
            'VASP_BASE_URL': vasp.base_url,
            'OFFCHAIN_SERVICE_PORT': 5091,
            'JSON_RPC_URL': vasp.chain.json_rpc_url,
            'CHAIN_ID': vasp.chain.value,
            'GAS_CURRENCY_CODE': CURRENCY,
        }
        if env_vars is not None:
            environment_variables.update(env_vars)

        docker_image = f"{ECR_HOST}/{WALLET_BACKEND_IMAGE_NAME}:{self.variables['build_tag']['value']}"

        return SimpleService(namespace=self.env_prefix,
                             service_name=service_name,
                             docker_image=docker_image,
                             command=command,
                             port=8080,
                             collect_telemetry=True,
                             routes=routes,
                             environment_variables=environment_variables,
                             secret_mappings=[
                                 SecretMapping(
                                     secret=WalletSecrets.get_backend_custodial_private_keys_secret_name(vasp.chain),
                                     set_to_env='CUSTODY_PRIVATE_KEYS'
                                 ),
                                 SecretMapping(
                                     secret=WalletSecrets.get_backend_compliance_private_key_secret_name(vasp.chain),
                                     set_to_env='VASP_COMPLIANCE_KEY'
                                 ),
                             ],
                             worker_selector=worker_label_selector)

    def liquidity_deployable(self,
                             service_name,
                             routes,
                             db_username,
                             db_password,
                             db_host,
                             db_port,
                             db_name_liquidity_provider,
                             worker_label_selector: WorkerLabelSelector,
                             liquidity_vasp_address,
                             chain: ChainType,
                             env_vars=None):
        db_url_lp = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name_liquidity_provider}'

        environment_variables = {
            'COMPOSE_ENV': 'production',
            'LP_DB_URL': db_url_lp,
            'LIQUIDITY_PORT': 8080,
            'LIQUIDITY_CUSTODY_ACCOUNT_NAME': 'liquidity',
            'JSON_RPC_URL': chain.json_rpc_url,
            'CHAIN_ID': chain.value,
        }
        if env_vars is not None:
            environment_variables.update(env_vars)

        secret_mappings = None
        if chain == ChainType.PREMAINNET:
            environment_variables['LIQUIDITY_VASP_ADDR'] = liquidity_vasp_address
            secret_mappings = [
                SecretMapping(
                    secret=f'{REFERENCE_WALLET_KUB_SECRET_NAME}.liquidity_custodial_private_keys',
                    set_to_env='CUSTODY_PRIVATE_KEYS'),
            ]

        return SimpleService(namespace=self.env_prefix,
                             service_name=service_name,
                             command=["/liquidity/run.sh"],
                             docker_image=f"{ECR_HOST}/{LIQUIDITY_IMAGE_NAME}:{self.variables['build_tag']['value']}",
                             port=8080,
                             collect_telemetry=True,
                             routes=routes,
                             environment_variables=environment_variables,
                             secret_mappings=secret_mappings,
                             worker_selector=worker_label_selector)

    def frontend_deployable(self, chain):
        return StaticResource(cd_mode=self.cd_mode,
                              env_prefix=self.env_prefix,
                              host=self.get_diem_wallet_hostname(chain),
                              path='/',
                              resources_dir='/frontend')

    def db_for_service_deployable(self, db_name, db_password):
        return PostgresDatabase(
            cd_mode=self.cd_mode,
            aws_region=self.region,
            db_host=self.outputs['PostgresInstance']['db_host'],
            db_port=self.outputs['PostgresInstance']['db_port'],
            master_username=self.outputs['PostgresInstance']['master_username'],
            master_password=self.outputs['PostgresInstance']['master_password'],
            db_name=db_name,
            db_username='drwuser',
            db_password=db_password,
        )

    def _deploy(self):
        secrets = self.deploy_secrets(WalletSecrets.generate())
        self.deploy_for_chain(ChainType.TESTNET, secrets)
        self.deploy_for_chain(ChainType.PREMAINNET, secrets)

    def deploy_for_chain(self, chain: ChainType, secrets: WalletSecrets):
        deployable_names = DeployableNames.create(chain, self.env_prefix)

        worker_type_label = self.outputs['EKS']['worker-type-label']['value']
        worker_tag = self.outputs['EKS']['worker-tag']['value']
        worker_label_selector = WorkerLabelSelector(worker_type_label, [worker_tag])

        wallet_hostname = self.get_diem_wallet_hostname(chain)
        offchain_url = f'https://{wallet_hostname}/api/offchain'

        backend_compliance_private_key = secrets.get_backend_compliance_private_key(chain)
        wallet_vasp = Vasp.create(
            chain=chain,
            private_key=secrets.get_backend_wallet_private_key(chain),
            base_url=offchain_url,
            compliance_private_key=backend_compliance_private_key,
        )

        wallet_vasp.rotate_dual_attestation_info()
        wallet_vasp.validate_attestation()

        liquidity_vasp_address = None
        if chain == ChainType.PREMAINNET:
            # Liquidity is a DD so no offchain related values
            liquidity_vasp = Vasp.create(
                chain=chain,
                private_key=secrets.liquidity_wallet_private_key,
                base_url=None,
                compliance_private_key=None,
            )
            liquidity_vasp.validate_account()
            liquidity_vasp_address = liquidity_vasp.account_address_hex

        redis_host = self.outputs['ElasticCacheRedis']['redis_host']['value']
        redis_db = 0 if chain == ChainType.TESTNET else 1

        # Wallet database
        wallet_db = self.db_for_service_deployable(deployable_names.web_backend_db, secrets.db_password)
        wallet_db_connection_params = dict(
            db_username=wallet_db.db_username,
            db_password=wallet_db.db_password,
            db_host=wallet_db.db_host,
            db_port=wallet_db.db_port,
            db_name_wallet=wallet_db.db_name,
        )
        wallet_db.deploy()

        # Liquidity provider database
        lp_db = self.db_for_service_deployable(deployable_names.liquidity_db, secrets.db_password)
        lp_db_connection_params = dict(
            db_username=lp_db.db_username,
            db_password=lp_db.db_password,
            db_host=lp_db.db_host,
            db_port=lp_db.db_port,
            db_name_liquidity_provider=lp_db.db_name,
        )
        lp_db.deploy()

        # web backend
        self.backend_deployable(service_name=deployable_names.web_backend_service,
                                liquidity_service_name=deployable_names.liquidity_service,
                                command=['/wallet/run_web.sh'],
                                routes=[
                                    Route(host=wallet_hostname, path='/api'),
                                ],
                                redis_host=redis_host,
                                redis_db=redis_db,
                                worker_label_selector=worker_label_selector,
                                vasp=wallet_vasp,
                                env_vars={'ADMIN_USERNAME': 'admin@diem'},
                                **wallet_db_connection_params).deploy()

        # dramatiq backend
        self.backend_deployable(service_name=deployable_names.dramatiq_service,
                                liquidity_service_name=deployable_names.liquidity_service,
                                command=['/wallet/run_worker.sh'],
                                routes=None,
                                redis_host=redis_host,
                                redis_db=redis_db,
                                vasp=wallet_vasp,
                                worker_label_selector=worker_label_selector,
                                env_vars={'PROCS': 10, 'THREADS': 10},
                                **wallet_db_connection_params).deploy()

        # pubsub backend
        self.backend_deployable(service_name=deployable_names.pubsub_service,
                                liquidity_service_name=deployable_names.liquidity_service,
                                command=['/wallet/run_pubsub.sh'],
                                routes=None,
                                redis_host=redis_host,
                                redis_db=redis_db,
                                vasp=wallet_vasp,
                                worker_label_selector=worker_label_selector,
                                **wallet_db_connection_params).deploy()

        # liquidity
        self.liquidity_deployable(service_name=deployable_names.liquidity_service,
                                  routes=None,
                                  worker_label_selector=worker_label_selector,
                                  liquidity_vasp_address=liquidity_vasp_address,
                                  chain=chain,
                                  **lp_db_connection_params).deploy()

        self.frontend_deployable(chain).deploy()

    def _destroy(self):
        pass
        # TODO: destroy


deployment_class = DiemReferenceWallet

if __name__ == '__main__':
    go_hyperspace(deployment_class)
