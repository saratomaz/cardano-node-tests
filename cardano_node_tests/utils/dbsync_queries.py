"""SQL queries to db-sync database."""
import contextlib
import decimal
from typing import Any
from typing import Generator
from typing import Iterator
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Sequence
from typing import Tuple

import psycopg2

from cardano_node_tests.utils import dbsync_conn


class PoolDataDBRow(NamedTuple):
    id: int
    hash: memoryview
    view: str
    cert_index: int
    vrf_key_hash: memoryview
    pledge: int
    reward_addr: memoryview
    active_epoch_no: int
    meta_id: int
    margin: decimal.Decimal
    fixed_cost: int
    registered_tx_id: int
    metadata_url: str
    metadata_hash: memoryview
    owner_stake_address_id: int
    owner: memoryview
    ipv4: str
    ipv6: str
    dns_name: str
    port: int
    retire_cert_index: int
    retire_announced_tx_id: int
    retiring_epoch: int


class TxDBRow(NamedTuple):
    tx_id: int
    tx_hash: memoryview
    block_id: int
    block_index: int
    out_sum: decimal.Decimal
    fee: decimal.Decimal
    deposit: int
    size: int
    invalid_before: Optional[decimal.Decimal]
    invalid_hereafter: Optional[decimal.Decimal]
    tx_out_id: int
    tx_out_tx_id: int
    utxo_ix: int
    tx_out_addr: str
    tx_out_value: decimal.Decimal
    metadata_count: int
    reserve_count: int
    treasury_count: int
    pot_transfer_count: int
    stake_reg_count: int
    stake_dereg_count: int
    stake_deleg_count: int
    withdrawal_count: int
    collateral_count: int
    script_count: int
    redeemer_count: int
    ma_tx_out_id: Optional[int]
    ma_tx_out_policy: Optional[memoryview]
    ma_tx_out_name: Optional[memoryview]
    ma_tx_out_quantity: Optional[decimal.Decimal]
    ma_tx_mint_id: Optional[int]
    ma_tx_mint_policy: Optional[memoryview]
    ma_tx_mint_name: Optional[memoryview]
    ma_tx_mint_quantity: Optional[decimal.Decimal]


class MetadataDBRow(NamedTuple):
    id: int
    key: decimal.Decimal
    json: Any
    bytes: memoryview
    tx_id: int


class ADAStashDBRow(NamedTuple):
    id: int
    addr_view: str
    cert_index: int
    amount: decimal.Decimal
    tx_id: int


class PotTransferDBRow(NamedTuple):
    id: int
    cert_index: int
    treasury: decimal.Decimal
    reserves: decimal.Decimal
    tx_id: int


class StakeAddrDBRow(NamedTuple):
    id: int
    view: str
    tx_id: int


class StakeDelegDBRow(NamedTuple):
    tx_id: int
    active_epoch_no: Optional[int]
    pool_id: Optional[str]
    address: Optional[str]


class WithdrawalDBRow(NamedTuple):
    tx_id: int
    address: str
    amount: int


class TxInDBRow(NamedTuple):
    tx_out_id: int
    utxo_ix: int
    address: str
    value: decimal.Decimal
    tx_hash: memoryview
    ma_tx_out_id: Optional[int]
    ma_tx_out_policy: Optional[memoryview]
    ma_tx_out_name: Optional[memoryview]
    ma_tx_out_quantity: Optional[decimal.Decimal]


class CollateralTxInDBRow(NamedTuple):
    tx_out_id: int
    utxo_ix: int
    address: str
    value: decimal.Decimal
    tx_hash: memoryview


class ScriptDBRow(NamedTuple):
    id: int
    tx_id: int
    hash: memoryview
    type: str
    serialised_size: Optional[int]


class RedeemerDBRow(NamedTuple):
    id: int
    tx_id: int
    unit_mem: int
    unit_steps: int
    fee: int
    purpose: str
    script_hash: memoryview


