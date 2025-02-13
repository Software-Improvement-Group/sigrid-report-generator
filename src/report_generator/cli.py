#!/usr/bin/env python3

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

import logging
import click
import os
import requests
from .specific_reports.default_report import DefaultReport
from .specific_reports.debug_report import DebugReport
from .word_report import WordReport
from .powerpoint_report import PowerpointReport
from importlib_resources import files

REPORT_TYPES = ['default', 'debug', 'word-debug']
PPTX_LAYOUTS = {
    'default': files("report_generator.templates").joinpath("default-template.pptx"),
    'debug': files("report_generator.templates").joinpath("debug-template.pptx")
}
DOCX_LAYOUTS = {
    'word-debug': files("report_generator.templates").joinpath("debug-template.docx")
}

MATOMO_URL = os.environ.get('MATOMO_URL', 'https://sigrid-says.com/usage')

SIGRID_CI_TOKEN = os.environ.get('SIGRID_CI_TOKEN', None)

@click.command()
@click.option('-d', '--debug', is_flag=True, default=False, help='enable debug messages')
@click.option('-c', '--customer', required = True, help='Customer name')
@click.option('-s', '--system', required = True, help='System name')
@click.option('-t', '--token', default=lambda: os.environ.get('SIGRID_CI_TOKEN'), required = True, help='Sigrid CI token for this customer')
@click.option('-l', '--layout',  type=click.Choice(REPORT_TYPES), default='default', help='The type of report (e.g. itdd-light, monitor, ...)  (mutually exclusive with the -p/--template option)')
@click.option('-p', '--template', type=click.File('rb'), help='A custom report template file (mutually exclusive with the -l/--layout option)')
@click.option('-o', '--out-file', default='out.pptx', help='write output to this file (default out.pptx)')
@click.pass_context
def run(ctx, debug, customer, system, token, layout, template, out_file):
    configure_logging(debug)
    record_usage_statistics()
    if not require_either_layout_or_template(layout, template):
        return

    report = determine_report(template, layout, customer, system, token, out_file)
    if report != None:
        report.create()
    else:
        logging.error(f"Unsupported report type. Either select a predefined report: ({','.join(REPORT_TYPES)}) or supply your own custom template")

def require_either_layout_or_template(layout, template):
    if layout == 'default' and template == None:
        logging.info("No layout or template defined. Using default layout")
        return True
    if layout != None and layout != 'default' and template != None:
        logging.error("Both a layout and template are defined. Choose either a predefined layout using -l/--layout, or provide your own report template using -p/--template. Not both")
        return False
    return True

def determine_report(template, layout, customer, system, token, out_file):
    if(template != None):
        if template.name.endswith(".pptx"):
            return PowerpointReport(customer, system, token, out_file, template)
        elif template.name.endswith(".docx"):
            return WordReport(customer, system, token, out_file, template)
        else:
            logging.error("The report template should either be a .pptx or a .docx document")
            return None
    
    if layout in PPTX_LAYOUTS:
        return PowerpointReport(customer, system, token, out_file, PPTX_LAYOUTS[layout])
    if layout in DOCX_LAYOUTS:
        return WordReport(customer, system, token, out_file, DOCX_LAYOUTS[layout])

# Usage statistics, just fire-and-forget the request, we don't care about the response.
def record_usage_statistics():
    user = os.environ.get('USER', 'unknown')
    try:
        requests.get(f"{MATOMO_URL}matomo.php?idsite=5&rec=1&ca=1&e_c=consultancy&e_a=report-generator&e_n={user}&uid={user}")
    except requests.exceptions.ConnectionError as e:
        logging.warn(f"Failed to connect to {MATOMO_URL} for registering usage statistics (not harmful).")

def configure_logging(debug):
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

if __name__=="__main__":
    run()
