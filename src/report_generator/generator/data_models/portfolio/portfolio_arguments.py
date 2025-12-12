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

from typing import Optional
from functools import wraps
import click

from report_generator.generator import sigrid_api

METADATA_LIFECYCLE_MAPPING = {
    "INITIAL" : "Initial development",
    "EVOLUTION" : "Evolution",
    "MAINTENANCE" : "Maintenance",
    "EOL" : "End-of-life",
    "DECOMMISSIONED" : "Decommissioned"
}
METADATA_DEPLOYMENT_MAPPING = {x: x.lower().capitalize().replace('_','-') for x in ["PUBLIC_FACING", "CONNECTED", "INTERNAL", "PHYSICAL"]}
METADATA_BUSINESS_CRITICALITY_MAPPING = {x: x.lower().capitalize() for x in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]}
METADATA_DISTRIBUTION_MAPPING = {x: x.lower().capitalize().replace('_', ' ') for x in ["NOT_DISTRIBUTED", "NETWORK_SERVICE", "DISTRIBUTED"]}
METADATA_APPLICATION_TYPE_MAPPING = {x: x.lower().capitalize().replace('_', ' ') for x in ["PROCESS_CONTROLLER","TRANSACTION_PROCESSING","RESOURCE_MANAGEMENT","CASE_MANAGEMENT","DESIGN_ENGINEERING_DEVELOPMENT","ANALYTICAL","AUTHENTICATION_AND_PORTALS","COMMUNICATION","FUNCTIONAL_APPLICATIONS","KNOWLEDGE_AND_DOCUMENT_MANAGEMENT","PERSONAL_PRODUCTIVITY_APPLICATIONS"]}
METADATA_TARGET_INDUSTRY_MAPPING = {"ICD0500":"Oil & Gas","ICD1750":"Industrial Metals & Mining","ICD2350":"Construction & Materials","ICD2710":"Aerospace & Defense","ICD2730":"Electronic & Electrical Equipment","ICD2750":"Industrial Engineering","ICD2770":"Industrial Transportation","ICD2790":"Support Services","ICD2797":"Industrial Suppliers","ICD3350":"Automobiles & Part","ICD3500":"Food & Beverage","ICD3700":"Personal & Household Goods","ICD4500":"Health Care","ICD5300":"Retail","ICD5500":"Media","ICD5700":"Travel & Leisure","ICD6500":"Telecommunications","ICD7500":"Energy","ICD7577":"Water","ICD8300":"Banking","ICD8500":"Insurance","ICD8630":"Real Estate Investment & Services","ICD8700":"Financial Services","ICD9530":"Software & Computer Services","ICD9570":"Technology hardware & equipment","SIG2200":"Legal Services","SIG1200":"Research","SIG1000":"Government","SIG1100":"Education"}

_team: Optional[list[str]] = None
_division: Optional[list[str]] = None
_lifecycle: Optional[list[str]] = None
_deployment: Optional[list[str]] = None
_business_crititality: Optional[list[str]] = None
_distribution: Optional[list[str]] = None
_application_type: Optional[list[str]] = None
_target_industry: Optional[list[str]] = None

def validate_values(values: list[str], allowed_values: set[str], field: str) -> None:
    invalid = set(values) - allowed_values
    if invalid:
        raise ValueError(f"Invalid value(s) for {field}: {', '.join(sorted(invalid))}")

def process_values(values, mapping, field):
    processed_values = [x.upper() for x in values]
    validate_values(values=processed_values, allowed_values=mapping.keys(), field=field)
    return processed_values

def set_context(
        team: Optional[list[str]] = None,
        division: Optional[list[str]] = None,
        lifecycle: Optional[list[str]] = None,
        deployment: Optional[list[str]] = None,
        business_criticality: Optional[list[str]] = None,
        distribution: Optional[list[str]] = None,
        application_type: Optional[list[str]] = None,
        target_industry: Optional[list[str]] = None
) -> None:
    global _team, _division, _lifecycle, _deployment, _business_crititality, _distribution, _application_type, _target_industry
    if team:
        _team = list(team)

    if division:
        _division = list(division)
    
    if lifecycle:
        _lifecycle = process_values(values=lifecycle, mapping=METADATA_LIFECYCLE_MAPPING, field="Lifecycle")
    
    if deployment:
        _deployment = process_values(values=deployment, mapping=METADATA_DEPLOYMENT_MAPPING, field="Deployment")
    
    if business_criticality:
        _business_crititality = process_values(values=business_criticality, mapping=METADATA_BUSINESS_CRITICALITY_MAPPING, field="Business criticality")
    
    if distribution:
        _distribution = process_values(values=distribution, mapping=METADATA_DISTRIBUTION_MAPPING, field="Distribution")

    if application_type:
        _application_type = process_values(values=application_type, mapping=METADATA_APPLICATION_TYPE_MAPPING, field="Application type")

    if target_industry:
        _target_industry = process_values(values=target_industry, mapping=METADATA_TARGET_INDUSTRY_MAPPING, field="Target industry")

