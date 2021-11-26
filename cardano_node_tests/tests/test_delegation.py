"""Tests for stake address registration and delegation."""
import logging
from pathlib import Path
from typing import List
from typing import Tuple

import allure
import pytest
from _pytest.tmpdir import TempdirFactory
from cardano_clusterlib import clusterlib

from cardano_node_tests.tests import delegation
from cardano_node_tests.utils import cluster_management
from cardano_node_tests.utils import cluster_nodes
from cardano_node_tests.utils import clusterlib_utils
from cardano_node_tests.utils import constants
from cardano_node_tests.utils import dbsync_utils
from cardano_node_tests.utils import helpers

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def create_temp_dir(tmp_path_factory: TempdirFactory):
    """Create a temporary dir."""
    p = Path(tmp_path_factory.getbasetemp()).joinpath(helpers.get_id_for_mktemp(__file__)).resolve()
    p.mkdir(exist_ok=True, parents=True)
    return p


@pytest.fixture
def temp_dir(create_temp_dir: Path):
    """Change to a temporary dir."""
    with helpers.change_cwd(create_temp_dir):
        yield create_temp_dir


# use the "temp_dir" fixture for all tests automatically
pytestmark = pytest.mark.usefixtures("temp_dir")


@pytest.fixture
def cluster_and_pool(
    cluster_manager: cluster_management.ClusterManager,
) -> Tuple[clusterlib.ClusterLib, str]:
    return delegation.cluster_and_pool(cluster_manager=cluster_manager)


@pytest.fixture
def cluster_use_pool1(cluster_manager: cluster_management.ClusterManager) -> clusterlib.ClusterLib:
    return cluster_manager.get(use_resources=[cluster_management.Resources.POOL1])


@pytest.fixture
def pool_users(
    cluster_manager: cluster_management.ClusterManager,
    cluster: clusterlib.ClusterLib,
) -> List[clusterlib.PoolUser]:
    """Create pool users."""
    with cluster_manager.cache_fixture() as fixture_cache:
        if fixture_cache.value:
            return fixture_cache.value  # type: ignore

        created_users = clusterlib_utils.create_pool_users(
            cluster_obj=cluster,
            name_template=f"test_delegation_pool_users_ci{cluster_manager.cluster_instance_num}",
            no_of_addr=2,
        )
        fixture_cache.value = created_users

    # fund source addresses
    clusterlib_utils.fund_from_faucet(
        created_users[0],
        cluster_obj=cluster,
        faucet_data=cluster_manager.cache.addrs_data["user1"],
    )

    return created_users


@pytest.fixture
def pool_users_disposable(
    cluster: clusterlib.ClusterLib,
) -> List[clusterlib.PoolUser]:
    """Create function scoped pool users."""
    pool_users = clusterlib_utils.create_pool_users(
        cluster_obj=cluster,
        name_template=f"test_delegation_pool_users_{clusterlib.get_rand_str(3)}",
        no_of_addr=2,
    )
    return pool_users