class ADAPotsDBRow(NamedTuple):
    id: int
    slot_no: int
    epoch_no: int
    treasury: decimal.Decimal
    reserves: decimal.Decimal
    rewards: decimal.Decimal
    utxo: decimal.Decimal
    deposits: decimal.Decimal
    fees: decimal.Decimal
    block_id: int


class RewardDBRow(NamedTuple):
    address: str
    type: str
    amount: decimal.Decimal
    earned_epoch: int
    spendable_epoch: int
    pool_id: str


class BlockDBRow(NamedTuple):
    id: int
    epoch_no: Optional[int]
    slot_no: Optional[int]
    epoch_slot_no: Optional[int]
    block_no: Optional[int]
    previous_id: Optional[int]


class SchemaVersionStages(NamedTuple):
    one: int
    two: int
    three: int


@contextlib.contextmanager
def execute(query: str, vars: Sequence = ()) -> Iterator[psycopg2.extensions.cursor]:
    # pylint: disable=redefined-builtin
    try:
        cur = dbsync_conn.DBSync.conn().cursor()

        try:
            cur.execute(query, vars)
            conn_alive = True
        except psycopg2.Error:
            conn_alive = False

        if not conn_alive:
            cur = dbsync_conn.DBSync.reconn().cursor()
            cur.execute(query, vars)

        yield cur
    finally:
        cur.close()


class SchemaVersion:
    """Query and cache db-sync schema version."""

    _stages: Optional[SchemaVersionStages] = None

    @classmethod
    def stages(cls) -> SchemaVersionStages:
        if cls._stages is not None:
            return cls._stages

        query = (
            "SELECT stage_one, stage_two, stage_three "
            "FROM schema_version ORDER BY id DESC LIMIT 1;"
        )

        with execute(query=query) as cur:
            cls._stages = SchemaVersionStages(*cur.fetchone())

        return cls._stages


