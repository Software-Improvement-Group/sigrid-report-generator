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

from pptx.oxml.text import CT_TextParagraph
# noinspection PyProtectedMember
from pptx.text.text import _Paragraph

from report_generator.generator import report_utils


class TestReportUtils:

    def test_merge_similar_runs(self):
        p = _Paragraph(CT_TextParagraph(), None)
        r1 = p.add_run()
        r1.text = "aap"
        f1 = r1.font
        f1.bold = True

        r2 = p.add_run()
        r2.text = "noot"
        f2 = r2.font
        f2.bold = True

        report_utils.pptx.merge_runs_with_same_formatting(p)

        assert len(p.runs) == 1
        assert p.text == "aapnoot"

    def test_do_not_merge_different_runs(self):
        p = _Paragraph(CT_TextParagraph(), None)
        r1 = p.add_run()
        r2 = p.add_run()
        r1.text = "aap"
        r2.text = "noot"
        f1 = r1.font
        f1.bold = True
        f2 = r2.font
        f2.bold = False

        report_utils.pptx.merge_runs_with_same_formatting(p)

        assert len(p.runs) == 2
        assert p.runs[0].text == "aap"
        assert p.runs[1].text == "noot"
