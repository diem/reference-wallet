import json
import time
from dataclasses import dataclass, asdict
from secrets import token_bytes

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from diem import jsonrpc, testnet, LocalAccount, utils, diem_types, stdlib
from jwcrypto import jwk
from jwcrypto.common import base64url_encode
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
WALLET_BACKEND_SERVICE_NAME = 'diem-reference-wallet-backend'
LIQUIDITY_SERVICE_NAME = 'diem-reference-wallet-liquidity'

CHAIN_ID = testnet.CHAIN_ID.to_int()
JSON_RPC_URL = testnet.JSON_RPC_URL
CURRENCY = 'XUS'


def get_account_from_private_key(private_key) -> LocalAccount:
    return LocalAccount(Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key)))


class ComplianceKey:
    def __init__(self, key):
        self._key = key

    def get_public(self):
        return self._key.get_op_key('verify')

    def get_private(self):
        return self._key.get_op_key('sign')

    @staticmethod
    def generate():
        key = jwk.JWK.generate(kty='OKP', crv='Ed25519')
        return ComplianceKey(key)

    @staticmethod
    def from_str(data):
        key = jwk.JWK(**json.loads(data))
        return ComplianceKey(key)

    @staticmethod
    def from_pub_bytes(pub_key_data):
        key = jwk.JWK(
            kty='OKP',
            crv='Ed25519',
            x=base64url_encode(pub_key_data)
        )
        return ComplianceKey(key)

    def export_pub(self):
        return self._key.export_public()

    def export_full(self):
        return self._key.export_private()


@dataclass
class WalletSecrets:
    db_password: str
    backend_custodial_private_keys: str
    backend_wallet_private_key: str
    backend_compliance_private_key: str
    liquidity_custodial_private_keys: str
    liquidity_wallet_private_key: str

    @classmethod
    def generate(cls):
        db_password = passwords.generate_pg_password(18)
        backend_custodial_private_key = token_bytes(32).hex()
        liquidity_custodial_private_key = token_bytes(32).hex()
        backend_compliance_private_key = ComplianceKey.generate().export_full()

        return cls(
            db_password=db_password,
            backend_custodial_private_keys='{"wallet":"' + backend_custodial_private_key + '"}',
            backend_wallet_private_key=backend_custodial_private_key,
            backend_compliance_private_key=backend_compliance_private_key,
            liquidity_custodial_private_keys='{"liquidity":"' + liquidity_custodial_private_key + '"}',
            liquidity_wallet_private_key=liquidity_custodial_private_key,
        )


class Vasp:
    def __init__(self, private_key, base_url, compliance_private_key):
        self.api = jsonrpc.Client(JSON_RPC_URL)
        self.faucet = testnet.Faucet(self.api)

        self.account = get_account_from_private_key(private_key)
        self.base_url = base_url
        self.compliance_key = ComplianceKey.from_str(compliance_private_key)

    @classmethod
    def create(cls, private_key, base_url, compliance_private_key):
        vasp = cls(private_key, base_url, compliance_private_key)
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
        return utils.public_key_bytes(self.compliance_key.get_public())

    @property
    def compliance_private_key_str(self) -> str:
        return self.compliance_key.export_full()

    def ensure_account(self):
        logger.info(f'Creating and initialize the blockchain account {self.account_address_hex}')
        account_info = self.api.get_account(self.account.account_address)
        if not account_info:
            self.mint(1_000_000, CURRENCY)

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
            chain_id=diem_types.ChainId.from_int(CHAIN_ID),
        )
        signed_tx = self.account.sign(tx)

        self.api.submit(signed_tx)
        self.api.wait_for_transaction(signed_tx)
        logger.info(f'Rotated dual attestation for account {self.account_address_hex}')