def query_tx(txhash: str) -> Generator[TxDBRow, None, None]:
    """Query a transaction in db-sync."""
    schema_stages = SchemaVersion.stages()
    # TODO: old schema, remove when no longer needed
    if schema_stages.one == 9 and schema_stages.two > 19:
        query = (
            "SELECT"
            " tx.id, tx.hash, tx.block_id, tx.block_index, tx.out_sum, tx.fee, tx.deposit, tx.size,"
            " tx.invalid_before, tx.invalid_hereafter,"
            " tx_out.id, tx_out.tx_id, tx_out.index, tx_out.address, tx_out.value,"
            " (SELECT COUNT(id) FROM tx_metadata WHERE tx_id=tx.id) AS metadata_count,"
            " (SELECT COUNT(id) FROM reserve WHERE tx_id=tx.id) AS reserve_count,"
            " (SELECT COUNT(id) FROM treasury WHERE tx_id=tx.id) AS treasury_count,"
            " (SELECT COUNT(id) FROM pot_transfer WHERE tx_id=tx.id) AS pot_transfer_count,"
            " (SELECT COUNT(id) FROM stake_registration WHERE tx_id=tx.id) AS reg_count,"
            " (SELECT COUNT(id) FROM stake_deregistration WHERE tx_id=tx.id) AS dereg_count,"
            " (SELECT COUNT(id) FROM delegation WHERE tx_id=tx.id) AS deleg_count,"
            " (SELECT COUNT(id) FROM withdrawal WHERE tx_id=tx.id) AS withdrawal_count,"
            " (SELECT COUNT(id) FROM collateral_tx_in WHERE tx_in_id=tx.id) AS collateral_count,"
            " (SELECT COUNT(id) FROM script WHERE tx_id=tx.id) AS script_count,"
            " (SELECT COUNT(id) FROM redeemer WHERE tx_id=tx.id) AS redeemer_count,"
            " ma_tx_out.id, ma_tx_out.policy, ma_tx_out.name, ma_tx_out.quantity,"
            " ma_tx_mint.id, ma_tx_mint.policy, ma_tx_mint.name, ma_tx_mint.quantity "
            "FROM tx "
            "LEFT JOIN tx_out ON tx.id = tx_out.tx_id "
            "LEFT JOIN ma_tx_out ON tx_out.id = ma_tx_out.tx_out_id "
            "LEFT JOIN ma_tx_mint ON tx.id = ma_tx_mint.tx_id "
            "WHERE tx.hash = %s;"
        )
    else:
        query = (
            "SELECT"
            " tx.id, tx.hash, tx.block_id, tx.block_index, tx.out_sum, tx.fee, tx.deposit, tx.size,"
            " tx.invalid_before, tx.invalid_hereafter,"
            " tx_out.id, tx_out.tx_id, tx_out.index, tx_out.address, tx_out.value,"
            " (SELECT COUNT(id) FROM tx_metadata WHERE tx_id=tx.id) AS metadata_count,"
            " (SELECT COUNT(id) FROM reserve WHERE tx_id=tx.id) AS reserve_count,"
            " (SELECT COUNT(id) FROM treasury WHERE tx_id=tx.id) AS treasury_count,"
            " (SELECT COUNT(id) FROM pot_transfer WHERE tx_id=tx.id) AS pot_transfer_count,"
            " (SELECT COUNT(id) FROM stake_registration WHERE tx_id=tx.id) AS reg_count,"
            " (SELECT COUNT(id) FROM stake_deregistration WHERE tx_id=tx.id) AS dereg_count,"
            " (SELECT COUNT(id) FROM delegation WHERE tx_id=tx.id) AS deleg_count,"
            " (SELECT COUNT(id) FROM withdrawal WHERE tx_id=tx.id) AS withdrawal_count,"
            " (SELECT COUNT(id) FROM collateral_tx_in WHERE tx_in_id=tx.id) AS collateral_count,"
            " (SELECT COUNT(id) FROM script WHERE tx_id=tx.id) AS script_count,"
            " (SELECT COUNT(id) FROM redeemer WHERE tx_id=tx.id) AS redeemer_count,"
            " ma_tx_out.id, join_ma_out.policy, join_ma_out.name, ma_tx_out.quantity,"
            " ma_tx_mint.id, join_ma_mint.policy, join_ma_mint.name, ma_tx_mint.quantity "
            "FROM tx "
            "LEFT JOIN tx_out ON tx.id = tx_out.tx_id "
            "LEFT JOIN ma_tx_out ON tx_out.id = ma_tx_out.tx_out_id "
            "LEFT JOIN ma_tx_mint ON tx.id = ma_tx_mint.tx_id "
            "LEFT JOIN multi_asset join_ma_out ON ma_tx_out.ident = join_ma_out.id "
            "LEFT JOIN multi_asset join_ma_mint ON ma_tx_mint.ident = join_ma_mint.id "
            "WHERE tx.hash = %s;"
        )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield TxDBRow(*result)