@pytest.mark.testnets
@pytest.mark.order(3)
class TestDelegateAddr:
    """Tests for address delegation to stake pools."""

    @allure.link(helpers.get_vcs_link())
    @pytest.mark.parametrize(
        "use_build_cmd",
        (
            False,
            pytest.param(
                True,
                marks=pytest.mark.skipif(
                    not constants.BUILD_USABLE, reason=constants.BUILD_SKIP_MSG
                ),
            ),
        ),
        ids=("build_raw", "build"),
    )
    @pytest.mark.dbsync
    def test_delegate_using_pool_id(
        self,
        cluster_manager: cluster_management.ClusterManager,
        cluster_and_pool: Tuple[clusterlib.ClusterLib, str],
        use_build_cmd: bool,
    ):
        """Submit registration certificate and delegate to pool using pool id.

        * register stake address and delegate it to pool
        * check that the stake address was delegated
        * (optional) check records in db-sync
        """
        cluster, pool_id = cluster_and_pool
        temp_template = f"{clusterlib_utils.get_temp_template(cluster)}_{use_build_cmd}"

        clusterlib_utils.wait_for_epoch_interval(
            cluster_obj=cluster, start=0, stop=-10, force_epoch=False
        )
        init_epoch = cluster.get_epoch()

        # submit registration certificate and delegate to pool
        delegation_out = delegation.delegate_stake_addr(
            cluster_obj=cluster,
            addrs_data=cluster_manager.cache.addrs_data,
            temp_template=temp_template,
            pool_id=pool_id,
            use_build_cmd=use_build_cmd,
        )

        tx_db_record = dbsync_utils.check_tx(
            cluster_obj=cluster, tx_raw_output=delegation_out.tx_raw_output
        )
        delegation.db_check_delegation(
            pool_user=delegation_out.pool_user,
            db_record=tx_db_record,
            deleg_epoch=init_epoch,
            pool_id=delegation_out.pool_id,
        )

    @allure.link(helpers.get_vcs_link())
    @pytest.mark.parametrize(
        "use_build_cmd",
        (
            False,
            pytest.param(
                True,
                marks=pytest.mark.skipif(
                    not constants.BUILD_USABLE, reason=constants.BUILD_SKIP_MSG
                ),
            ),
        ),
        ids=("build_raw", "build"),
    )
    @pytest.mark.dbsync
    @pytest.mark.skipif(
        cluster_nodes.get_cluster_type().type == cluster_nodes.ClusterType.TESTNET_NOPOOLS,
        reason="supposed to run on cluster with pools",
    )
    def test_delegate_using_vkey(
        self,
        cluster_manager: cluster_management.ClusterManager,
        cluster_use_pool1: clusterlib.ClusterLib,
        use_build_cmd: bool,
    ):
        """Submit registration certificate and delegate to pool using cold vkey.

        * register stake address and delegate it to pool
        * check that the stake address was delegated
        * (optional) check records in db-sync
        """
        pool_name = "node-pool1"
        cluster = cluster_use_pool1
        temp_template = f"{clusterlib_utils.get_temp_template(cluster)}_{use_build_cmd}"

        clusterlib_utils.wait_for_epoch_interval(
            cluster_obj=cluster, start=0, stop=-10, force_epoch=False
        )
        init_epoch = cluster.get_epoch()

        # submit registration certificate and delegate to pool
        node_cold = cluster_manager.cache.addrs_data[pool_name]["cold_key_pair"]
        delegation_out = delegation.delegate_stake_addr(
            cluster_obj=cluster,
            addrs_data=cluster_manager.cache.addrs_data,
            temp_template=temp_template,
            cold_vkey=node_cold.vkey_file,
            use_build_cmd=use_build_cmd,
        )

        tx_db_record = dbsync_utils.check_tx(
            cluster_obj=cluster, tx_raw_output=delegation_out.tx_raw_output
        )
        delegation.db_check_delegation(
            pool_user=delegation_out.pool_user,
            db_record=tx_db_record,
            deleg_epoch=init_epoch,
            pool_id=delegation_out.pool_id,
        )

    @allure.link(helpers.get_vcs_link())
    @pytest.mark.order(2)
    @pytest.mark.dbsync
    @pytest.mark.long
    def test_deregister(
        self,
        cluster_manager: cluster_management.ClusterManager,
        cluster_and_pool: Tuple[clusterlib.ClusterLib, str],
    ):
        """Deregister stake address.

        * submit registration certificate and delegate to pool
        * attempt to deregister the stake address - deregistration is expected to fail
          because there are rewards in the stake address
        * withdraw rewards to payment address and deregister stake address
        * check that the key deposit was returned and rewards withdrawn
        * check that the stake address is no longer delegated
        * (optional) check records in db-sync
        """
        cluster, pool_id = cluster_and_pool
        temp_template = clusterlib_utils.get_temp_template(cluster)

        clusterlib_utils.wait_for_epoch_interval(
            cluster_obj=cluster, start=0, stop=-10, force_epoch=False
        )
        init_epoch = cluster.get_epoch()

        # submit registration certificate and delegate to pool
        delegation_out = delegation.delegate_stake_addr(
            cluster_obj=cluster,
            addrs_data=cluster_manager.cache.addrs_data,
            temp_template=temp_template,
            pool_id=pool_id,
        )

        tx_db_deleg = dbsync_utils.check_tx(
            cluster_obj=cluster, tx_raw_output=delegation_out.tx_raw_output
        )
        delegation.db_check_delegation(
            pool_user=delegation_out.pool_user,
            db_record=tx_db_deleg,
            deleg_epoch=init_epoch,
            pool_id=delegation_out.pool_id,
        )

        clusterlib_utils.wait_for_stake_distribution(cluster)

        src_address = delegation_out.pool_user.payment.address

        LOGGER.info("Waiting up to 4 full epochs for first reward.")
        for i in range(5):
            if i > 0:
                cluster.wait_for_new_epoch(padding_seconds=10)
            if cluster.get_stake_addr_info(
                delegation_out.pool_user.stake.address
            ).reward_account_balance:
                break
        else:
            pytest.skip(f"User of pool '{pool_id}' hasn't received any rewards, cannot continue.")

        # make sure we have enough time to finish deregistration in one epoch
        clusterlib_utils.wait_for_epoch_interval(
            cluster_obj=cluster, start=0, stop=-40, force_epoch=False
        )

        # files for deregistering stake address
        stake_addr_dereg_cert = cluster.gen_stake_addr_deregistration_cert(
            addr_name=f"{temp_template}_addr0",
            stake_vkey_file=delegation_out.pool_user.stake.vkey_file,
        )
        tx_files_deregister = clusterlib.TxFiles(
            certificate_files=[stake_addr_dereg_cert],
            signing_key_files=[
                delegation_out.pool_user.payment.skey_file,
                delegation_out.pool_user.stake.skey_file,
            ],
        )

        # attempt to deregister the stake address - deregistration is expected to fail
        # because there are rewards in the stake address
        with pytest.raises(clusterlib.CLIError) as excinfo:
            cluster.send_tx(
                src_address=src_address,
                tx_name=f"{temp_template}_dereg_fail",
                tx_files=tx_files_deregister,
            )
        assert "StakeKeyNonZeroAccountBalanceDELEG" in str(excinfo.value)

        src_payment_balance = cluster.get_address_balance(src_address)
        reward_balance = cluster.get_stake_addr_info(
            delegation_out.pool_user.stake.address
        ).reward_account_balance

        # withdraw rewards to payment address, deregister stake address
        tx_raw_deregister_output = cluster.send_tx(
            src_address=src_address,
            tx_name=f"{temp_template}_dereg_withdraw",
            tx_files=tx_files_deregister,
            withdrawals=[
                clusterlib.TxOut(address=delegation_out.pool_user.stake.address, amount=-1)
            ],
        )

        # check that the key deposit was returned and rewards withdrawn
        assert (
            cluster.get_address_balance(src_address)
            == src_payment_balance
            - tx_raw_deregister_output.fee
            + reward_balance
            + cluster.get_address_deposit()
        ), f"Incorrect balance for source address `{src_address}`"

        # check that the stake address is no longer delegated
        stake_addr_info = cluster.get_stake_addr_info(delegation_out.pool_user.stake.address)
        assert (
            not stake_addr_info.delegation
        ), f"Stake address is still delegated: {stake_addr_info}"

        tx_db_dereg = dbsync_utils.check_tx(
            cluster_obj=cluster, tx_raw_output=tx_raw_deregister_output
        )
        if tx_db_dereg:
            assert delegation_out.pool_user.stake.address in tx_db_dereg.stake_deregistration

    @allure.link(helpers.get_vcs_link())
    @pytest.mark.parametrize(
        "use_build_cmd",
        (
            False,
            pytest.param(
                True,
                marks=pytest.mark.skipif(
                    not constants.BUILD_USABLE, reason=constants.BUILD_SKIP_MSG
                ),
            ),
        ),
        ids=("build_raw", "build"),
    )
    @pytest.mark.dbsync
    def test_addr_registration_deregistration(
        self,
        cluster: clusterlib.ClusterLib,
        pool_users: List[clusterlib.PoolUser],
        pool_users_disposable: List[clusterlib.PoolUser],
        use_build_cmd: bool,
    ):
        """Submit registration and deregistration certificates in single TX.

        * create stake address registration cert
        * create stake address deregistration cert
        * register and deregister stake address in single TX
        * check that the balance for source address was correctly updated and that key deposit
          was not needed
        * (optional) check records in db-sync
        """
        temp_template = f"{clusterlib_utils.get_temp_template(cluster)}_{use_build_cmd}"

        user_registered = pool_users_disposable[0]
        user_payment = pool_users[0].payment
        src_init_balance = cluster.get_address_balance(user_payment.address)

        # create stake address registration cert
        stake_addr_reg_cert_file = cluster.gen_stake_addr_registration_cert(
            addr_name=f"{temp_template}_addr0", stake_vkey_file=user_registered.stake.vkey_file
        )

        # create stake address deregistration cert
        stake_addr_dereg_cert = cluster.gen_stake_addr_deregistration_cert(
            addr_name=f"{temp_template}_addr0", stake_vkey_file=user_registered.stake.vkey_file
        )

        # register and deregister stake address in single TX
        tx_files = clusterlib.TxFiles(
            certificate_files=[stake_addr_reg_cert_file, stake_addr_dereg_cert],
            signing_key_files=[user_payment.skey_file, user_registered.stake.skey_file],
        )

        if use_build_cmd:
            tx_raw_output = cluster.build_tx(
                src_address=user_payment.address,
                tx_name=f"{temp_template}_reg_deleg",
                tx_files=tx_files,
                fee_buffer=2000_000,
                witness_override=len(tx_files.signing_key_files) * 2,
            )
            tx_signed = cluster.sign_tx(
                tx_body_file=tx_raw_output.out_file,
                signing_key_files=tx_files.signing_key_files,
                tx_name=f"{temp_template}_reg_deleg",
            )
            cluster.submit_tx(tx_file=tx_signed, txins=tx_raw_output.txins)
        else:
            tx_raw_output = cluster.send_tx(
                src_address=user_payment.address,
                tx_name=f"{temp_template}_reg_dereg",
                tx_files=tx_files,
            )

        # check that the balance for source address was correctly updated and that key deposit
        # was not needed
        assert (
            cluster.get_address_balance(user_payment.address)
            == src_init_balance - tx_raw_output.fee
        ), f"Incorrect balance for source address `{user_payment.address}`"

        tx_db_record = dbsync_utils.check_tx(cluster_obj=cluster, tx_raw_output=tx_raw_output)
        if tx_db_record:
            assert user_registered.stake.address in tx_db_record.stake_registration
            assert user_registered.stake.address in tx_db_record.stake_deregistration

    @allure.link(helpers.get_vcs_link())
    @pytest.mark.parametrize(
        "use_build_cmd",
        (
            False,
            pytest.param(
                True,
                marks=pytest.mark.skipif(
                    not constants.BUILD_USABLE, reason=constants.BUILD_SKIP_MSG
                ),
            ),
        ),
        ids=("build_raw", "build"),
    )
    @pytest.mark.dbsync
    def test_addr_delegation_deregistration(
        self,
        cluster_and_pool: Tuple[clusterlib.ClusterLib, str],
        pool_users: List[clusterlib.PoolUser],
        pool_users_disposable: List[clusterlib.PoolUser],
        use_build_cmd: bool,
    ):
        """Submit delegation and deregistration certificates in single TX.

        * create stake address registration cert
        * create stake address deregistration cert
        * register stake address
        * create stake address delegation cert
        * delegate and deregister stake address in single TX
        * check that the balance for source address was correctly updated and that the key
          deposit was returned
        * check that the stake address was NOT delegated
        * (optional) check records in db-sync
        """
        cluster, pool_id = cluster_and_pool
        temp_template = f"{clusterlib_utils.get_temp_template(cluster)}_{use_build_cmd}"

        user_registered = pool_users_disposable[0]
        user_payment = pool_users[0].payment
        src_init_balance = cluster.get_address_balance(user_payment.address)

        # create stake address registration cert
        stake_addr_reg_cert_file = cluster.gen_stake_addr_registration_cert(
            addr_name=f"{temp_template}_addr0", stake_vkey_file=user_registered.stake.vkey_file
        )

        # create stake address deregistration cert
        stake_addr_dereg_cert = cluster.gen_stake_addr_deregistration_cert(
            addr_name=f"{temp_template}_addr0", stake_vkey_file=user_registered.stake.vkey_file
        )

        # register stake address
        tx_files = clusterlib.TxFiles(
            certificate_files=[stake_addr_reg_cert_file],
            signing_key_files=[user_payment.skey_file],
        )
        tx_raw_output_reg = cluster.send_tx(
            src_address=user_payment.address,
            tx_name=f"{temp_template}_reg",
            tx_files=tx_files,
        )

        tx_db_reg = dbsync_utils.check_tx(cluster_obj=cluster, tx_raw_output=tx_raw_output_reg)
        if tx_db_reg:
            assert user_registered.stake.address in tx_db_reg.stake_registration

        # check that the balance for source address was correctly updated
        assert (
            cluster.get_address_balance(user_payment.address)
            == src_init_balance - tx_raw_output_reg.fee - cluster.get_address_deposit()
        ), f"Incorrect balance for source address `{user_payment.address}`"

        src_registered_balance = cluster.get_address_balance(user_payment.address)

        # create stake address delegation cert
        stake_addr_deleg_cert_file = cluster.gen_stake_addr_delegation_cert(
            addr_name=f"{temp_template}_addr0",
            stake_vkey_file=user_registered.stake.vkey_file,
            stake_pool_id=pool_id,
        )

        clusterlib_utils.wait_for_epoch_interval(
            cluster_obj=cluster, start=0, stop=-10, force_epoch=False
        )
        init_epoch = cluster.get_epoch()

        # delegate and deregister stake address in single TX
        tx_files = clusterlib.TxFiles(
            certificate_files=[stake_addr_deleg_cert_file, stake_addr_dereg_cert],
            signing_key_files=[user_payment.skey_file, user_registered.stake.skey_file],
        )

        if use_build_cmd:
            tx_raw_output_deleg = cluster.build_tx(
                src_address=user_payment.address,
                tx_name=f"{temp_template}_deleg_dereg",
                tx_files=tx_files,
                fee_buffer=2000_000,
                witness_override=len(tx_files.signing_key_files) * 2,
            )
            tx_signed = cluster.sign_tx(
                tx_body_file=tx_raw_output_deleg.out_file,
                signing_key_files=tx_files.signing_key_files,
                tx_name=f"{temp_template}_deleg_dereg",
            )
            cluster.submit_tx(tx_file=tx_signed, txins=tx_raw_output_deleg.txins)
        else:
            tx_raw_output_deleg = cluster.send_tx(
                src_address=user_payment.address,
                tx_name=f"{temp_template}_deleg_dereg",
                tx_files=tx_files,
            )

        # check that the balance for source address was correctly updated and that the key
        # deposit was returned
        assert (
            cluster.get_address_balance(user_payment.address)
            == src_registered_balance - tx_raw_output_deleg.fee + cluster.get_address_deposit()
        ), f"Incorrect balance for source address `{user_payment.address}`"

        clusterlib_utils.wait_for_stake_distribution(cluster)

        # check that the stake address was NOT delegated
        stake_addr_info = cluster.get_stake_addr_info(user_registered.stake.address)
        assert not stake_addr_info.delegation, f"Stake address was delegated: {stake_addr_info}"

        tx_db_deleg = dbsync_utils.check_tx(cluster_obj=cluster, tx_raw_output=tx_raw_output_deleg)
        if tx_db_deleg:
            assert user_registered.stake.address in tx_db_deleg.stake_deregistration
            assert user_registered.stake.address == tx_db_deleg.stake_delegation[0].address
            assert tx_db_deleg.stake_delegation[0].active_epoch_no == init_epoch + 2
            assert pool_id == tx_db_deleg.stake_delegation[0].pool_id


