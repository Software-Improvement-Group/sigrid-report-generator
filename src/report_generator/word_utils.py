# Copyright Software Improvement Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

class WordUtils:

    def merge_runs_with_same_formatting(paragraph):
        last_run = None
        for run in paragraph.runs:
            if last_run is None:
                last_run = run
                continue
            if WordUtils.has_same_formatting(run, last_run):
                last_run = WordUtils.combine_runs(last_run, run)
                continue
            last_run = run

    def has_same_formatting(run, run_2):
        font, font_2 = run.font, run_2.font
        if font.bold != font_2.bold:
            return False
        if font.italic != font_2.italic:
            return False
        if font.name != font_2.name:
            return False
        if font.size != font_2.size:
            return False
        if font.underline != font_2.underline:
            return False
        return True
    
    def combine_runs(base, suffix):
        base.text = base.text + suffix.text
        r_to_remove = suffix._r
        r_to_remove.getparent().remove(r_to_remove)
        return base