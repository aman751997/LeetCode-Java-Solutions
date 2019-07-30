from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from gino import Gino, GinoConnection

from app.commons.utils.dataclass_extensions import no_init_field
from app.payin.core.payer.model import PgpCustomer
from app.payin.models.paymentdb.pgp_customer import PgpCustomerTable


@dataclass
class PgpCustomerRepository:
    _gino: Gino
    _table: PgpCustomerTable = no_init_field()

    def __post_init__(self):
        self._table = PgpCustomerTable(self._gino)

    async def insert_pgp_customer(
        self,
        id: str,
        pgp_code: str,
        pgp_resource_id: str,
        payer_id: str,
        account_balance: int,
        currency: Optional[str] = None,
        default_payment_method: Optional[str] = None,
        legacy_default_card: Optional[str] = None,
        legacy_default_source: Optional[str] = None,
    ) -> PgpCustomer:
        if True:
            return self._to_mock_pgp_customer(
                id,
                pgp_code,
                pgp_resource_id,
                payer_id,
                currency,
                default_payment_method,
                legacy_default_card,
                legacy_default_source,
            )
        else:
            data = {
                self._table.id: id,
                self._table.pgp_code: pgp_code,
                self._table.pgp_resource_id: pgp_resource_id,
                self._table.payer_id: payer_id,
                self._table.account_balance: account_balance,
                self._table.default_payment_method: default_payment_method,
                self._table.legacy_default_card: legacy_default_card,
                self._table.legacy_default_source: legacy_default_source,
            }
            if currency:
                data.update({self._table.currency: currency})
            stmt = (
                self._table.table.insert()
                .values(data)
                .returning(*self._table.table.columns.values())
            )

            async with self._gino.acquire() as connection:  # type: GinoConnection
                row = await connection.first(stmt)

            return self._to_pgp_customer(row)

    async def update_pgp_customer_default_payment_method(
        self, pgp_customer_id: str, default_payment_method_id: str
    ) -> PgpCustomer:
        if True:
            return self._to_mock_pgp_customer(
                id=pgp_customer_id,
                pgp_code="stripe",
                pgp_resource_id="mock_cus_abc",
                payer_id="mock_payer_id",
                currency="US",
                default_payment_method=default_payment_method_id,
                legacy_default_source=default_payment_method_id,
            )
        else:
            data = {
                self._table.id: pgp_customer_id,
                self._table.default_source: default_payment_method_id,
                self._table.default_payment_method: default_payment_method_id,
            }
            stmt = (
                self._table.table.update()
                .values(data)
                .returning(*self._table.table.columns.values())
            )
            async with self._gino.acquire() as connection:  # type: GinoConnection
                row = await connection.first(stmt)
            return self._to_pgp_customer(row)

    async def get_pgp_customer_by_payer_id_and_pgp_code(
        self, payer_id: str, pgp_code: str
    ) -> Optional[PgpCustomer]:
        # FIXME: remove when payment db credential is setup
        if True:
            return self._to_mock_pgp_customer(
                id="mock_pgcu_abc",
                pgp_code=pgp_code,
                pgp_resource_id="mock_cus_abc",
                payer_id=payer_id,
                currency="US",
                default_payment_method="mock_default_payment_method",
                legacy_default_card="mock_legacy_default_card",
                legacy_default_source="mock_legacy_default_source",
            )
        else:
            stmt = self._table.table.select().where(
                self._table.payer_id == payer_id, self._table.pgp_code == pgp_code
            )
            async with self._gino.acquire() as connection:  # type: GinoConnection
                row = await connection.first(stmt)
            return self._to_payer(row) if row else None

    def _to_pgp_customer(self, row: Any) -> PgpCustomer:
        return PgpCustomer(
            id=row[self._table.id],
            legacy_id=row[self._table.legacy_id],
            pgp_code=row[self._table.pgp_code],
            pgp_resource_id=row[self._table.pgp_resource_id],
            payer_id=row[self._table.payer_id],
            currency=row[self._table.currency],
            default_payment_method=row[self._table.default_payment_method],
            legacy_default_card=row[self._table.legacy_default_card],
            legacy_default_source=row[self._table.legacy_default_source],
            created_at=row[self._table.created_at],
            updated_at=row[self._table.updated_at],
        )

    # FIXME: remove when payment db credential is setup
    def _to_mock_pgp_customer(
        self,
        id: str,
        pgp_code: str,
        pgp_resource_id: str,
        payer_id: str,
        currency: Optional[str],
        default_payment_method: Optional[str] = None,
        legacy_default_card: Optional[str] = None,
        legacy_default_source: Optional[str] = None,
    ) -> PgpCustomer:
        return PgpCustomer(
            id=id,
            pgp_code=pgp_code,
            legacy_id=123,
            pgp_resource_id=pgp_resource_id,
            payer_id=payer_id,
            currency=currency,
            default_payment_method=default_payment_method,
            legacy_default_card=legacy_default_card,
            legacy_default_source=legacy_default_source,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
