from typing import Dict

from soda.execution.check import Check
from soda.execution.check_outcome import CheckOutcome
from soda.execution.metric import Metric
from soda.execution.user_defined_failed_rows_metric import UserDefinedFailedRowsMetric

KEY_FAILED_ROWS_COUNT = "failed_rows_count"


class UserDefinedFailedRowsCheck(Check):
    """
    Eg:

    checks:
      - "Customers must have size":
          failed rows query: |
            SELECT *
            FROM {table_name}
            WHERE size < 0
    """

    def __init__(
        self, check_cfg: "UserDefinedFailedRowsCheckCfg", data_source_scan: "DataSourceScan", partition: "Partition"
    ):
        super().__init__(
            check_cfg=check_cfg,
            data_source_scan=data_source_scan,
            partition=partition,
            column=None,
            name="user-defined-failed-rows",
            identity_parts=check_cfg.get_identity_parts(),
        )

        from soda.sodacl.user_defined_failed_rows_check_cfg import (
            UserDefinedFailedRowsCheckCfg,
        )

        check_cfg: UserDefinedFailedRowsCheckCfg = self.check_cfg

        metric = UserDefinedFailedRowsMetric(
            data_source_scan=self.data_source_scan,
            check_name=check_cfg.source_line,
            query=check_cfg.query,
            check=self,
        )
        metric = self.data_source_scan.resolve_metric(metric)
        self.metrics[KEY_FAILED_ROWS_COUNT] = metric

    def evaluate(self, metrics: Dict[str, Metric], historic_values: Dict[str, object]):
        metric = metrics.get(KEY_FAILED_ROWS_COUNT)
        failed_row_count: int = metric.value

        self.outcome = CheckOutcome.PASS
        if failed_row_count > 0:
            self.outcome = CheckOutcome.FAIL

        self.failed_rows_storage_ref = metric.failed_rows_storage_ref
