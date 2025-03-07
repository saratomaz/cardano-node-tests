"""SECP256k1 tests for minting with Plutus using `transaction build-raw`."""

import logging
import pathlib as pl
import re
import typing as tp

import allure
import pytest
from cardano_clusterlib import clusterlib

from cardano_node_tests.cluster_management import cluster_management
from cardano_node_tests.tests import common
from cardano_node_tests.tests import plutus_common
from cardano_node_tests.tests.tests_plutus_v2 import mint_raw
from cardano_node_tests.utils import helpers

LOGGER = logging.getLogger(__name__)

pytestmark = [
    common.SKIPIF_PLUTUSV2_UNUSABLE,
    pytest.mark.plutus,
]


@pytest.fixture
def payment_addrs(
    cluster_manager: cluster_management.ClusterManager,
    cluster: clusterlib.ClusterLib,
) -> list[clusterlib.AddressRecord]:
    """Create new payment address."""
    addrs = common.get_payment_addrs(
        name_template=common.get_test_id(cluster),
        cluster_manager=cluster_manager,
        cluster_obj=cluster,
        num=2,
        fund_idx=[0],
        amount=3_000_000_000,
    )
    return addrs


class TestSECP256k1:
    def _fund_issuer_mint_token(
        self,
        cluster_obj: clusterlib.ClusterLib,
        temp_template: str,
        payment_addrs: list[clusterlib.AddressRecord],
        script_file: pl.Path,
        redeemer_file: pl.Path,
    ):
        """Fund the token issuer and mint a token."""
        __: tp.Any  # mypy workaround
        payment_addr = payment_addrs[0]
        issuer_addr = payment_addrs[1]

        lovelace_amount = 2_000_000
        token_amount = 5
        fee_txsize = 600_000

        minting_cost = plutus_common.compute_cost(
            execution_cost=plutus_common.MINTING_V2_REF_COST,
            protocol_params=cluster_obj.g_query.get_protocol_params(),
        )

        mint_utxos, collateral_utxos, __, __ = mint_raw._fund_issuer(
            cluster_obj=cluster_obj,
            temp_template=temp_template,
            payment_addr=payment_addr,
            issuer_addr=issuer_addr,
            minting_cost=minting_cost,
            amount=lovelace_amount,
            fee_txsize=fee_txsize,
        )

        policyid = cluster_obj.g_transaction.get_policyid(script_file)
        asset_name = f"qacoin{clusterlib.get_rand_str(4)}".encode().hex()
        token = f"{policyid}.{asset_name}"
        mint_txouts = [
            clusterlib.TxOut(address=issuer_addr.address, amount=token_amount, coin=token)
        ]

        plutus_mint_data = [
            clusterlib.Mint(
                txouts=mint_txouts,
                script_file=script_file,
                collaterals=collateral_utxos,
                execution_units=(
                    plutus_common.MINTING_V2_REF_COST.per_time,
                    plutus_common.MINTING_V2_REF_COST.per_space,
                ),
                redeemer_file=redeemer_file,
                policyid=policyid,
            )
        ]

        tx_files_step2 = clusterlib.TxFiles(
            signing_key_files=[issuer_addr.skey_file],
        )
        txouts_step2 = [
            clusterlib.TxOut(address=issuer_addr.address, amount=lovelace_amount),
            *mint_txouts,
        ]

        tx_raw_output_step2 = cluster_obj.g_transaction.build_raw_tx_bare(
            out_file=f"{temp_template}_step2_tx.body",
            txins=mint_utxos,
            txouts=txouts_step2,
            mint=plutus_mint_data,
            tx_files=tx_files_step2,
            fee=minting_cost.fee + fee_txsize,
        )

        tx_signed_step2 = cluster_obj.g_transaction.sign_tx(
            tx_body_file=tx_raw_output_step2.out_file,
            signing_key_files=tx_files_step2.signing_key_files,
            tx_name=f"{temp_template}_step2",
        )

        cluster_obj.g_transaction.submit_tx(tx_file=tx_signed_step2, txins=mint_utxos)

        out_utxos = cluster_obj.g_query.get_utxo(tx_raw_output=tx_raw_output_step2)
        token_utxo = clusterlib.filter_utxos(
            utxos=out_utxos, address=issuer_addr.address, coin=token
        )
        assert token_utxo and token_utxo[0].amount == token_amount, "The token was not minted"

        common.check_missing_utxos(cluster_obj=cluster_obj, utxos=out_utxos)

    @allure.link(helpers.get_vcs_link())
    @common.PARAM_PLUTUS2ONWARDS_VERSION
    @pytest.mark.parametrize("algorithm", ("ecdsa", "schnorr"))
    @pytest.mark.smoke
    @pytest.mark.testnets
    def test_use_secp_builtin_functions(
        self,
        cluster: clusterlib.ClusterLib,
        payment_addrs: list[clusterlib.AddressRecord],
        algorithm: str,
        plutus_version: str,
    ):
        """Test that is possible to use the two SECP256k1 builtin functions.

        * fund the token issuer
        * mint the tokens using a Plutus script with a SECP256k1 function
        * check that the token was minted
        """
        temp_template = common.get_test_id(cluster)

        script_file = (
            plutus_common.MINTING_SECP256K1_ECDSA[plutus_version]
            if algorithm == "ecdsa"
            else plutus_common.MINTING_SECP256K1_SCHNORR[plutus_version]
        )

        redeemer_dir = (
            plutus_common.SEPC256K1_ECDSA_DIR
            if algorithm == "ecdsa"
            else plutus_common.SEPC256K1_SCHNORR_DIR
        )

        redeemer_file = redeemer_dir / "positive.redeemer"

        try:
            self._fund_issuer_mint_token(
                cluster_obj=cluster,
                temp_template=temp_template,
                payment_addrs=payment_addrs,
                script_file=script_file,
                redeemer_file=redeemer_file,
            )
        except clusterlib.CLIError as err:
            plutus_common.xfail_on_secp_error(
                cluster_obj=cluster, algorithm=algorithm, err_msg=str(err)
            )
            raise

    @allure.link(helpers.get_vcs_link())
    @common.PARAM_PLUTUS2ONWARDS_VERSION
    @pytest.mark.parametrize(
        "test_vector",
        ("invalid_sig", "invalid_pubkey", "no_msg", "no_pubkey", "no_sig"),
    )
    @pytest.mark.parametrize("algorithm", ("ecdsa", "schnorr"))
    @pytest.mark.smoke
    @pytest.mark.testnets
    def test_negative_secp_builtin_functions(
        self,
        cluster: clusterlib.ClusterLib,
        payment_addrs: list[clusterlib.AddressRecord],
        test_vector: str,
        algorithm: str,
        plutus_version: str,
    ):
        """Try to mint a token with invalid test vectors.

        Expect failure.
        """
        temp_template = common.get_test_id(cluster)

        script_file = (
            plutus_common.MINTING_SECP256K1_ECDSA[plutus_version]
            if algorithm == "ecdsa"
            else plutus_common.MINTING_SECP256K1_SCHNORR[plutus_version]
        )

        redeemer_dir = (
            plutus_common.SEPC256K1_ECDSA_DIR
            if algorithm == "ecdsa"
            else plutus_common.SEPC256K1_SCHNORR_DIR
        )

        redeemer_file = redeemer_dir / f"{test_vector}.redeemer"

        before_pv8 = cluster.g_query.get_protocol_params()["protocolVersion"]["major"] < 8

        with pytest.raises(clusterlib.CLIError) as excinfo:
            self._fund_issuer_mint_token(
                cluster_obj=cluster,
                temp_template=temp_template,
                payment_addrs=payment_addrs,
                script_file=script_file,
                redeemer_file=redeemer_file,
            )

        err_msg = str(excinfo.value)

        # Before protocol version 8 the SECP256k1 is blocked.
        # After that the usage is limited by high cost model.
        is_forbidden = "MalformedScriptWitnesses" in err_msg

        is_overspending = (
            "The machine terminated part way through evaluation due to "
            "overspending the budget." in err_msg
        )

        # From protocol version 8 the SECP256k1 functions are allowed
        decoding_error = rf"Caused by: \(?verify{algorithm.capitalize()}Secp256k1Signature"

        validation_error = (
            "The machine terminated because of an error, "
            "either from a built-in function or from an explicit use of 'error'."
        )

        expected_error_messages = {
            "invalid_sig": validation_error,
            "invalid_pubkey": validation_error,
            "no_msg": decoding_error if algorithm == "ecdsa" else validation_error,
            "no_pubkey": decoding_error,
            "no_sig": decoding_error,
        }

        if before_pv8:
            assert is_forbidden or is_overspending, err_msg
        else:
            assert re.search(expected_error_messages[test_vector], err_msg), err_msg
            # Assert expected_error_messages[test_vector] in err_msg, err_msg