def query_tx_ins(txhash: str) -> Generator[TxInDBRow, None, None]:
    """Query transaction txins in db-sync."""
    schema_stages = SchemaVersion.stages()
    # TODO: old schema, remove when no longer needed
    if schema_stages.one == 9 and schema_stages.two > 19:
        query = (
            "SELECT"
            " tx_out.id, tx_out.index, tx_out.address, tx_out.value,"
            " (SELECT hash FROM tx WHERE id = tx_out.tx_id) AS tx_hash,"
            " ma_tx_out.id, ma_tx_out.policy, ma_tx_out.name, ma_tx_out.quantity "
            "FROM tx_in "
            "LEFT JOIN tx_out "
            "ON (tx_out.tx_id = tx_in.tx_out_id AND tx_out.index = tx_in.tx_out_index) "
            "LEFT JOIN tx ON tx.id = tx_in.tx_in_id "
            "LEFT JOIN ma_tx_out ON tx_out.id = ma_tx_out.tx_out_id "
            "WHERE tx.hash = %s;"
        )
    else:
        query = (
            "SELECT"
            " tx_out.id, tx_out.index, tx_out.address, tx_out.value,"
            " (SELECT hash FROM tx WHERE id = tx_out.tx_id) AS tx_hash,"
            " ma_tx_out.id, join_ma_out.policy, join_ma_out.name, ma_tx_out.quantity "
            "FROM tx_in "
            "LEFT JOIN tx_out "
            "ON (tx_out.tx_id = tx_in.tx_out_id AND tx_out.index = tx_in.tx_out_index) "
            "LEFT JOIN tx ON tx.id = tx_in.tx_in_id "
            "LEFT JOIN ma_tx_out ON tx_out.id = ma_tx_out.tx_out_id "
            "LEFT JOIN multi_asset join_ma_out ON ma_tx_out.ident = join_ma_out.id "
            "WHERE tx.hash = %s;"
        )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield TxInDBRow(*result)


def query_collateral_tx_ins(txhash: str) -> Generator[CollateralTxInDBRow, None, None]:
    """Query transaction collateral txins in db-sync."""
    query = (
        "SELECT"
        " tx_out.id, tx_out.index, tx_out.address, tx_out.value,"
        " (SELECT hash FROM tx WHERE id = tx_out.tx_id) AS tx_hash "
        "FROM collateral_tx_in "
        "LEFT JOIN tx_out "
        "ON (tx_out.tx_id = collateral_tx_in.tx_out_id AND"
        "    tx_out.index = collateral_tx_in.tx_out_index) "
        "LEFT JOIN tx ON tx.id = collateral_tx_in.tx_in_id "
        "WHERE tx.hash = %s;"
    )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield CollateralTxInDBRow(*result)


def query_plutus_scripts(txhash: str) -> Generator[ScriptDBRow, None, None]:
    """Query transaction plutus scripts in db-sync."""
    query = (
        "SELECT"
        " script.id, script.tx_id, script.hash, script.type, script.serialised_size "
        "FROM script "
        "LEFT JOIN tx ON tx.id = script.tx_id "
        "WHERE tx.hash = %s;"
    )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield ScriptDBRow(*result)


def query_redeemers(txhash: str) -> Generator[RedeemerDBRow, None, None]:
    """Query transaction redeemers in db-sync."""
    query = (
        "SELECT"
        " redeemer.id, redeemer.tx_id, redeemer.unit_mem, redeemer.unit_steps, redeemer.fee,"
        " redeemer.purpose, redeemer.script_hash "
        "FROM redeemer "
        "LEFT JOIN tx ON tx.id = redeemer.tx_id "
        "WHERE tx.hash = %s;"
    )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield RedeemerDBRow(*result)


def query_tx_metadata(txhash: str) -> Generator[MetadataDBRow, None, None]:
    """Query transaction metadata in db-sync."""
    query = (
        "SELECT"
        " tx_metadata.id, tx_metadata.key, tx_metadata.json, tx_metadata.bytes,"
        " tx_metadata.tx_id "
        "FROM tx_metadata "
        "INNER JOIN tx ON tx.id = tx_metadata.tx_id "
        "WHERE tx.hash = %s;"
    )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield MetadataDBRow(*result)


def query_tx_reserve(txhash: str) -> Generator[ADAStashDBRow, None, None]:
    """Query transaction reserve record in db-sync."""
    query = (
        "SELECT"
        " reserve.id, stake_address.view, reserve.cert_index, reserve.amount, reserve.tx_id "
        "FROM reserve "
        "INNER JOIN stake_address ON reserve.addr_id = stake_address.id "
        "INNER JOIN tx ON tx.id = reserve.tx_id "
        "WHERE tx.hash = %s;"
    )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield ADAStashDBRow(*result)


