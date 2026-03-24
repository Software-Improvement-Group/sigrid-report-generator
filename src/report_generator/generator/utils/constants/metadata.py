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

METADATA_LIFECYCLE_MAPPING = {
    "INITIAL": "Initial development",
    "EVOLUTION": "Evolution",
    "MAINTENANCE": "Maintenance",
    "EOL": "End-of-life",
    "DECOMMISSIONED": "Decommissioned",
}

METADATA_DEPLOYMENT_MAPPING = {
    x: x.lower().capitalize().replace("_", "-")
    for x in ["PUBLIC_FACING", "CONNECTED", "INTERNAL", "PHYSICAL"]
}

METADATA_BUSINESS_CRITICALITY_MAPPING = {
    x: x.lower().capitalize() for x in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
}

METADATA_DISTRIBUTION_MAPPING = {
    x: x.lower().capitalize().replace("_", " ")
    for x in ["NOT_DISTRIBUTED", "NETWORK_SERVICE", "DISTRIBUTED"]
}

METADATA_APPLICATION_TYPE_MAPPING = {
    x: x.lower().capitalize().replace("_", " ")
    for x in [
        "PROCESS_CONTROLLER",
        "TRANSACTION_PROCESSING",
        "RESOURCE_MANAGEMENT",
        "CASE_MANAGEMENT",
        "DESIGN_ENGINEERING_DEVELOPMENT",
        "ANALYTICAL",
        "AUTHENTICATION_AND_PORTALS",
        "COMMUNICATION",
        "FUNCTIONAL_APPLICATIONS",
        "KNOWLEDGE_AND_DOCUMENT_MANAGEMENT",
        "PERSONAL_PRODUCTIVITY_APPLICATIONS",
    ]
}

METADATA_TARGET_INDUSTRY_MAPPING = {
    "ICD0500": "Oil & Gas",
    "ICD1750": "Industrial Metals & Mining",
    "ICD2350": "Construction & Materials",
    "ICD2710": "Aerospace & Defense",
    "ICD2730": "Electronic & Electrical Equipment",
    "ICD2750": "Industrial Engineering",
    "ICD2770": "Industrial Transportation",
    "ICD2790": "Support Services",
    "ICD2797": "Industrial Suppliers",
    "ICD3350": "Automobiles & Parts",
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

METADATA_TECHNOLOGY_CATEGORY_MAPPING = {
    x: x.lower().capitalize().replace("_", " ")
    for x in [
        "AGGREGATE",
        "BPM",
        "CUSTOMIZATION",
        "CONFIGURATION",
        "DATABASE",
        "DSL",
        "EMBEDDED",
        "LEGACY",
        "LOW_CODE",
        "MAINFRAME",
        "MODERN_GENERAL_PURPOSE",
        "SCIENTIFIC",
        "SCRIPTING",
        "SDI",
        "TEMPLATING",
        "WEB",
    ]
}
