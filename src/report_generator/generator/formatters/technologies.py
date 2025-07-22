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
from typing import Dict, Optional

import requests
import yaml

TECHNOLOGY_DATA_URL = "https://raw.githubusercontent.com/Software-Improvement-Group/sigridci/main/resources/technologies.yaml"
_has_attempted_load = False
_technology_cache: Optional[Dict[str, Dict[str, str]]] = None


def _fetch_technologies_yaml() -> list:
    global _has_attempted_load
    _has_attempted_load = True

    try:
        response = requests.get(TECHNOLOGY_DATA_URL, timeout=10)
        response.raise_for_status()
        data = yaml.safe_load(response.text)
        if not isinstance(data, list):
            logging.warning("Expected YAML to be a list of technology entries")
            return []
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch technologies.yaml: {e}")
        return []
    except yaml.YAMLError as e:
        logging.error(f"Failed to parse technologies.yaml: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error loading technologies: {e}")
        return []


def _load_technologies() -> Dict[str, Dict[str, str]]:
    data = _fetch_technologies_yaml()
    tech_dict = {}
    for tech in data:
        if isinstance(tech, dict) and 'context' in tech:
            context = tech['context'].lower()
            tech_dict[context] = {
                'display_name': tech.get('display_name'),
                'category'    : tech.get('category')
            }
    return tech_dict


def _get_technology_cache() -> dict[str, dict[str, str]]:
    global _technology_cache, _has_attempted_load

    if _technology_cache is None and not _has_attempted_load:
        _technology_cache = _load_technologies()
        logging.info(f"Loaded technology data from {len(_technology_cache)} technologies")

    return _technology_cache


def get_technology_name(technology: str) -> str:
    tech_cache = _get_technology_cache()
    technology = technology.lower()
    display_name = tech_cache.get(technology, {}).get('display_name')

    return display_name if display_name else get_fallback_technology_name(technology)


def get_fallback_technology_name(technology: str) -> str:
    return technology.upper() if len(technology) < 3 else technology.title()


def get_technology_category(technology: str) -> str:
    tech_cache = _get_technology_cache()
    technology = technology.lower()
    technology_category = tech_cache.get(technology, {}).get('category')

    return technology_category if technology_category else "unknown"


def clear_technology_cache():
    global _technology_cache
    _technology_cache = None


def get_cache_info() -> Dict:
    return {
        "has_attempted_load": _has_attempted_load,
        "is_loaded"         : _technology_cache is not None,
        "cache_size"        : len(_technology_cache) if _technology_cache else 0,
    }
