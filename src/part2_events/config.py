# src/part2_events/config.py

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class EventConfig:
    event_id: str
    name: str
    description: str
    keywords: List[str]


EVENTS: Dict[str, EventConfig] = {
    "election_1860": EventConfig(
        event_id="election_1860",
        name="Election Night 1860",
        description="Abraham Lincoln's election as President in November 1860.",
        keywords=[
            "election of 1860", "election night", "November 1860",
            "presidential election", "Lincoln elected", "ballots"
        ],
    ),
    "fort_sumter": EventConfig(
        event_id="fort_sumter",
        name="Fort Sumter Decision",
        description="Decisions around provisioning or evacuating Fort Sumter in early 1861.",
        keywords=[
            "Fort Sumter", "Charleston harbor", "Anderson", "resupply",
            "Sumter", "Charleston", "batteries", "Coast of South Carolina"
        ],
    ),
    "gettysburg_address": EventConfig(
        event_id="gettysburg_address",
        name="Gettysburg Address",
        description="Lincoln's speech dedicating the cemetery at Gettysburg.",
        keywords=[
            "Gettysburg Address", "four score and seven", "cemetery dedication",
            "Gettysburg", "battlefield", "speech at Gettysburg"
        ],
    ),
    "second_inaugural": EventConfig(
        event_id="second_inaugural",
        name="Second Inaugural Address",
        description="Lincoln's second inaugural address in March 1865.",
        keywords=[
            "second inaugural", "with malice toward none", "inaugural address",
            "March 4, 1865", "inauguration", "second term"
        ],
    ),
    "fords_theatre": EventConfig(
        event_id="fords_theatre",
        name="Ford's Theatre Assassination",
        description="Abraham Lincoln's assassination at Ford's Theatre on April 14, 1865.",
        keywords=[
            "Ford's Theatre", "assassination", "John Wilkes Booth",
            "April 14, 1865", "shot", "balcony", "Washington theatre"
        ],
    ),
}


def get_all_events() -> List[EventConfig]:
    return list(EVENTS.values())