def query_tx_treasury(txhash: str) -> Generator[ADAStashDBRow, None, None]:
    """Query transaction treasury record in db-sync."""
    query = (
        "SELECT"
        " treasury.id, stake_address.view, treasury.cert_index,"
        " treasury.amount, treasury.tx_id "
        "FROM treasury "
        "INNER JOIN stake_address ON treasury.addr_id = stake_address.id "
        "INNER JOIN tx ON tx.id = treasury.tx_id "
        "WHERE tx.hash = %s;"
    )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield ADAStashDBRow(*result)


def query_tx_pot_transfers(txhash: str) -> Generator[PotTransferDBRow, None, None]:
    """Query transaction MIR certificate records in db-sync."""
    query = (
        "SELECT"
        " pot_transfer.id, pot_transfer.cert_index, pot_transfer.treasury,"
        " pot_transfer.reserves, pot_transfer.tx_id "
        "FROM pot_transfer "
        "INNER JOIN tx ON tx.id = pot_transfer.tx_id "
        "WHERE tx.hash = %s;"
    )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield PotTransferDBRow(*result)


def query_tx_stake_reg(txhash: str) -> Generator[StakeAddrDBRow, None, None]:
    """Query stake registration record in db-sync."""
    query = (
        "SELECT"
        " stake_registration.addr_id, stake_address.view, stake_registration.tx_id "
        "FROM stake_registration "
        "INNER JOIN stake_address ON stake_registration.addr_id = stake_address.id "
        "INNER JOIN tx ON tx.id = stake_registration.tx_id "
        "WHERE tx.hash = %s;"
    )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield StakeAddrDBRow(*result)


def query_tx_stake_dereg(txhash: str) -> Generator[StakeAddrDBRow, None, None]:
    """Query stake deregistration record in db-sync."""
    query = (
        "SELECT"
        " stake_deregistration.addr_id, stake_address.view, stake_deregistration.tx_id "
        "FROM stake_deregistration "
        "INNER JOIN stake_address ON stake_deregistration.addr_id = stake_address.id "
        "INNER JOIN tx ON tx.id = stake_deregistration.tx_id "
        "WHERE tx.hash = %s;"
    )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield StakeAddrDBRow(*result)


def query_tx_stake_deleg(txhash: str) -> Generator[StakeDelegDBRow, None, None]:
    """Query stake registration record in db-sync."""
    query = (
        "SELECT"
        " tx.id, delegation.active_epoch_no, pool_hash.view AS pool_view,"
        " stake_address.view AS address_view "
        "FROM delegation "
        "INNER JOIN stake_address ON delegation.addr_id = stake_address.id "
        "INNER JOIN tx ON tx.id = delegation.tx_id "
        "INNER JOIN pool_hash ON pool_hash.id = delegation.pool_hash_id "
        "WHERE tx.hash = %s;"
    )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield StakeDelegDBRow(*result)


def query_tx_withdrawal(txhash: str) -> Generator[WithdrawalDBRow, None, None]:
    """Query reward withdrawal record in db-sync."""
    query = (
        "SELECT"
        " tx.id, stake_address.view, amount "
        "FROM withdrawal "
        "INNER JOIN stake_address ON withdrawal.addr_id = stake_address.id "
        "INNER JOIN tx ON tx.id = withdrawal.tx_id "
        "WHERE tx.hash = %s;"
    )

    with execute(query=query, vars=(rf"\x{txhash}",)) as cur:
        while (result := cur.fetchone()) is not None:
            yield WithdrawalDBRow(*result)


def query_ada_pots(
    epoch_from: int = 0, epoch_to: int = 99999999
) -> Generator[ADAPotsDBRow, None, None]:
    """Query ADA pots record in db-sync."""
    query = (
        "SELECT"
        " id, slot_no, epoch_no, treasury, reserves, rewards, utxo, deposits, fees, block_id "
        "FROM ada_pots "
        "WHERE epoch_no BETWEEN %s AND %s;"
    )

    with execute(query=query, vars=(epoch_from, epoch_to)) as cur:
        while (result := cur.fetchone()) is not None:
            yield ADAPotsDBRow(*result)


