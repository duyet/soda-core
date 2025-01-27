import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set

from soda.scan import Scan
from soda.soda_cloud.soda_cloud import SodaCloud

logger = logging.getLogger(__name__)


class TimeGenerator:
    def __init__(
        self,
        timestamp: datetime = datetime.now(),
        timedelta: timedelta = timedelta(days=-1),
    ):
        self.timestamp = timestamp
        self.timedelta = timedelta

    def next(self):
        self.timestamp += self.timedelta
        return self.timestamp


class MockSodaCloud(SodaCloud):
    def __init__(self):
        super().__init__(host="test_host", api_key_id="test_api_key", api_key_secret="test_api_key_secret")
        self.historic_metric_values: list = []

    def create_soda_cloud(self):
        return self

    def send_scan_results(self, scan: Scan):
        pass
        # scan_results = self.build_scan_results(scan)
        # logger.debug(f"  # Sending to Soda Cloud:\n\n{to_yaml_str(scan_results)}")

    def mock_historic_values(self, metric_identity: str, metric_values: list, time_generator=TimeGenerator()):
        """
        To learn the metric_identity: fill in any string, check the error log and capture the metric_identity from there
        """
        historic_metric_values = [
            {"identity": metric_identity, "value": v, "data_time": time_generator.next()} for v in metric_values
        ]
        self.add_historic_metric_values(historic_metric_values)

    def add_historic_metric_values(self, historic_metric_values: List[Dict[str, object]]):
        """
        Each historic metric value is a dict like this:
            {'data_time': time_generator.next(),
             'metric': metric,
             'value': v
            }
        """
        self.historic_metric_values.extend(historic_metric_values)

    def get(self, historic_query):
        pass

    def get_historic_data(self, historic_descriptors: Set["HistoricDescriptor"]):
        historic_data = {}

        for historic_descriptor in historic_descriptors:
            historic_data[historic_descriptor] = self.__get_historic_data(historic_descriptor)

        return historic_data

    def __get_historic_data(self, historic_descriptor):
        if historic_descriptor.change_over_time_cfg:
            change_over_time_aggregation = historic_descriptor.change_over_time_cfg.last_aggregation
            if change_over_time_aggregation in ["avg", "min", "max"]:
                historic_metric_values = self.__get_historic_metric_values(historic_descriptor.metric)

                max_historic_values = historic_descriptor.change_over_time_cfg.last_measurements

                if max_historic_values < len(historic_metric_values):
                    historic_metric_values = historic_metric_values[:max_historic_values]

                historic_values = [historic_metric_value["value"] for historic_metric_value in historic_metric_values]

                if change_over_time_aggregation == "min":
                    value = min(historic_values)
                elif change_over_time_aggregation == "max":
                    value = max(historic_values)
                elif change_over_time_aggregation == "avg":
                    value = sum(historic_values) / len(historic_values)

                return value

            elif change_over_time_aggregation is None:
                historic_metric_values = self.__get_historic_metric_values(historic_descriptor.metric)
                if len(historic_metric_values) > 0:
                    previous_metric_value = historic_metric_values[0]
                    return previous_metric_value

        elif isinstance(historic_descriptor.anomaly_values, int):
            return self.__get_historic_metric_values(historic_descriptor.metric)

    def __get_historic_metric_values(self, metric):
        historic_metric_values = [
            historic_metric_value
            for historic_metric_value in self.historic_metric_values
            if historic_metric_value["identity"] == metric.identity
        ]

        if not historic_metric_values:
            raise AssertionError(f"No historic measurements for metric {metric.identity}")

        if len(historic_metric_values) > 0:
            historic_metric_values.sort(key=lambda m: m["data_time"], reverse=True)

        return historic_metric_values


MOCK_SODA_CLOUD_INSTANCE = MockSodaCloud()
