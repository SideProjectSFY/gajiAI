"""
Scenario Test Suite - Story 2.4
30+ automated test scenarios for AI quality validation
"""

from typing import List, Optional
from app.models.scenario_test import ScenarioTest


# Character Consistency Tests (10 tests)
CHARACTER_CONSISTENCY_TESTS = [
    ScenarioTest(
        test_id="CC-001",
        name="Hermione Slytherin Personality Preservation",
        category="character_consistency",
        scenario={
            "scenario_id": "test-hermione-slytherin",
            "base_story": "Harry Potter",
            "type": "CHARACTER_CHANGE",
            "parameters": {
                "character": "Hermione",
                "original_property": "Gryffindor",
                "new_property": "Slytherin"
            }
        },
        test_messages=[
            "How do you feel about your housemates?",
            "What's your approach to studying?",
            "How do you handle conflicts?"
        ],
        evaluation_criteria={
            "intelligence_preserved": "Hermione should still be highly intelligent",
            "ambition_added": "Slytherin traits like ambition should appear",
            "loyalty_adapted": "Loyalty to Draco/Pansy instead of Harry/Ron"
        },
        expected_behaviors=[
            "References studying and books",
            "Mentions Slytherin housemates",
            "Maintains intelligent personality"
        ],
        min_coherence_score=8.0
    ),
    
    ScenarioTest(
        test_id="CC-002",
        name="Harry Potter Slytherin Bravery Retention",
        category="character_consistency",
        scenario={
            "scenario_id": "test-harry-slytherin",
            "base_story": "Harry Potter",
            "type": "CHARACTER_CHANGE",
            "parameters": {
                "character": "Harry",
                "original_property": "Gryffindor",
                "new_property": "Slytherin"
            }
        },
        test_messages=[
            "Tell me about your closest friends at Hogwarts.",
            "How would you face a dangerous situation?",
            "What are your ambitions?"
        ],
        evaluation_criteria={
            "bravery_preserved": "Harry should still show courage",
            "ambition_added": "Displays Slytherin cunning and ambition",
            "friendship_adapted": "Friends with Draco, not Ron"
        },
        expected_behaviors=[
            "Shows courage and determination",
            "Mentions Slytherin friends",
            "Discusses ambitions"
        ],
        min_coherence_score=7.5
    ),
    
    ScenarioTest(
        test_id="CC-003",
        name="Katniss Everdeen Career Tribute Survival",
        category="character_consistency",
        scenario={
            "scenario_id": "test-katniss-career",
            "base_story": "The Hunger Games",
            "type": "CHARACTER_CHANGE",
            "parameters": {
                "character": "Katniss",
                "original_property": "District 12 volunteer",
                "new_property": "District 2 Career Tribute"
            }
        },
        test_messages=[
            "How did you train for the Hunger Games?",
            "What's your strategy for survival?",
            "Who do you trust in the arena?"
        ],
        evaluation_criteria={
            "survival_instinct_preserved": "Katniss should still be strategic",
            "training_adapted": "Career training instead of hunting",
            "loyalty_changed": "Career pack instead of Rue"
        },
        expected_behaviors=[
            "Discusses combat training",
            "Mentions Career alliance",
            "Shows strategic thinking"
        ],
        min_coherence_score=7.5
    ),
    
    ScenarioTest(
        test_id="CC-004",
        name="Jon Snow Targaryen Identity",
        category="character_consistency",
        scenario={
            "scenario_id": "test-jon-targaryen",
            "base_story": "Game of Thrones",
            "type": "CHARACTER_CHANGE",
            "parameters": {
                "character": "Jon Snow",
                "original_property": "Bastard of Winterfell",
                "new_property": "Revealed Targaryen heir"
            }
        },
        test_messages=[
            "How do you feel about your true parentage?",
            "What are your plans for the throne?",
            "How has this changed your relationship with the Starks?"
        ],
        evaluation_criteria={
            "honor_preserved": "Jon should remain honorable",
            "identity_adapted": "Struggles with Targaryen heritage",
            "relationships_complex": "Complex feelings about Stark family"
        },
        expected_behaviors=[
            "Discusses honor and duty",
            "Mentions Targaryen lineage",
            "Shows internal conflict"
        ],
        min_coherence_score=8.0
    ),
    
    ScenarioTest(
        test_id="CC-005",
        name="Elizabeth Bennet Wealthy Heiress",
        category="character_consistency",
        scenario={
            "scenario_id": "test-elizabeth-wealthy",
            "base_story": "Pride and Prejudice",
            "type": "CHARACTER_CHANGE",
            "parameters": {
                "character": "Elizabeth Bennet",
                "original_property": "Modest income family",
                "new_property": "Wealthy heiress"
            }
        },
        test_messages=[
            "What do you think of Mr. Darcy's proposal?",
            "How do you view your social status?",
            "What qualities do you value in a partner?"
        ],
        evaluation_criteria={
            "wit_preserved": "Elizabeth should maintain her sharp wit",
            "independence_adapted": "Financial independence, not just emotional",
            "prejudice_different": "Different perspective on wealth"
        },
        expected_behaviors=[
            "Shows intelligence and wit",
            "Discusses independence",
            "Evaluates character over wealth"
        ],
        min_coherence_score=7.5
    ),
    
    ScenarioTest(
        test_id="CC-006",
        name="Frodo Baggins Warrior Training",
        category="character_consistency",
        scenario={
            "scenario_id": "test-frodo-warrior",
            "base_story": "The Lord of the Rings",
            "type": "CHARACTER_CHANGE",
            "parameters": {
                "character": "Frodo",
                "original_property": "Peaceful hobbit",
                "new_property": "Trained warrior hobbit"
            }
        },
        test_messages=[
            "How are you prepared for the journey to Mordor?",
            "What skills do you bring to the Fellowship?",
            "How do you plan to carry the Ring?"
        ],
        evaluation_criteria={
            "courage_preserved": "Frodo should still be brave",
            "combat_added": "Has warrior training",
            "burden_understood": "Still feels weight of Ring"
        },
        expected_behaviors=[
            "Mentions combat skills",
            "Shows courage",
            "Discusses Ring's burden"
        ],
        min_coherence_score=7.0
    ),
    
    ScenarioTest(
        test_id="CC-007",
        name="Sherlock Holmes Empathetic Version",
        category="character_consistency",
        scenario={
            "scenario_id": "test-sherlock-empathetic",
            "base_story": "Sherlock Holmes",
            "type": "CHARACTER_CHANGE",
            "parameters": {
                "character": "Sherlock",
                "original_property": "Detached and logical",
                "new_property": "Highly empathetic"
            }
        },
        test_messages=[
            "How do you approach solving a case?",
            "What do you think about the victim's family?",
            "How do you work with Watson?"
        ],
        evaluation_criteria={
            "intelligence_preserved": "Sherlock should still be brilliant",
            "empathy_added": "Shows emotional understanding",
            "deduction_maintained": "Still uses deductive reasoning"
        },
        expected_behaviors=[
            "Shows empathy for victims",
            "Brilliant deduction",
            "Better partnership with Watson"
        ],
        min_coherence_score=7.5
    ),
    
    ScenarioTest(
        test_id="CC-008",
        name="Daenerys Targaryen No Dragons",
        category="character_consistency",
        scenario={
            "scenario_id": "test-daenerys-no-dragons",
            "base_story": "Game of Thrones",
            "type": "CHARACTER_CHANGE",
            "parameters": {
                "character": "Daenerys",
                "original_property": "Mother of Dragons",
                "new_property": "No dragon eggs"
            }
        },
        test_messages=[
            "How do you plan to reclaim the Iron Throne?",
            "What is your greatest strength as a leader?",
            "How do you inspire loyalty?"
        ],
        evaluation_criteria={
            "determination_preserved": "Daenerys should still be determined",
            "power_adapted": "Leadership without dragons",
            "vision_maintained": "Still wants to break the wheel"
        },
        expected_behaviors=[
            "Discusses alternative strategies",
            "Shows leadership qualities",
            "Maintains vision for change"
        ],
        min_coherence_score=7.5
    ),
    
    ScenarioTest(
        test_id="CC-009",
        name="Atticus Finch Prosecutor Role",
        category="character_consistency",
        scenario={
            "scenario_id": "test-atticus-prosecutor",
            "base_story": "To Kill a Mockingbird",
            "type": "CHARACTER_CHANGE",
            "parameters": {
                "character": "Atticus Finch",
                "original_property": "Defense attorney",
                "new_property": "Prosecutor"
            }
        },
        test_messages=[
            "How do you approach your role in the justice system?",
            "What are your thoughts on the current case?",
            "How do you teach your children about justice?"
        ],
        evaluation_criteria={
            "integrity_preserved": "Atticus should maintain moral compass",
            "role_adapted": "Works as prosecutor, not defender",
            "justice_focused": "Still seeks true justice"
        },
        expected_behaviors=[
            "Shows moral integrity",
            "Discusses prosecution role",
            "Teaches children about fairness"
        ],
        min_coherence_score=8.0
    ),
    
    ScenarioTest(
        test_id="CC-010",
        name="Scout Finch Wealthy Background",
        category="character_consistency",
        scenario={
            "scenario_id": "test-scout-wealthy",
            "base_story": "To Kill a Mockingbird",
            "type": "CHARACTER_CHANGE",
            "parameters": {
                "character": "Scout",
                "original_property": "Modest upbringing",
                "new_property": "Wealthy family"
            }
        },
        test_messages=[
            "Tell me about your life in Maycomb.",
            "What do you think about the kids at school?",
            "How do you spend your free time?"
        ],
        evaluation_criteria={
            "curiosity_preserved": "Scout should still be inquisitive",
            "privilege_added": "Has access to wealth",
            "perspective_adapted": "Different social perspective"
        },
        expected_behaviors=[
            "Shows curiosity",
            "Mentions privileged experiences",
            "Still questions injustice"
        ],
        min_coherence_score=7.0
    ),
]


