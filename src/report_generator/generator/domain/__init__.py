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

from functools import reduce

from report_generator.generator.context.portfolio_filters import portfolio_arguments_command
from report_generator.generator.domain.portfolio.architecture_portfolio import architecture_portfolio_data
from report_generator.generator.domain.portfolio.maintainability_delta_quality_portfolio import \
    maintainability_delta_quality_changed_code, maintainability_delta_quality_new_and_changed_code, \
    maintainability_delta_quality_new_code
from report_generator.generator.domain.portfolio.maintainability_portfolio import maintainability_portfolio_data
from report_generator.generator.domain.portfolio.modernization import modernization_data
from report_generator.generator.domain.portfolio.objectives import objectives_data
from report_generator.generator.domain.portfolio.osh_portfolio import osh_portfolio_data
from report_generator.generator.domain.portfolio.progress_sigrid import progress_sigrid_data
from report_generator.generator.domain.portfolio.security_dashboard_findings_portfolio import \
    security_dashboard_findings_portfolio_data
from report_generator.generator.domain.portfolio.security_dashboard_resolution_times_portfolio import \
    security_dashboard_resolution_times_portfolio_data
from report_generator.generator.domain.portfolio.security_portfolio import security_ratings_portfolio_data
from report_generator.generator.domain.system.architecture import architecture_data
from report_generator.generator.domain.system.maintainability import maintainability_data
from report_generator.generator.domain.system.osh import osh_data
from report_generator.generator.domain.system.refactoring_candidates import refactoring_candidates_data
from report_generator.generator.domain.system.security import security_data
from report_generator.generator.domain.system.system_metadata import system_metadata


def compose_options(*decorators):
    """
    Composes multiple decorators into a single decorator.
    Applied in reverse order so the first in the list is the outermost wrapper.
    """
    def composition(func):
        return reduce(lambda f, dec: dec(f), reversed(decorators), func)
    return composition

_data_model_arguments_decorator = [
    portfolio_arguments_command()
]

data_model_arguments = compose_options(*_data_model_arguments_decorator)
