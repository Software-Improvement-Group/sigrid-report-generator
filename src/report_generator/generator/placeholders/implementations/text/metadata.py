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

from report_generator.generator.domain import maintainability_data, system_metadata

from .base import text_placeholder

LIFECYCLE_PHASE_LABELS = {
    "INITIAL": "Initial development",
    "EVOLUTION": "Evolution",
    "MAINTENANCE": "Maintenance",
    "EOL": "End-of-life",
    "DECOMMISSIONED": "Decommissioned",
}

BUSINESS_CRITICALITY_LABELS = {
    "CRITICAL": "Critical",
    "HIGH": "High",
    "MEDIUM": "Medium",
    "LOW": "Low",
}

DEPLOYMENT_TYPE_LABELS = {
    "PUBLIC_FACING": "Public-facing",
    "CONNECTED": "Connected",
    "INTERNAL": "Internal",
    "PHYSICAL": "Physical",
}

APPLICATION_TYPE_LABELS = {
    "PROCESS_CONTROLLER": "Process controller",
    "TRANSACTION_PROCESSING": "Transaction processing",
    "RESOURCE_MANAGEMENT": "Resource management",
    "CASE_MANAGEMENT": "Case management",
    "DESIGN_ENGINEERING_DEVELOPMENT": "Design engineering development",
    "ANALYTICAL": "Analytical",
    "AUTHENTICATION_AND_PORTALS": "Authentication and portals",
    "COMMUNICATION": "Communication",
    "FUNCTIONAL_APPLICATIONS": "Functional applications",
    "KNOWLEDGE_AND_DOCUMENT_MANAGEMENT": "Knowledge and document management",
    "PERSONAL_PRODUCTIVITY_APPLICATIONS": "Personal productivity applications",
}

DISTRIBUTION_STRATEGY_LABELS = {
    "NOT_DISTRIBUTED": "Not distributed",
    "NETWORK_SERVICE": "Network service",
    "DISTRIBUTED": "Distributed",
}

TARGET_INDUSTRY_LABELS = {
    "ICD0500": "Oil & Gas",
    "ICD1750": "Industrial Metals & Mining",
    "ICD2350": "Construction & Materials",
    "ICD2710": "Aerospace & Defense",
    "ICD2730": "Electronic & Electrical Equipment",
    "ICD2750": "Industrial Engineering",
    "ICD2770": "Industrial Transportation",
    "ICD2790": "Support Services",
    "ICD2797": "Industrial Suppliers",
    "ICD3350": "Automobiles & Part",
    "ICD3500": "Food & Beverage",
    "ICD3700": "Personal & Household Goods",
    "ICD4500": "Health Care",
    "ICD5300": "Retail",
    "ICD5500": "Media",
    "ICD5700": "Travel & Leisure",
    "ICD6500": "Telecommunications",
    "ICD7500": "Energy",
    "ICD7577": "Water",
    "ICD8300": "Banking",
    "ICD8500": "Insurance",
    "ICD8630": "Real Estate Investment & Services",
    "ICD8700": "Financial Services",
    "ICD9530": "Software & Computer Services",
    "ICD9570": "Technology hardware & equipment",
    "SIG2200": "Legal Services",
    "SIG1200": "Research",
    "SIG1000": "Government",
    "SIG1100": "Education",
}


@text_placeholder()
def system_name():
    """The name of the system as defined in Sigrid Metadata, capitalized."""
    return system_metadata.display_name


@text_placeholder()
def customer_name():
    """The name of the customer as defined in Sigrid, capitalized."""
    return maintainability_data.customer_name


@text_placeholder()
def metadata_display_name():
    """The display name of the system."""
    return system_metadata.display_name or ""


@text_placeholder()
def metadata_division():
    """The division name of the system."""
    return system_metadata.division_name or ""


@text_placeholder()
def metadata_team():
    """The team names associated with the system, comma-separated."""
    teams = system_metadata.team_names
    if not teams:
        return ""
    return ", ".join(teams)


@text_placeholder()
def metadata_supplier():
    """The supplier names associated with the system, comma-separated."""
    suppliers = system_metadata.supplier_names
    if not suppliers:
        return ""
    return ", ".join(suppliers)


@text_placeholder()
def metadata_remark():
    """The remark field for the system."""
    return system_metadata.remark or ""


@text_placeholder()
def metadata_status_active():
    """Whether the system is active (Yes/No)."""
    return "Yes" if system_metadata.active else "No"


@text_placeholder()
def metadata_excluded_from_dashboards():
    """Whether the system is excluded from dashboards (Yes/No)."""
    return "Yes" if system_metadata.is_development_only else "No"


@text_placeholder()
def metadata_in_production_since():
    """The year when the system was put into production."""
    year = system_metadata.in_production_since
    return str(year) if year else ""


@text_placeholder()
def metadata_business_criticality():
    """The business criticality level of the system."""
    criticality = system_metadata.business_criticality
    if not criticality:
        return ""
    return BUSINESS_CRITICALITY_LABELS.get(criticality, criticality)


@text_placeholder()
def metadata_lifecycle_phase():
    """The lifecycle phase of the system."""
    phase = system_metadata.lifecycle_phase
    if not phase:
        return ""
    return LIFECYCLE_PHASE_LABELS.get(phase, phase)


@text_placeholder()
def metadata_target_industry():
    """The target industry of the system."""
    industry = system_metadata.target_industry
    if not industry:
        return ""
    return TARGET_INDUSTRY_LABELS.get(industry, industry)


@text_placeholder()
def metadata_deployment_type():
    """The deployment type of the system."""
    deployment = system_metadata.deployment_type
    if not deployment:
        return ""
    return DEPLOYMENT_TYPE_LABELS.get(deployment, deployment)


@text_placeholder()
def metadata_application_type():
    """The application type of the system."""
    app_type = system_metadata.application_type
    if not app_type:
        return ""
    return APPLICATION_TYPE_LABELS.get(app_type, app_type)


@text_placeholder()
def metadata_distribution_strategy():
    """The software distribution strategy of the system."""
    strategy = system_metadata.software_distribution_strategy
    if not strategy:
        return ""
    return DISTRIBUTION_STRATEGY_LABELS.get(strategy, strategy)


@text_placeholder()
def metadata_external_id():
    """The external ID of the system."""
    return system_metadata.external_id or ""


@text_placeholder()
def metadata_external_display_name():
    """The external display name of the system."""
    return system_metadata.external_display_name or ""