class DiemReferenceWallet(Deployment):
    def __init__(self, config: DeploymentConfig):
        super().__init__(config)

        self.variables['build_tag'] = {'description': 'Official Diem Reference wallet build tag for all components'}
        self.depends_on = [EKS, IngressController, PostgresInstance, ElasticCacheRedis]

    def get_diem_wallet_hostname(self):
        domains: DomainRepository = self.outputs['IngressController']['domains']
        application_name = 'diem-reference-wallet'
        diem_reference_wallet_hostname = domains.get_mapped_domain(Subsystem.DEMO, application_name)
        return diem_reference_wallet_hostname

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
                           command,
                           routes,
                           db_username,
                           db_password,
                           db_host,
                           db_port,
                           db_name_wallet,
                           redis_host,
                           vasp: Vasp,
                           worker_label_selector: WorkerLabelSelector,
                           env_vars=None):

        db_url_diem_reference_wallet = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name_wallet}'

        environment_variables = {
            'COMPOSE_ENV': 'production',
            'WALLET_PORT': 8080,
            'API_URL': f'https://{self.get_diem_wallet_hostname()}/api',
            'REDIS_HOST': redis_host,
            'DB_URL': db_url_diem_reference_wallet,
            'VASP_ADDR': vasp.account_address_hex,
            'LIQUIDITY_SERVICE_HOST': LIQUIDITY_SERVICE_NAME,
            'LIQUIDITY_SERVICE_PORT': 8080,
            'WALLET_CUSTODY_ACCOUNT_NAME': 'wallet',
            'VASP_BASE_URL': vasp.base_url,
            'OFFCHAIN_SERVICE_PORT': 5091,
            'JSON_RPC_URL': JSON_RPC_URL,
            'CHAIN_ID': CHAIN_ID,
            'GAS_CURRENCY_CODE': CURRENCY,
        }
        if env_vars is not None:
            environment_variables.update(env_vars)

        return SimpleService(namespace=self.env_prefix,
                             service_name=service_name,
                             docker_image=f"{ECR_HOST}/{WALLET_BACKEND_SERVICE_NAME}:{self.variables['build_tag']['value']}",
                             command=command,
                             port=8080,
                             collect_telemetry=True,
                             routes=routes,
                             environment_variables=environment_variables,
                             secret_mappings=[
                                 SecretMapping(
                                     secret=f'{REFERENCE_WALLET_KUB_SECRET_NAME}.backend_custodial_private_keys',
                                     set_to_env='CUSTODY_PRIVATE_KEYS'
                                 ),
                                 SecretMapping(
                                     secret=f'{REFERENCE_WALLET_KUB_SECRET_NAME}.backend_compliance_private_key',
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
                             liquidity_vasp_auth_key,
                             worker_label_selector: WorkerLabelSelector,
                             env_vars=None):
        db_url_lp = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name_liquidity_provider}'

        environment_variables = {
            'COMPOSE_ENV': 'production',
            'ADMIN_USERNAME': 'admin@diem',
            'LP_DB_URL': db_url_lp,
            'LIQUIDITY_PORT': 8080,
            'LIQUIDITY_CUSTODY_ACCOUNT_NAME': 'liquidity',
            'ACCOUNT_WATCHER_AUTH_KEY': liquidity_vasp_auth_key,
            'JSON_RPC_URL': JSON_RPC_URL,
            'CHAIN_ID': CHAIN_ID,
        }
        if env_vars is not None:
            environment_variables.update(env_vars)

        return SimpleService(namespace=self.env_prefix,
                             service_name=service_name,
                             command=["/liquidity/run.sh"],
                             docker_image=f"{ECR_HOST}/{LIQUIDITY_SERVICE_NAME}:{self.variables['build_tag']['value']}",
                             port=8080,
                             collect_telemetry=True,
                             routes=routes,
                             environment_variables=environment_variables,
                             secret_mappings=[
                                 SecretMapping(
                                     secret=f'{REFERENCE_WALLET_KUB_SECRET_NAME}.liquidity_custodial_private_keys',
                                     set_to_env='CUSTODY_PRIVATE_KEYS'),
                             ],
                             worker_selector=worker_label_selector)

    def frontend_deployable(self):
        return StaticResource(cd_mode=self.cd_mode,
                              env_prefix=self.env_prefix,
                              host=self.get_diem_wallet_hostname(),
                              path='/',
                              resources_dir='/frontend')

    def _deploy(self):
        worker_type_label = self.outputs['EKS']['worker-type-label']['value']
        worker_tag = self.outputs['EKS']['worker-tag']['value']
        worker_label_selector = WorkerLabelSelector(worker_type_label, [worker_tag])

        wallet_secrets = WalletSecrets.generate()
        secrets = self.deploy_secrets(wallet_secrets)

        wallet_vasp = Vasp.create(
            private_key=secrets.backend_wallet_private_key,
            base_url=self.get_diem_wallet_hostname(),  # FIXME: Should be fixed to use offchain
            compliance_private_key=secrets.backend_compliance_private_key,
        )

        if wallet_secrets.backend_compliance_private_key == secrets.backend_compliance_private_key:
            # means it's a new compliance key, needs to be rotated in the blockchain!
            wallet_vasp.rotate_dual_attestation_info()

        # Liquidity is not a real VASP at this moment, so the attestation info is not
        # used and contains dummy values
        liquidity_vasp = Vasp.create(
            private_key=secrets.liquidity_wallet_private_key,
            base_url="UNUSED",
            compliance_private_key=ComplianceKey.generate().export_full(),
        )
        liquidity_vasp.mint(99 * 1_000_000, CURRENCY)

        db_host = self.outputs['PostgresInstance']['db_host']
        db_port = self.outputs['PostgresInstance']['db_port']
        master_username = self.outputs['PostgresInstance']['master_username']
        master_password = self.outputs['PostgresInstance']['master_password']
        db_name_wallet = f'{self.env_prefix}_diem_reference_wallet'
        db_name_liquidity_provider = f'{self.env_prefix}_lp'
        db_username = 'drwuser'
        db_password = secrets.db_password

        redis_host = self.outputs['ElasticCacheRedis']['redis_host']['value']

        db_config = {
            "cd_mode": self.cd_mode,
            "aws_region": self.region,
            "db_host": db_host,
            "db_port": db_port,
            "master_username": master_username,
            "master_password": master_password,
            "db_name": db_name_wallet,
            "db_username": db_username,
            "db_password": db_password
        }

        # Wallet database
        database = PostgresDatabase(**db_config)
        database.deploy()

        # Liquidity provider database
        db_config["db_name"] = db_name_liquidity_provider
        lp_database = PostgresDatabase(**db_config)
        lp_database.deploy()

        # web backend
        self.backend_deployable(service_name=f'{WALLET_BACKEND_SERVICE_NAME}-web',
                                command=['/wallet/run_web.sh'],
                                routes=[Route(host=self.get_diem_wallet_hostname(), path='/api')],
                                db_username=db_username,
                                db_password=db_password,
                                db_host=db_host,
                                db_port=db_port,
                                db_name_wallet=db_name_wallet,
                                redis_host=redis_host,
                                worker_label_selector=worker_label_selector,
                                vasp=wallet_vasp,
                                env_vars={'ADMIN_USERNAME': 'admin@diem'}).deploy()

        # dramatiq backend
        self.backend_deployable(service_name=f'{WALLET_BACKEND_SERVICE_NAME}-dramatiq',
                                command=['/wallet/run_worker.sh'],
                                routes=None,
                                db_username=db_username,
                                db_password=db_password,
                                db_host=db_host,
                                db_port=db_port,
                                db_name_wallet=db_name_wallet,
                                redis_host=redis_host,
                                vasp=wallet_vasp,
                                worker_label_selector=worker_label_selector,
                                env_vars={'PROCS': 10, 'THREADS': 10}).deploy()

        # pubsub backend
        self.backend_deployable(service_name=f'{WALLET_BACKEND_SERVICE_NAME}-pubsub',
                                command=['/wallet/run_pubsub.sh'],
                                routes=None,
                                db_username=db_username,
                                db_password=db_password,
                                db_host=db_host,
                                db_port=db_port,
                                db_name_wallet=db_name_wallet,
                                redis_host=redis_host,
                                vasp=wallet_vasp,
                                worker_label_selector=worker_label_selector).deploy()

        # liquidity
        self.liquidity_deployable(service_name=LIQUIDITY_SERVICE_NAME,
                                  routes=None,
                                  db_username=db_username,
                                  db_password=db_password,
                                  db_host=db_host,
                                  db_port=db_port,
                                  db_name_liquidity_provider=db_name_liquidity_provider,
                                  liquidity_vasp_auth_key=liquidity_vasp.auth_key_hex,
                                  worker_label_selector=worker_label_selector).deploy()

        self.frontend_deployable().deploy()

    def _destroy(self):
        pass
        # TODO: destroy


deployment_class = DiemReferenceWallet

if __name__ == '__main__':
    go_hyperspace(deployment_class)
