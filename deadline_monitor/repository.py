"""Read-only access to the orders database."""

import logging
from collections.abc import Sequence

import psycopg2
from psycopg2.extras import NamedTupleCursor

from deadline_monitor.domain import OpenOrder, PendingOperation

logger = logging.getLogger(__name__)

# Status numbers from core/fixtures/statuses.json.
ORDER_STATUSES_IN_PROGRESS = (1, 2, 3)  # sent for work order, work order created, in work
OPERATION_STATUS_DONE = 3

# One round trip for the whole picture. Duration follows Operation.get_exec_time:
# fixed time + per-item time * work amount, at minute precision.
OPEN_ORDERS_QUERY = """
    SELECT
        o.id AS order_id,
        o.deadline,
        os.number AS status_number,
        COALESCE(c.name, '') AS customer_name,
        w.id AS work_id,
        (
            EXTRACT(HOUR FROM ot.fixed_exec_time) * 60 + EXTRACT(MINUTE FROM ot.fixed_exec_time)
            + (EXTRACT(HOUR FROM ot.exec_time_per_item) * 60 + EXTRACT(MINUTE FROM ot.exec_time_per_item)) * w.amount
        )::int AS duration_minutes
    FROM orders_order o
    JOIN orders_orderstatus os ON os.id = o.status_id
    LEFT JOIN accounts_customer c ON c.id = o.customer_id
    LEFT JOIN works_work w ON w.order_id = o.id AND w.is_active
    LEFT JOIN operations_operation op ON op.work_id = w.id AND op.is_active
        AND NOT EXISTS (
            SELECT 1 FROM operations_operationstatus s
            WHERE s.id = op.operation_status_id AND s.number = %(done)s
        )
    LEFT JOIN operations_operationtype ot ON ot.id = op.operation_type_id
    WHERE o.is_active AND os.number = ANY(%(statuses)s)
    ORDER BY o.deadline, o.id, w.id, op.ordinal_number
"""


class OrderRepository:
    def __init__(self, connection_params: dict):
        self._connection_params = connection_params
        self._connection = None

    def fetch_open_orders(self, statuses: Sequence[int] = ORDER_STATUSES_IN_PROGRESS) -> list[OpenOrder]:
        for attempt in (1, 2):
            try:
                rows = self._query(statuses)
                break
            except (psycopg2.OperationalError, psycopg2.InterfaceError):
                # A connection kept between runs may have been closed by the server: reconnect once.
                self._close()
                if attempt == 2:
                    raise
                logger.warning("Database connection lost, reconnecting")
        return self._group(rows)

    def _query(self, statuses: Sequence[int]) -> list:
        with self._get_connection().cursor() as cursor:
            cursor.execute(OPEN_ORDERS_QUERY, {"done": OPERATION_STATUS_DONE, "statuses": list(statuses)})
            return cursor.fetchall()

    def _get_connection(self):
        if self._connection is None or self._connection.closed:
            connection = psycopg2.connect(cursor_factory=NamedTupleCursor, **self._connection_params)
            # The monitor never writes: make that a property of the session, not a convention.
            connection.set_session(readonly=True, autocommit=True)
            self._connection = connection
        return self._connection

    def _close(self) -> None:
        if self._connection is not None:
            try:
                self._connection.close()
            except psycopg2.Error:
                pass
            self._connection = None

    @staticmethod
    def _group(rows: list) -> list[OpenOrder]:
        orders: dict[str, dict] = {}
        for row in rows:
            order = orders.setdefault(
                row.order_id,
                {
                    "deadline": row.deadline,
                    "status_number": row.status_number,
                    "customer_name": row.customer_name,
                    "operations": [],
                },
            )
            if row.duration_minutes is not None:
                order["operations"].append(PendingOperation(row.work_id, row.duration_minutes))
        return [
            OpenOrder(
                id=order_id,
                deadline=data["deadline"],
                status_number=data["status_number"],
                customer_name=data["customer_name"],
                operations=tuple(data["operations"]),
            )
            for order_id, data in orders.items()
        ]