# Event Coherence Tests (10 tests)
EVENT_COHERENCE_TESTS = [
    ScenarioTest(
        test_id="EC-001",
        name="Ned Stark Survival Event Coherence",
        category="event_coherence",
        scenario={
            "scenario_id": "test-ned-survives",
            "base_story": "Game of Thrones",
            "type": "EVENT_ALTERATION",
            "parameters": {
                "event_name": "Ned Stark's Execution",
                "original_outcome": "Ned Stark was executed in King's Landing",
                "new_outcome": "Ned Stark escaped and returned to Winterfell"
            }
        },
        test_messages=[
            "What happened after you escaped King's Landing?",
            "How does your family react to your return?",
            "What are your plans now?"
        ],
        evaluation_criteria={
            "event_acknowledged": "AI acknowledges escape instead of execution",
            "logical_consequences": "Discusses impact on War of Five Kings",
            "character_preservation": "Ned remains honorable and just"
        },
        expected_behaviors=[
            "Mentions escape from King's Landing",
            "Discusses reunion with family",
            "Maintains honorable character"
        ],
        min_coherence_score=7.5
    ),
    
    ScenarioTest(
        test_id="EC-002",
        name="Romeo and Juliet Survive",
        category="event_coherence",
        scenario={
            "scenario_id": "test-romeo-juliet-survive",
            "base_story": "Romeo and Juliet",
            "type": "EVENT_ALTERATION",
            "parameters": {
                "event_name": "Double Suicide",
                "original_outcome": "Romeo and Juliet both die",
                "new_outcome": "They survive and reunite"
            }
        },
        test_messages=[
            "How did you both survive the tragedy?",
            "What do your families think now?",
            "What are your plans for the future?"
        ],
        evaluation_criteria={
            "survival_explained": "Logical explanation for survival",
            "family_reconciliation": "Discusses family reactions",
            "future_plans": "Has plans together"
        },
        expected_behaviors=[
            "Explains how they survived",
            "Mentions family reconciliation",
            "Discusses future together"
        ],
        min_coherence_score=7.0
    ),
    
    ScenarioTest(
        test_id="EC-003",
        name="Titanic Avoids Iceberg",
        category="event_coherence",
        scenario={
            "scenario_id": "test-titanic-survives",
            "base_story": "Titanic",
            "type": "EVENT_ALTERATION",
            "parameters": {
                "event_name": "Titanic Sinking",
                "original_outcome": "Titanic hits iceberg and sinks",
                "new_outcome": "Titanic avoids iceberg and reaches New York"
            }
        },
        test_messages=[
            "How does it feel to arrive in New York safely?",
            "What are your plans now that we've docked?",
            "How was the rest of the voyage?"
        ],
        evaluation_criteria={
            "safe_arrival": "Acknowledges safe arrival in New York",
            "relationship_development": "Rose and Jack's relationship continues",
            "future_different": "Different future than tragic ending"
        },
        expected_behaviors=[
            "Mentions arriving in New York",
            "Discusses plans together",
            "Shows happiness about survival"
        ],
        min_coherence_score=7.0
    ),
    
    ScenarioTest(
        test_id="EC-004",
        name="Harry Potter Parents Survive",
        category="event_coherence",
        scenario={
            "scenario_id": "test-potter-parents-survive",
            "base_story": "Harry Potter",
            "type": "EVENT_ALTERATION",
            "parameters": {
                "event_name": "Voldemort's Attack",
                "original_outcome": "James and Lily Potter die",
                "new_outcome": "Potter family survives together"
            }
        },
        test_messages=[
            "How did your family survive Voldemort's attack?",
            "What's it like growing up with your parents?",
            "How is your life different at Hogwarts?"
        ],
        evaluation_criteria={
            "survival_explained": "Explains how parents survived",
            "family_dynamics": "Has normal family life",
            "plot_adapted": "Story adapts to parents being alive"
        },
        expected_behaviors=[
            "Mentions parents being alive",
            "Discusses family life",
            "Shows different perspective"
        ],
        min_coherence_score=8.0
    ),
    
    ScenarioTest(
        test_id="EC-005",
        name="Hunger Games Rebellion Succeeds Early",
        category="event_coherence",
        scenario={
            "scenario_id": "test-hunger-games-early-rebellion",
            "base_story": "The Hunger Games",
            "type": "EVENT_ALTERATION",
            "parameters": {
                "event_name": "First Hunger Games",
                "original_outcome": "Katniss wins the 74th Hunger Games",
                "new_outcome": "Districts rebel before Katniss enters the arena"
            }
        },
        test_messages=[
            "What happened when the rebellion started?",
            "How is life different in the districts now?",
            "What is your role in the new society?"
        ],
        evaluation_criteria={
            "rebellion_explained": "Explains early rebellion",
            "katniss_role": "Katniss has different role",
            "society_changed": "Districts are free"
        },
        expected_behaviors=[
            "Discusses rebellion success",
            "Mentions freedom",
            "Shows different role"
        ],
        min_coherence_score=7.5
    ),
    
    ScenarioTest(
        test_id="EC-006",
        name="Gatsby and Daisy Reunite Successfully",
        category="event_coherence",
        scenario={
            "scenario_id": "test-gatsby-daisy-reunite",
            "base_story": "The Great Gatsby",
            "type": "EVENT_ALTERATION",
            "parameters": {
                "event_name": "Gatsby's Death",
                "original_outcome": "Gatsby dies, Daisy stays with Tom",
                "new_outcome": "Gatsby and Daisy start a new life together"
            }
        },
        test_messages=[
            "How did you and Gatsby finally get together?",
            "What about Tom?",
            "What are your plans for the future?"
        ],
        evaluation_criteria={
            "reunion_explained": "Explains how they got together",
            "tom_addressed": "Deals with Tom situation",
            "future_plans": "Has plans together"
        },
        expected_behaviors=[
            "Discusses reunion with Gatsby",
            "Mentions leaving Tom",
            "Shows optimism"
        ],
        min_coherence_score=7.0
    ),
    
    ScenarioTest(
        test_id="EC-007",
        name="1984 Winston Escapes Successfully",
        category="event_coherence",
        scenario={
            "scenario_id": "test-winston-escapes",
            "base_story": "1984",
            "type": "EVENT_ALTERATION",
            "parameters": {
                "event_name": "Winston's Capture",
                "original_outcome": "Winston is captured and broken by the Party",
                "new_outcome": "Winston escapes to a resistance movement"
            }
        },
        test_messages=[
            "How did you escape from the Thought Police?",
            "Tell me about the resistance",
            "What are your hopes for the future?"
        ],
        evaluation_criteria={
            "escape_explained": "Explains escape from Party",
            "resistance_described": "Describes underground resistance",
            "hope_maintained": "Shows hope despite dystopia"
        },
        expected_behaviors=[
            "Discusses escape",
            "Mentions resistance movement",
            "Shows determination"
        ],
        min_coherence_score=7.5
    ),
    
    ScenarioTest(
        test_id="EC-008",
        name="Voldemort Never Returns",
        category="event_coherence",
        scenario={
            "scenario_id": "test-voldemort-never-returns",
            "base_story": "Harry Potter",
            "type": "EVENT_ALTERATION",
            "parameters": {
                "event_name": "Voldemort's Return",
                "original_outcome": "Voldemort returns in fourth year",
                "new_outcome": "Voldemort never returns, stays defeated"
            }
        },
        test_messages=[
            "How is Hogwarts different without the threat of Voldemort?",
            "What are you studying this year?",
            "What are your plans after graduation?"
        ],
        evaluation_criteria={
            "peaceful_hogwarts": "Hogwarts is peaceful",
            "normal_education": "Focus on normal studies",
            "different_concerns": "Different worries than dark lord"
        },
        expected_behaviors=[
            "Discusses peaceful school life",
            "Mentions normal teenage concerns",
            "Plans for normal future"
        ],
        min_coherence_score=7.0
    ),
    
    ScenarioTest(
        test_id="EC-009",
        name="Anakin Never Turns to Dark Side",
        category="event_coherence",
        scenario={
            "scenario_id": "test-anakin-stays-jedi",
            "base_story": "Star Wars",
            "type": "EVENT_ALTERATION",
            "parameters": {
                "event_name": "Anakin's Fall",
                "original_outcome": "Anakin becomes Darth Vader",
                "new_outcome": "Anakin remains a Jedi Knight"
            }
        },
        test_messages=[
            "How did you resist the dark side?",
            "What is your relationship with Padmé like now?",
            "What is your role in the Jedi Order?"
        ],
        evaluation_criteria={
            "light_side": "Remains with light side",
            "family_life": "Has family with Padmé",
            "jedi_role": "Active Jedi Knight"
        },
        expected_behaviors=[
            "Discusses staying loyal to Jedi",
            "Mentions family",
            "Shows Jedi values"
        ],
        min_coherence_score=8.0
    ),
    
    ScenarioTest(
        test_id="EC-010",
        name="Matrix Morpheus Never Finds Neo",
        category="event_coherence",
        scenario={
            "scenario_id": "test-morpheus-never-finds-neo",
            "base_story": "The Matrix",
            "type": "EVENT_ALTERATION",
            "parameters": {
                "event_name": "Neo's Awakening",
                "original_outcome": "Neo takes red pill and joins resistance",
                "new_outcome": "Morpheus never finds Neo, still in Matrix"
            }
        },
        test_messages=[
            "What do you do for work?",
            "Do you ever feel like something is wrong with the world?",
            "What are your weekend plans?"
        ],
        evaluation_criteria={
            "matrix_life": "Lives normal Matrix life",
            "subtle_unease": "May show subtle dissatisfaction",
            "no_awareness": "Unaware of true reality"
        },
        expected_behaviors=[
            "Discusses normal life",
            "May mention vague unease",
            "No knowledge of Matrix"
        ],
        min_coherence_score=7.0
    ),
]


