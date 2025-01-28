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

class StaticData:
    maint_metrics = ["VOLUME", "DUPLICATION", "UNIT_SIZE", "UNIT_COMPLEXITY", "UNIT_INTERFACING", "MODULE_COUPLING", "COMPONENT_INDEPENDENCE", "COMPONENT_ENTANGLEMENT"]
    arch_metrics = ["CODE_BREAKDOWN", "COMPONENT_COUPLING", "COMPONENT_COHESION", "CODE_REUSE", "COMMUNICATION_CENTRALIZATION", "DATA_COUPLING", "TECHNOLOGY_PREVALENCE", "BOUNDED_EVOLUTION", "KNOWLEDGE_DISTRIBUTION", "COMPONENT_FRESHNESS"]
    arch_subcharacteristics = ["KNOWLEDGE", "COMMUNICATION", "DATA_ACCESS", "STRUCTURE", "EVOLUTION", "TECHNOLOGY_STACK"]

    ARCH_WORST_METRIC_TEXT = {
        "CODE_BREAKDOWN": "The system's low score in Code Breakdown restricts flexibility, hindering parallel work across boundaries, as the codebase lacks clear, well-defined components, impeding efficient collaboration and adaptability.",
        "COMPONENT_COUPLING": "The system's low score in Component Coupling constrains architecture, constraining evolution and imposing high-impact changes, impeding system adaptability.",
        "COMPONENT_COHESION": "The system scores poorly in Component Cohesion, constraining evolution and triggering high-impact changes, impeding adaptability across the system or landscape.",
        "CODE_REUSE": "The system's low score in Code Reuse heightens complexity, fostering coupling through duplicated code. This impedes flexibility and hinders responsibility separation.",
        "COMMUNICATION_CENTRALIZATION": "The system's low score in Communication Centralization weakens encapsulation, heightening sensitivity to external changes, making updates challenging, and impacting adaptability.",
        "DATA_COUPLING": "The system's low score in Data Coupling constrains flexibility, demanding changes across components with each alteration to the data store structure, hindering adaptability and system resilience.",
        "TECHNOLOGY_PREVALENCE": "The system scores poorly in Technology Prevalence, hampering adaptability and risking component abandonment due to misaligned tech knowledge, impacting efficient change implementation.",
        "BOUNDED_EVOLUTION": "The system scores poorly in Bounded Evolution, implying excessive updates, possibly signaling over-dependence, centralization issues, and hindering system stability and adaptability.",
        "KNOWLEDGE_DISTRIBUTION": "The system's low score in Knowledge Distribution risks knowledge loss with a single developer on a large component, hindering adaptability and continuity upon that person's departure.",
        "COMPONENT_FRESHNESS": "The system's low score in Component Freshness impedes adaptability, indicating centralized activity rather than distributed across components, hindering a balanced and responsive system."
    }

    ARCH_BEST_METRIC_TEXT = {
        "CODE_BREAKDOWN": "The system scores highly in Code Breakdown resulting in increased flexibility through well-defined components that enable efficient parallel work across functional or technical boundaries.",
        "COMPONENT_COUPLING": "The system's high score in component coupling means components with fewer dependencies, allowing for greater evolution, and minimizing impact on the system or landscape during interface changes.",
        "COMPONENT_COHESION": "The system's high score in Component Cohesion means highly reusable and replaceable components with focused internal logic. This minimizes external dependencies and references from other external components.",
        "CODE_REUSE": "The system scores highly in Code Reuse, minimizing duplication within and between components. This reduces coupling, preventing implicit dependencies and enhancing system modularity.",
        "COMMUNICATION_CENTRALIZATION": "The system's high score Communication Centralization reflects high encapsulation. Centralized calls from a component enhance encapsulation, making it less sensitive to external changes and easier to update in response to such modifications.",
        "DATA_COUPLING": "The system scores highly in Data coupling, ensuring high flexibility by limiting components accessing a data store, preventing widespread impact from changes to its structure and enhancing system adaptability.",
        "TECHNOLOGY_PREVALENCE": "The system excels in Technology Prevalence, aligning team knowledge and preventing component abandonment due to unfamiliar tech, fostering adaptability in areas requiring changes.",
        "BOUNDED_EVOLUTION": "The system's high score in Bounded Evolution signifies limited updates for components, preventing excessive dependencies and knowledge centralization, and promoting a more balanced and adaptable system.",
        "KNOWLEDGE_DISTRIBUTION": "The system's high score in Knowledge Distribution averts reliance on a single developer, mitigating knowledge loss risks and fostering continuity.",
        "COMPONENT_FRESHNESS": "The system's high score in Component Freshness ensures activity across multiple components, avoiding centralization, fostering balance, and reducing reliance on a single component."
    }