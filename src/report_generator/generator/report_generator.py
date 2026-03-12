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

import logging
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from report_generator.generator.placeholders import PlaceholderCollection, placeholders as default_placeholders
from report_generator.generator.report import Report


class ReportGenerator:
    def __init__(self, template_path: str):
        self.placeholders: PlaceholderCollection = default_placeholders
        self.report: Report = Report.from_template(template_path)

    def register_additional_placeholders(self, placeholders: PlaceholderCollection) -> None:
        self.placeholders.update(placeholders)

    def get_placeholder_progress_bar(self):
        if logging.getLogger('root').level == logging.DEBUG:
            return self.placeholders

        return tqdm(self.placeholders, desc="Processing", unit=" placeholders")

    def generate(self, output_path: str) -> None:
        num_workers = max(2, min(os.cpu_count() or 4, 8))
        is_debug = logging.getLogger('root').level == logging.DEBUG
        
        logging.debug(f"Processing {len(self.placeholders)} placeholders in parallel ({num_workers} workers, CPU count: {os.cpu_count()})...")
        
        if is_debug:
            timings = self._execute_placeholders(num_workers, self._resolve_placeholder_with_timing)
            slowest = sorted(timings, key=lambda x: x[1], reverse=True)[:10]
            logging.debug("Top 10 slowest placeholders:")
            for key, elapsed in slowest:
                logging.debug(f"  {key}: {elapsed:.2f}s")
        else:
            self._execute_placeholders(num_workers, self._resolve_placeholder)

        self.report.save(output_path)
    
    def _execute_placeholders(self, num_workers: int, resolve_func):
        timings = []
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            with tqdm(total=len(self.placeholders), desc="Processing", unit=" placeholders") as pbar:
                futures = {executor.submit(resolve_func, p): p for p in self.placeholders}
                for future in as_completed(futures):
                    placeholder = futures[future]
                    try:
                        result = future.result()
                        if result is not None:
                            timings.append((placeholder.key, result[1]))
                        pbar.set_postfix_str(f"Current: {placeholder.key}")
                        pbar.update(1)
                    except Exception as e:
                        logging.error(f"Error processing placeholder {placeholder.key}: {e}")
                        pbar.update(1)
        
        return timings
    
    def _resolve_placeholder(self, placeholder):
        placeholder.resolve(self.report)
    
    def _resolve_placeholder_with_timing(self, placeholder):
        start = time.time()
        placeholder.resolve(self.report)
        elapsed = time.time() - start
        return start, elapsed