def portfolio_arguments_command():
    def decorator(func):
        @click.option('--team', multiple=True, help="[filter] Team name filter, as displayed in Sigrid (multiple values need separate --team flags, ie.: --team aap --team noot)")
        @click.option('--division', multiple=True, help="[filter] Division name filter, as displayed in Sigrid (multiple values need separate --division flags, ie.: --division aap --division noot)")
        @click.option('--lifecycle', multiple=True, help=f"[filter] Lifecycle filter, as displayed in Sigrid (multiple values need separate --lifecycle flags, ie.: --lifecycle initial --lifecycle evolution). Allowed values: {', '.join([x.lower() for x in METADATA_LIFECYCLE_MAPPING.keys()])}")
        @click.option('--deployment', multiple=True, help=f"[filter] Deployment filter, as displayed in Sigrid (multiple values need separate --deployment flags, ie.: --deployment public-facing --deployment connected). Allowed values: {', '.join([x.lower().replace('_','-') for x in METADATA_DEPLOYMENT_MAPPING.keys()])}")
        @click.option('--business-criticality', multiple=True, help=f"[filter] Business criticality filter, as displayed in Sigrid (multiple values need separate --business-criticality flags, ie.: --business-criticality critical --business-criticality high). Allowed values: {', '.join([x.lower() for x in METADATA_BUSINESS_CRITICALITY_MAPPING.keys()])}")
        @click.option('--distribution', multiple=True, help=f"[filter] Distribution filter, as displayed in Sigrid (multiple values need separate --distribution flags, ie.: --distribution not-distributed --distribution connected). Allowed values: {', '.join([x.lower().replace('_', '-') for x in METADATA_DISTRIBUTION_MAPPING.keys()])}")
        @click.option('--application-type', multiple=True, help=f"[filter] Application type filter, as displayed in Sigrid (multiple values need separate --application-type flags, ie.: --application-type functional-applications --application-type case-management). Allowed values: {', '.join([x.lower().replace('_', '-') for x in METADATA_APPLICATION_TYPE_MAPPING.keys()])}")
        @click.option('--target-industry', multiple=True, help=f"[filter] Target industry filter, as displayed in Sigrid (multiple values need separate --target-industry flags, ie.: --target-industry ICD0500 --target-industry SIG1100). Allowed values: {', '.join([x.lower() for x in METADATA_TARGET_INDUSTRY_MAPPING.keys()])}")
        @wraps(func)
        def wrapper(team, division, lifecycle, deployment, business_criticality, distribution, application_type, target_industry, *args, **kwargs):
            set_context(team=team, division=division, lifecycle=lifecycle, deployment=deployment, business_criticality=business_criticality,
                        distribution=distribution, application_type=application_type, target_industry=target_industry)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def filter_data_on_portfolio_arguments(data_tag=None, system_tag=None):
    """
    This decorator integrates with the Sigrid API to apply portfolio-aware filtering logic to the data returned by the decorated function.
    It ensures that at least one of `data_tag` or `system_tag` is specified to define the filtering context.

    Parameters
    ----------
    data_tag : str, optional
        Tag indicating where system entries are stored in the Sigrid API JSON response.
        E.g.: In `maintainability_portfolio_data`, system entries are available in `maintainability_portfolio_data['systems']`, hence `data_tag='systems'`.
    system_tag : str, optional
        Tag indicating where the system entry's name can be found.
        E.g.: System entries are available in `maintainability_portfolio_data['systems']`, and their system name can be found in `maintainability_portfolio_data['systems']['system']`. Hence: `system_tag='system'`.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if data_tag is None and system_tag is None:
                raise PlaceholderArgumentException(func.__name__)
            
            data = func(*args, **kwargs)

            if not _are_filters_set():
                return data

            pmd = sigrid_api.get_portfolio_metadata()

            if data_tag:
                return _with_data_tag(data=data, portfolio_metadata=pmd, data_tag=data_tag, system_tag=system_tag)
            else:
                return _without_data_tag(data=data, portfolio_metadata=pmd, system_tag=system_tag)
        return wrapper
    return decorator

def _with_data_tag(data, portfolio_metadata, data_tag, system_tag):
    systems = [entry for entry in data[data_tag] if _include(system_name=entry[system_tag], portfolio_metadata=portfolio_metadata)]
    data[data_tag] = systems
    return data

def _without_data_tag(data, portfolio_metadata, system_tag):
    systems = [entry for entry in data if _include(system_name=entry[system_tag], portfolio_metadata=portfolio_metadata)]
    return systems

def _include(system_name, portfolio_metadata):
    global _team, _division, _lifecycle, _deployment, _business_crititality, _distribution, _application_type, _target_industry
    md = _find_system_metadata(system_name=system_name, portfolio_metadata=portfolio_metadata)
    if md is None:
        return False
    
    checks = [
        (_team, md.get('teamNames'), None),
        (_division, md.get('divisionName'), None),
        (_lifecycle, md.get('lifecyclePhase'), str.upper),
        (_deployment, md.get('deploymentType'), lambda x: x.upper().replace('-', '_')),
        (_business_crititality, md.get('businessCriticality'), str.upper),
        (_distribution, md.get('softwareDistributionStrategy'), lambda x: x.upper().replace('-', '_')),
        (_application_type, md.get('applicationType'), lambda x: x.upper().replace('-', '_')),
        (_target_industry, md.get('targetIndustry'), str.upper),
    ]

    for filter_vals, actual_val, transform in checks:
        if filter_vals:
            # Normalize filter values if a transform function is provided
            clean_filters = {transform(x) if transform else x for x in filter_vals}
            
            # Handle intersection (list vs list) or membership (list vs string)
            is_match = False
            if isinstance(actual_val, list):
                is_match = bool(set(actual_val) & clean_filters)
            else:
                is_match = actual_val in clean_filters
                
            if not is_match:
                return False

    return True

def _are_filters_set():
    return _team is not None or _division is not None

def _find_system_metadata(system_name, portfolio_metadata):
    for s in portfolio_metadata:
        if s['systemName'] == system_name:
            return s
    return None

class PlaceholderArgumentException(Exception):
    def __init__(self, function_name, message="Placeholder argument exception"):
        self.function_name = function_name
        self.message = f"{message} in function '{function_name}'"
        super().__init__(self.message)