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
from typing import Optional

import click
import requests

from report_generator import presets
from report_generator.generator import ReportGenerator, sigrid_api

MATOMO_URL = os.environ.get('MATOMO_URL', 'https://sigrid-says.com/usage')


@click.command()
@click.option('-d', '--debug', is_flag=True, default=False, help='Enable debug messages')
@click.option('-c', '--customer', required=True, help='Customer name')
@click.option('-s', '--system', required=True, help='System name')
@click.option('-t', '--token', default=lambda: os.environ.get('SIGRID_CI_TOKEN'),
              help='Sigrid CI token for this customer')
@click.option('-l', '--layout', type=click.Choice(presets.ids),
              default='default',
              help='The type of report (mutually exclusive with the -p/--template option)')
@click.option('-p', '--template', type=click.STRING,
              help='A custom report template file (mutually exclusive with the -l/--layout option)')
@click.option('-o', '--out-file', default='out', help='write output to this file (default out.pptx/docx)')
@click.option('-a', '--api-url', default=None,
              help=f'Sigrid API base URL, will default to {sigrid_api.DEFAULT_BASE_URL} if not provided')
@click.pass_context
def run(ctx, debug, customer, system, token, layout, template, out_file, api_url):
    _configure_logging(debug)
    _configure_api(customer, system, token, api_url)
    _record_usage_statistics()
    if not _require_either_layout_or_template(layout, template):
        return

    if template:
        ReportGenerator(template.name).generate(out_file)
        return

    presets.run(layout, out_file)


def _configure_api(customer: str, system: str, token: str, api_url: Optional[str]):
    sigrid_api.set_context(
        bearer_token=token,
        customer=customer,
        system=system,
        base_url=api_url
    )


def _require_either_layout_or_template(layout, template):
    if layout == 'default' and template is None:
        logging.info("No layout or template defined. Using default layout")
        return True
    if layout is not None and layout != 'default' and template is not None:
        logging.error(
            "Both a layout and template are defined. Choose either a predefined layout using -l/--layout, or provide your own report template using -p/--template. Not both")
        return False
    return True


def _record_usage_statistics():
    if os.environ.get('SIGRID_REPORT_GENERATOR_RECORD_USAGE', '1') == '0':
        logging.info("Not recording usage statistics")
        return

    user = os.environ.get('USER', 'unknown')
    try:
        requests.get(
            f"{MATOMO_URL}matomo.php?idsite=5&rec=1&ca=1&e_c=consultancy&e_a=report-generator&e_n={user}&uid={user}")
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