@pytest.mark.testnets
class TestNegative:
    """Tests that are expected to fail."""

    @allure.link(helpers.get_vcs_link())
    def test_registration_cert_with_wrong_key(
        self,
        cluster: clusterlib.ClusterLib,
        pool_users: List[clusterlib.PoolUser],
    ):
        """Try to generate stake address registration certificate using wrong stake vkey.

        Expect failure.
        """
        temp_template = clusterlib_utils.get_temp_template(cluster)

        # create stake address registration cert, use wrong stake vkey
        with pytest.raises(clusterlib.CLIError) as excinfo:
            cluster.gen_stake_addr_registration_cert(
                addr_name=f"{temp_template}_addr0", stake_vkey_file=pool_users[0].payment.vkey_file
            )
        assert "Expected: StakeVerificationKeyShelley" in str(excinfo.value)

    @allure.link(helpers.get_vcs_link())
    def test_delegation_cert_with_wrong_key(
        self,
        cluster_and_pool: Tuple[clusterlib.ClusterLib, str],
        pool_users: List[clusterlib.PoolUser],
    ):
        """Try to generate stake address delegation certificate using wrong stake vkey.

        Expect failure.
        """
        cluster, pool_id = cluster_and_pool
        temp_template = clusterlib_utils.get_temp_template(cluster)

        # create stake address delegation cert, use wrong stake vkey
        with pytest.raises(clusterlib.CLIError) as excinfo:
            cluster.gen_stake_addr_delegation_cert(
                addr_name=f"{temp_template}_addr0",
                stake_vkey_file=pool_users[0].payment.vkey_file,
                stake_pool_id=pool_id,
            )
        assert "Expected: StakeVerificationKeyShelley" in str(excinfo.value)

    @allure.link(helpers.get_vcs_link())
    def test_register_addr_with_wrong_key(
        self,
        cluster: clusterlib.ClusterLib,
        pool_users: List[clusterlib.PoolUser],
        pool_users_disposable: List[clusterlib.PoolUser],
    ):
        """Try to register stake address using wrong payment skey.

        Expect failure.
        """
        temp_template = clusterlib_utils.get_temp_template(cluster)

        user_registered = pool_users_disposable[0]
        user_payment = pool_users[0].payment

        # create stake address registration cert
        stake_addr_reg_cert_file = cluster.gen_stake_addr_registration_cert(
            addr_name=f"{temp_template}_addr0", stake_vkey_file=user_registered.stake.vkey_file
        )

        # register stake address, use wrong payment skey
        tx_files = clusterlib.TxFiles(
            certificate_files=[stake_addr_reg_cert_file],
            signing_key_files=[pool_users[1].payment.skey_file],
        )

        with pytest.raises(clusterlib.CLIError) as excinfo:
            cluster.send_tx(
                src_address=user_payment.address, tx_name=temp_template, tx_files=tx_files
            )
        assert "MissingVKeyWitnessesUTXOW" in str(excinfo.value)

    @allure.link(helpers.get_vcs_link())
    def test_delegate_addr_with_wrong_key(
        self,
        cluster_and_pool: Tuple[clusterlib.ClusterLib, str],
        pool_users: List[clusterlib.PoolUser],
        pool_users_disposable: List[clusterlib.PoolUser],
    ):
        """Try to delegate stake address using wrong payment skey.

        Expect failure.
        """
        cluster, pool_id = cluster_and_pool
        temp_template = clusterlib_utils.get_temp_template(cluster)

        user_registered = pool_users_disposable[0]
        user_payment = pool_users[0].payment

        # create stake address registration cert
        stake_addr_reg_cert_file = cluster.gen_stake_addr_registration_cert(
            addr_name=f"{temp_template}_addr0", stake_vkey_file=user_registered.stake.vkey_file
        )

        # register stake address
        tx_files = clusterlib.TxFiles(
            certificate_files=[stake_addr_reg_cert_file],
            signing_key_files=[user_payment.skey_file],
        )
        cluster.send_tx(
            src_address=user_payment.address, tx_name=f"{temp_template}_reg", tx_files=tx_files
        )

        # create stake address delegation cert
        stake_addr_deleg_cert_file = cluster.gen_stake_addr_delegation_cert(
            addr_name=f"{temp_template}_addr0",
            stake_vkey_file=user_registered.stake.vkey_file,
            stake_pool_id=pool_id,
        )

        # delegate stake address, use wrong payment skey
        tx_files = clusterlib.TxFiles(
            certificate_files=[stake_addr_deleg_cert_file],
            signing_key_files=[pool_users[1].payment.skey_file],
        )

        with pytest.raises(clusterlib.CLIError) as excinfo:
            cluster.send_tx(
                src_address=user_payment.address,
                tx_name=f"{temp_template}_deleg",
                tx_files=tx_files,
            )
        assert "MissingVKeyWitnessesUTXOW" in str(excinfo.value)

    @allure.link(helpers.get_vcs_link())
    @pytest.mark.parametrize(
        "use_build_cmd",
        (
            False,
            pytest.param(
                True,
                marks=pytest.mark.skipif(
                    not constants.BUILD_USABLE, reason=constants.BUILD_SKIP_MSG
                ),
            ),
        ),
        ids=("build_raw", "build"),
    )
    def test_delegate_unregistered_addr(
        self,
        cluster_and_pool: Tuple[clusterlib.ClusterLib, str],
        pool_users: List[clusterlib.PoolUser],
        pool_users_disposable: List[clusterlib.PoolUser],
        use_build_cmd: bool,
    ):
        """Try to delegate unregistered stake address.

        Expect failure.
        """
        cluster, pool_id = cluster_and_pool
        temp_template = f"{clusterlib_utils.get_temp_template(cluster)}_{use_build_cmd}"

        user_registered = pool_users_disposable[0]
        user_payment = pool_users[0].payment

        # create stake address delegation cert
        stake_addr_deleg_cert_file = cluster.gen_stake_addr_delegation_cert(
            addr_name=f"{temp_template}_addr0",
            stake_vkey_file=user_registered.stake.vkey_file,
            stake_pool_id=pool_id,
        )

        # delegate unregistered stake address
        tx_files = clusterlib.TxFiles(
            certificate_files=[stake_addr_deleg_cert_file],
            signing_key_files=[user_payment.skey_file],
        )

        with pytest.raises(clusterlib.CLIError) as excinfo:
            if use_build_cmd:
                tx_raw_output = cluster.build_tx(
                    src_address=user_payment.address,
                    tx_name=f"{temp_template}_deleg_unreg",
                    tx_files=tx_files,
                    fee_buffer=2000_000,
                    witness_override=len(tx_files.signing_key_files) * 2,
                )
                tx_signed = cluster.sign_tx(
                    tx_body_file=tx_raw_output.out_file,
                    signing_key_files=tx_files.signing_key_files,
                    tx_name=f"{temp_template}_deleg_unreg",
                )
                cluster.submit_tx(tx_file=tx_signed, txins=tx_raw_output.txins)
            else:
                cluster.send_tx(
                    src_address=user_payment.address,
                    tx_name=f"{temp_template}_deleg_unreg",
                    tx_files=tx_files,
                )
        assert "StakeDelegationImpossibleDELEG" in str(excinfo.value)

    @allure.link(helpers.get_vcs_link())
    @pytest.mark.parametrize(
        "use_build_cmd",
        (
            False,
            pytest.param(
                True,
                marks=pytest.mark.skipif(
                    not constants.BUILD_USABLE, reason=constants.BUILD_SKIP_MSG
                ),
            ),
        ),
        ids=("build_raw", "build"),
    )
    def test_deregister_not_registered_addr(
        self,
        cluster: clusterlib.ClusterLib,
        pool_users: List[clusterlib.PoolUser],
        pool_users_disposable: List[clusterlib.PoolUser],
        use_build_cmd: bool,
    ):
        """Deregister not registered stake address."""
        temp_template = f"{clusterlib_utils.get_temp_template(cluster)}_{use_build_cmd}"

        user_registered = pool_users_disposable[0]
        user_payment = pool_users[0].payment

        # files for deregistering stake address
        stake_addr_dereg_cert = cluster.gen_stake_addr_deregistration_cert(
            addr_name=f"{temp_template}_addr0", stake_vkey_file=user_registered.stake.vkey_file
        )
        tx_files = clusterlib.TxFiles(
            certificate_files=[stake_addr_dereg_cert],
            signing_key_files=[user_payment.skey_file, user_registered.stake.skey_file],
        )

        with pytest.raises(clusterlib.CLIError) as excinfo:
            if use_build_cmd:
                tx_raw_output = cluster.build_tx(
                    src_address=user_payment.address,
                    tx_name=f"{temp_template}_dereg_fail",
                    tx_files=tx_files,
                    fee_buffer=2000_000,
                    witness_override=len(tx_files.signing_key_files) * 2,
                )
                tx_signed = cluster.sign_tx(
                    tx_body_file=tx_raw_output.out_file,
                    signing_key_files=tx_files.signing_key_files,
                    tx_name=f"{temp_template}_dereg_fail",
                )
                cluster.submit_tx(tx_file=tx_signed, txins=tx_raw_output.txins)
            else:
                cluster.send_tx(
                    src_address=user_payment.address,
                    tx_name=f"{temp_template}_dereg_fail",
                    tx_files=tx_files,
                )
        assert "StakeKeyNonZeroAccountBalanceDELEG" in str(excinfo.value)