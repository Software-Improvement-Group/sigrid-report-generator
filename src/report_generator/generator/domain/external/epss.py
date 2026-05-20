#  Copyright Software Improvement Group
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import csv
import gzip
import io
import urllib.request
from functools import cached_property

FETCH_TIMEOUT_SECONDS = 15
EPSS_URL = "https://epss.empiricalsecurity.com/epss_scores-current.csv.gz"


class EPSSScoreRetrievalError(Exception):
    pass


class EPSSData:
    @cached_property
    def _download_epss_data(self) -> bytes | None:
        try:
            with urllib.request.urlopen(
                EPSS_URL, timeout=FETCH_TIMEOUT_SECONDS
            ) as response:
                return response.read()
        except Exception:
            return None

    def _parse_epss_data(self, compressed: bytes) -> dict[str, float]:
        try:
            with gzip.open(io.BytesIO(compressed), "rt") as f:
                f.readline()  # skip comment line: #model_version:...,score_date:...
                reader = csv.DictReader(f)
                return {row["cve"]: float(row["epss"]) for row in reader}
        except Exception as e:
            raise EPSSScoreRetrievalError("Failed to parse EPSS scores") from e

    @cached_property
    def epss_scores(self) -> dict[str, float]:
        compressed_data = self._download_epss_data
        if compressed_data is None:
            raise EPSSScoreRetrievalError("Failed to download EPSS scores")
        return self._parse_epss_data(compressed_data)


epss_data = EPSSData()