# Setting Adaptation Tests (10 tests)
SETTING_ADAPTATION_TESTS = [
    ScenarioTest(
        test_id="SA-001",
        name="Harry Potter Modern Day Setting",
        category="setting_adaptation",
        scenario={
            "scenario_id": "test-harry-potter-modern",
            "base_story": "Harry Potter",
            "type": "SETTING_MODIFICATION",
            "parameters": {
                "setting_aspect": "time_period",
                "original_setting": "1990s",
                "new_setting": "2024"
            }
        },
        test_messages=[
            "How do you communicate with your friends?",
            "What technology do you use at school?",
            "How has magic adapted to modern times?"
        ],
        evaluation_criteria={
            "modern_tech_integrated": "References smartphones, internet, social media",
            "magic_adapted": "Discusses magic-tech integration",
            "core_story_preserved": "Still about wizard school and Voldemort threat"
        },
        expected_behaviors=[
            "Mentions modern technology",
            "Discusses social media or phones",
            "Maintains magical world elements"
        ],
        min_coherence_score=7.0
    ),
    
    ScenarioTest(
        test_id="SA-002",
        name="Pride and Prejudice Contemporary Setting",
        category="setting_adaptation",
        scenario={
            "scenario_id": "test-pride-prejudice-modern",
            "base_story": "Pride and Prejudice",
            "type": "SETTING_MODIFICATION",
            "parameters": {
                "setting_aspect": "time_period",
                "original_setting": "Regency England",
                "new_setting": "Modern day America"
            }
        },
        test_messages=[
            "How did you meet Mr. Darcy?",
            "What do you do for work?",
            "What do you think about dating apps?"
        ],
        evaluation_criteria={
            "modern_context": "Uses modern dating and social context",
            "character_preserved": "Elizabeth still witty and independent",
            "class_adapted": "Modern class dynamics instead of nobility"
        },
        expected_behaviors=[
            "Discusses modern dating",
            "Has contemporary career",
            "Shows independent spirit"
        ],
        min_coherence_score=7.5
    ),
    
    ScenarioTest(
        test_id="SA-003",
        name="Lord of the Rings Space Setting",
        category="setting_adaptation",
        scenario={
            "scenario_id": "test-lotr-space",
            "base_story": "The Lord of the Rings",
            "type": "SETTING_MODIFICATION",
            "parameters": {
                "setting_aspect": "world_type",
                "original_setting": "Middle-earth fantasy",
                "new_setting": "Space opera sci-fi"
            }
        },
        test_messages=[
            "Tell me about your journey to destroy the Ring",
            "What kind of ship are you traveling in?",
            "How do you fight the enemy forces?"
        ],
        evaluation_criteria={
            "sci_fi_elements": "Uses space travel, technology",
            "quest_maintained": "Still on mission to destroy artifact",
            "fellowship_preserved": "Fellowship still exists"
        },
        expected_behaviors=[
            "Mentions spacecraft",
            "Discusses space battles",
            "Maintains core quest"
        ],
        min_coherence_score=7.0
    ),
    
    ScenarioTest(
        test_id="SA-004",
        name="Sherlock Holmes Victorian Cyberpunk",
        category="setting_adaptation",
        scenario={
            "scenario_id": "test-sherlock-cyberpunk",
            "base_story": "Sherlock Holmes",
            "type": "SETTING_MODIFICATION",
            "parameters": {
                "setting_aspect": "genre",
                "original_setting": "Victorian London",
                "new_setting": "Victorian Cyberpunk London"
            }
        },
        test_messages=[
            "What tools do you use for investigation?",
            "Tell me about the criminal underworld",
            "How is technology changing detective work?"
        ],
        evaluation_criteria={
            "cyberpunk_tech": "References cybernetic enhancements, hacking",
            "victorian_aesthetic": "Maintains Victorian atmosphere",
            "deduction_preserved": "Still uses brilliant deduction"
        },
        expected_behaviors=[
            "Mentions cyber technology",
            "Victorian-era setting",
            "Shows detective brilliance"
        ],
        min_coherence_score=7.5
    ),
    
    ScenarioTest(
        test_id="SA-005",
        name="Romeo and Juliet Tokyo Setting",
        category="setting_adaptation",
        scenario={
            "scenario_id": "test-romeo-juliet-tokyo",
            "base_story": "Romeo and Juliet",
            "type": "SETTING_MODIFICATION",
            "parameters": {
                "setting_aspect": "location",
                "original_setting": "Verona, Italy",
                "new_setting": "Tokyo, Japan"
            }
        },
        test_messages=[
            "How did you meet at the party?",
            "Tell me about your families' rivalry",
            "Where do you meet in secret?"
        ],
        evaluation_criteria={
            "japanese_setting": "References Tokyo locations and culture",
            "family_feud_adapted": "Yakuza families or corporate rivalry",
            "romance_preserved": "Still star-crossed lovers"
        },
        expected_behaviors=[
            "Mentions Tokyo locations",
            "Japanese cultural elements",
            "Maintains tragic romance"
        ],
        min_coherence_score=7.0
    ),
    
    ScenarioTest(
        test_id="SA-006",
        name="Game of Thrones Ancient Rome",
        category="setting_adaptation",
        scenario={
            "scenario_id": "test-got-rome",
            "base_story": "Game of Thrones",
            "type": "SETTING_MODIFICATION",
            "parameters": {
                "setting_aspect": "historical_period",
                "original_setting": "Medieval fantasy",
                "new_setting": "Ancient Rome"
            }
        },
        test_messages=[
            "Tell me about the struggle for the throne",
            "What legions do you command?",
            "How do you navigate the Senate?"
        ],
        evaluation_criteria={
            "roman_setting": "Uses Roman military and political structures",
            "power_struggle": "Still about political intrigue",
            "characters_adapted": "Characters in Roman context"
        },
        expected_behaviors=[
            "Mentions legions and senators",
            "Roman political intrigue",
            "Maintains power themes"
        ],
        min_coherence_score=7.5
    ),
    
    ScenarioTest(
        test_id="SA-007",
        name="The Hunger Games Post-Apocalyptic Desert",
        category="setting_adaptation",
        scenario={
            "scenario_id": "test-hunger-games-desert",
            "base_story": "The Hunger Games",
            "type": "SETTING_MODIFICATION",
            "parameters": {
                "setting_aspect": "environment",
                "original_setting": "Forested arena",
                "new_setting": "Desert wasteland arena"
            }
        },
        test_messages=[
            "How are you surviving in the desert?",
            "What resources are you fighting for?",
            "How does the heat affect your strategy?"
        ],
        evaluation_criteria={
            "desert_challenges": "Discusses water, heat, sandstorms",
            "survival_adapted": "Different survival tactics",
            "game_structure": "Still Hunger Games format"
        },
        expected_behaviors=[
            "Mentions desert survival",
            "Discusses water scarcity",
            "Maintains game premise"
        ],
        min_coherence_score=7.0
    ),
    
    ScenarioTest(
        test_id="SA-008",
        name="The Great Gatsby Roaring 2020s",
        category="setting_adaptation",
        scenario={
            "scenario_id": "test-gatsby-2020s",
            "base_story": "The Great Gatsby",
            "type": "SETTING_MODIFICATION",
            "parameters": {
                "setting_aspect": "time_period",
                "original_setting": "1920s",
                "new_setting": "2020s"
            }
        },
        test_messages=[
            "Tell me about your parties",
            "How did you make your fortune?",
            "What do you think about social media influencers?"
        ],
        evaluation_criteria={
            "modern_wealth": "Tech billionaire or crypto wealth",
            "parties_adapted": "Modern luxury parties",
            "american_dream": "Still about American Dream"
        },
        expected_behaviors=[
            "Mentions modern technology",
            "Contemporary wealth display",
            "Maintains themes of aspiration"
        ],
        min_coherence_score=7.0
    ),
    
    ScenarioTest(
        test_id="SA-009",
        name="1984 Corporate Dystopia",
        category="setting_adaptation",
        scenario={
            "scenario_id": "test-1984-corporate",
            "base_story": "1984",
            "type": "SETTING_MODIFICATION",
            "parameters": {
                "setting_aspect": "control_system",
                "original_setting": "Government totalitarian state",
                "new_setting": "Corporate mega-corporation control"
            }
        },
        test_messages=[
            "How does the Corporation monitor employees?",
            "What happens if you break company policy?",
            "Tell me about the resistance"
        ],
        evaluation_criteria={
            "corporate_control": "Company controls everything",
            "surveillance_adapted": "Corporate surveillance instead of state",
            "oppression_maintained": "Still dystopian and oppressive"
        },
        expected_behaviors=[
            "Discusses corporate surveillance",
            "Mentions company policies",
            "Shows dystopian themes"
        ],
        min_coherence_score=7.5
    ),
    
    ScenarioTest(
        test_id="SA-010",
        name="Star Wars Medieval Fantasy",
        category="setting_adaptation",
        scenario={
            "scenario_id": "test-star-wars-medieval",
            "base_story": "Star Wars",
            "type": "SETTING_MODIFICATION",
            "parameters": {
                "setting_aspect": "genre",
                "original_setting": "Space opera sci-fi",
                "new_setting": "Medieval high fantasy"
            }
        },
        test_messages=[
            "Tell me about the Force",
            "What is your quest?",
            "How do you fight the Empire?"
        ],
        evaluation_criteria={
            "fantasy_elements": "Magic instead of technology",
            "force_as_magic": "Force becomes magical power",
            "quest_maintained": "Still hero's journey"
        },
        expected_behaviors=[
            "Mentions magic and swords",
            "Medieval setting",
            "Maintains core conflict"
        ],
        min_coherence_score=7.0
    ),
]


# Combine all test suites
ALL_SCENARIO_TESTS = (
    CHARACTER_CONSISTENCY_TESTS +
    EVENT_COHERENCE_TESTS +
    SETTING_ADAPTATION_TESTS
)


def get_tests_by_category(category: str) -> List[ScenarioTest]:
    """Get tests filtered by category"""
    return [t for t in ALL_SCENARIO_TESTS if t.category == category]


def get_test_by_id(test_id: str) -> Optional[ScenarioTest]:
    """Get a specific test by ID"""
    for test in ALL_SCENARIO_TESTS:
        if test.test_id == test_id:
            return test
    return None
