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
import os
from datetime import date
from typing import Optional

import click
import requests
from dateutil.relativedelta import relativedelta

from report_generator import presets
from report_generator.generator import ReportGenerator, sigrid_api

DEFAULT_START_DATE = (date.today() + relativedelta(months=-1)).strftime('%Y-%m-%d')
DEFAULT_END_DATE = date.today().strftime('%Y-%m-%d')
MATOMO_URL = os.environ.get('MATOMO_URL', 'https://sigrid-says.com/usage')


def _validate_system_requirement(ctx, param, value):
    layout = ctx.params.get('layout')

    system_required = layout in presets.SYSTEM_LEVEL_PRESETS
    system_provided = value is not None

    if system_required and not system_provided:
        system_presets = ', '.join(sorted(presets.SYSTEM_LEVEL_PRESETS))
        raise click.BadParameter(
            f"System is required when using layout '{layout}' "
            f"(required for: {system_presets})"
        )
    elif layout is not None and not system_required and system_provided:
        raise click.BadParameter(
            f"System is not allowed when using layout '{layout}' "
            f"(only required for: {', '.join(presets.SYSTEM_LEVEL_PRESETS)})"
        )

    return value


def _validate_layout_or_template(ctx, param, value):
    if param.name == 'template':
        layout = ctx.params.get('layout')
        template = value

        if template and layout:
            raise click.BadParameter(
                "Both a layout and template are defined. Choose either a predefined layout using -l/--layout, or provide your own report template using -p/--template. Not both"
            )

    return value


@click.command()
@click.option('-d', '--debug', is_flag=True, default=False, help='Enable debug messages')
@click.option('-c', '--customer', required=True, help='Customer name')
@click.option('-s', '--system', required=False, callback=_validate_system_requirement,
              help='System name (required for: ' + ', '.join(presets.SYSTEM_LEVEL_PRESETS) + ')')
@click.option('-t', '--token', default=lambda: os.environ.get('SIGRID_CI_TOKEN'),
              help='Sigrid CI token for this customer')
@click.option('-l', '--layout', type=click.Choice(presets.ids),
              default='default',
              help='The type of report (mutually exclusive with the -p/--template option)')
@click.option('-p', '--template', type=click.File('rb'), callback=_validate_layout_or_template,
              help='A custom report template file (mutually exclusive with the -l/--layout option)')
@click.option('--start', default=DEFAULT_START_DATE, help='Report start date in yyyy-mm-dd, default is last month.')
@click.option('-o', '--out-file', default='out', help='write output to this file (default out.pptx/docx)')
@click.option('-a', '--api-url', default=None,
              help=f'Sigrid API base URL, will default to {sigrid_api.DEFAULT_BASE_URL} if not provided')
@click.pass_context
def run(ctx, debug, customer, system, token, layout, template, start, out_file, api_url):
    _configure_logging(debug)
    _configure_api(customer, system, token, (start, DEFAULT_END_DATE), api_url)
    _record_usage_statistics(layout, customer)

    if template:
        ReportGenerator(template.name).generate(out_file)
        return

    presets.run(layout, out_file)


def _configure_api(customer: str, system: str, token: str, period: tuple[str, str], api_url: Optional[str]):
    sigrid_api.set_context(
        bearer_token=token,
        customer=customer,
        system=system,
        period=period,
        base_url=api_url
    )


def _record_usage_statistics(layout, customer):
    if os.environ.get('SIGRID_REPORT_GENERATOR_RECORD_USAGE', '1') == '0':
        logging.info("Not recording usage statistics")
        return

    try:
        report_type = layout.replace("-", "") if layout else ""
        requests.get(
            f"{MATOMO_URL}/matomo.php?idsite=5&rec=1&ca=1&e_c=reportgenerator&e_a={report_type}&e_n={customer}")
    except requests.exceptions.ConnectionError as e:
        logging.warning(f"Failed to connect to {MATOMO_URL} for registering usage statistics (not harmful).")


def _configure_logging(debug):
    logger = logging.getLogger('root')

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.datefmt = '%Y-%m-%d %H:%M:%S'
    ch.setFormatter(formatter)
    logger.addHandler(ch)


if __name__ == "__main__":
    run()