def query_address_reward(
    address: str, epoch_from: int = 0, epoch_to: int = 99999999
) -> Generator[RewardDBRow, None, None]:
    """Query reward records for stake address in db-sync."""
    query = (
        "SELECT"
        " stake_address.view, reward.type, reward.amount, reward.earned_epoch,"
        " reward.spendable_epoch, pool_hash.view AS pool_view "
        "FROM reward "
        "INNER JOIN stake_address ON reward.addr_id = stake_address.id "
        "INNER JOIN pool_hash ON pool_hash.id = reward.pool_id "
        "WHERE (stake_address.view = %s) AND (reward.spendable_epoch BETWEEN %s AND %s);"
    )

    with execute(query=query, vars=(address, epoch_from, epoch_to)) as cur:
        while (result := cur.fetchone()) is not None:
            yield RewardDBRow(*result)


def query_pool_data(pool_id_bech32: str) -> Generator[PoolDataDBRow, None, None]:
    """Query pool data record in db-sync."""
    query = (
        "SELECT DISTINCT"
        " pool_hash.id, pool_hash.hash_raw, pool_hash.view,"
        " pool_update.cert_index, pool_update.vrf_key_hash, pool_update.pledge,"
        " pool_update.reward_addr, pool_update.active_epoch_no, pool_update.meta_id,"
        " pool_update.margin, pool_update.fixed_cost, pool_update.registered_tx_id,"
        " pool_metadata_ref.url as metadata_url,pool_metadata_ref.hash AS metadata_hash,"
        " pool_owner.addr_id AS owner_stake_address_id,"
        " stake_address.hash_raw AS owner,"
        " pool_relay.ipv4, pool_relay.ipv6, pool_relay.dns_name, pool_relay.port,"
        " pool_retire.cert_index AS retire_cert_index,"
        " pool_retire.announced_tx_id AS retire_announced_tx_id, pool_retire.retiring_epoch "
        "FROM pool_hash "
        "INNER JOIN pool_update ON pool_hash.id=pool_update.hash_id "
        "FULL JOIN pool_metadata_ref ON pool_update.meta_id=pool_metadata_ref.id "
        "INNER JOIN pool_owner ON pool_hash.id=pool_owner.pool_hash_id "
        "FULL JOIN pool_relay ON pool_update.id=pool_relay.update_id "
        "FULL JOIN pool_retire ON pool_hash.id=pool_retire.hash_id "
        "INNER JOIN stake_address ON pool_owner.addr_id=stake_address.id "
        "WHERE pool_hash.view = %s ORDER BY registered_tx_id;"
    )

    with execute(query=query, vars=(pool_id_bech32,)) as cur:
        while (result := cur.fetchone()) is not None:
            yield PoolDataDBRow(*result)


def query_blocks(
    epoch_from: int = 0, epoch_to: int = 99999999
) -> Generator[BlockDBRow, None, None]:
    """Query block records in db-sync."""
    query = (
        "SELECT"
        " id, epoch_no, slot_no, epoch_slot_no, block_no, previous_id "
        "FROM block "
        "WHERE (epoch_no BETWEEN %s AND %s);"
    )

    with execute(query=query, vars=(epoch_from, epoch_to)) as cur:
        while (result := cur.fetchone()) is not None:
            yield BlockDBRow(*result)


def query_table_names() -> List[str]:
    """Query table names in db-sync."""
    query = (
        "SELECT tablename "
        "FROM pg_catalog.pg_tables "
        "WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema' "
        "ORDER BY tablename ASC;"
    )

    with execute(query=query) as cur:
        results: List[Tuple[str]] = cur.fetchall()
        table_names = [r[0] for r in results]
        return table_names
