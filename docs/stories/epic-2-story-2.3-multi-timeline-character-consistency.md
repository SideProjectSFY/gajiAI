# Story 2.3: Multi-Timeline Character Consistency

**Epic**: Epic 2 - AI Adaptation Layer  
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 12 hours

## Description

Implement character trait preservation system that maintains core personality traits across different scenarios while adapting to scenario-specific changes.

## Dependencies

**Blocks**:

- Epic 4 stories (conversation quality depends on consistent characters)

**Requires**:

- Story 2.1: Scenario-to-Prompt Engine (extends prompt adaptation)
- Story 2.2: Context Window Manager (integrates with context building)

## Acceptance Criteria

- [ ] `CharacterTraitExtractor` service extracts core traits from base_story using **Gemini 2.5 Flash** (one-time per character)
- [ ] Trait database: `character_traits` table with character_name, base_story, core_traits JSONB, extracted_at
- [ ] Core traits categorized: personality (brave, intelligent), skills (magic, sword fighting), relationships (friends, enemies), values (loyalty, ambition)
- [ ] Scenario adaptation preserves core traits while modifying scenario-specific ones
- [ ] Example: Hermione in Slytherin preserves "intelligent, studious" but adapts "friends" from Harry/Ron to Draco/Pansy
- [ ] `/api/ai/character-traits/{base_story}/{character}` endpoint retrieves or extracts traits
- [ ] Prompt injection: "PRESERVE: [core_traits], ADAPT: [scenario_changes]"
- [ ] Trait cache with Redis (TTL 7 days, popular characters cached indefinitely)
- [ ] **Gemini API cost optimization**: Batch extract all characters from popular stories, cache aggressively
- [ ] **VectorDB integration**: Store extracted traits in ChromaDB for semantic similarity search
- [ ] Unit tests for trait preservation logic >80% coverage

## Technical Notes

**Character Trait Extraction** (one-time, cached):

```python
from google import generativeai as genai
import chromadb

class CharacterTraitExtractor:

    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.chroma_client = chromadb.HttpClient(host="localhost", port=8000)
        self.traits_collection = self.chroma_client.get_or_create_collection("character_traits")

    async def extract_traits(self, base_story: str, character: str) -> CharacterTraits:
        # Check cache first
        cached = await redis.get(f"traits:{base_story}:{character}")
        if cached:
            return CharacterTraits.parse_raw(cached)

        # Check database
        db_traits = await db.query(
            "SELECT core_traits FROM character_traits "
            "WHERE base_story = $1 AND character_name = $2",
            base_story, character
        )
        if db_traits:
            return CharacterTraits(**db_traits['core_traits'])

        # Extract using Gemini 2.5 Flash (one-time)
        extraction_prompt = f"""
        Analyze the character '{character}' from '{base_story}'.
        Extract their core traits in these categories:

        1. Personality: Adjectives describing their character (brave, cunning, kind)
        2. Skills: Abilities and talents (magic, combat, intelligence)
        3. Relationships: Key people they care about (friends, family, enemies)
        4. Values: What they believe in (loyalty, ambition, justice)

        Return ONLY valid JSON format:
        {{
          "personality": ["brave", "loyal", "impulsive"],
          "skills": ["magic", "flying", "leadership"],
          "relationships": {{"friends": ["Ron", "Hermione"], "enemies": ["Voldemort"]}},
          "values": ["courage", "friendship", "justice"]
        }}
        """

        response = await self.model.generate_content_async(
            extraction_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,  # Low temperature for consistent extraction
                max_output_tokens=1000
            )
        )

        traits_json = json.loads(response.text)
        traits = CharacterTraits(**traits_json)

        # Save to database
        await db.execute(
            "INSERT INTO character_traits (base_story, character_name, core_traits) "
            "VALUES ($1, $2, $3)",
            base_story, character, traits.dict()
        )

        # Save to Redis cache (7 days)
        await redis.setex(
            f"traits:{base_story}:{character}",
            604800,  # 7 days
            traits.json()
        )

        # Save to VectorDB for semantic search
        trait_text = f"{character} from {base_story}: " + \
                     f"Personality: {', '.join(traits.personality)}. " + \
                     f"Skills: {', '.join(traits.skills)}. " + \
                     f"Values: {', '.join(traits.values)}."

        self.traits_collection.add(
            documents=[trait_text],
            metadatas=[{"base_story": base_story, "character": character}],
            ids=[f"{base_story}:{character}"]
        )

        return traits
```

**Scenario Adaptation with Trait Preservation**:

```python
class CharacterConsistencyInjector:

    async def adapt_prompt_with_consistency(
        self,
        scenario: Scenario,
        base_prompt: str
    ) -> str:
        if scenario.scenario_type != "CHARACTER_CHANGE":
            return base_prompt  # Only relevant for character changes

        character = scenario.parameters.get("character")
        base_story = scenario.base_story

        # Get core traits
        traits = await trait_extractor.extract_traits(base_story, character)

        # Identify what changes in scenario
        changed_property = scenario.parameters.get("new_property")

        # Build consistency instruction
        preserve_traits = [
            *traits.personality,
            *traits.skills,
            *traits.values
        ]

        adapt_instruction = f"""
        CORE CHARACTER PRESERVATION:
        - Personality: {', '.join(traits.personality)} (PRESERVE)
        - Skills: {', '.join(traits.skills)} (PRESERVE)
        - Values: {', '.join(traits.values)} (PRESERVE)

        SCENARIO ADAPTATION:
        - {character} is now {changed_property}
        - Relationships adapt accordingly:
          Friends → {self.infer_new_relationships(changed_property, base_story)}

        IMPORTANT: Maintain {character}'s core personality while adapting social context.
        """

        return f"{base_prompt}\n\n{adapt_instruction}"

    def infer_new_relationships(self, new_property: str, base_story: str) -> str:
        # Simple heuristic for relationship adaptation
        # Future: Use Gemini 2.5 Flash for intelligent inference
        if "Slytherin" in new_property and base_story == "Harry Potter":
            return "Draco, Pansy, Blaise"
        elif "Gryffindor" in new_property:
            return "Harry, Ron, Neville"
        return "context-appropriate characters"
```

## QA Checklist

### Functional Testing

- [ ] Extract traits for 5 popular characters (Harry, Hermione, Ned Stark, etc.)
- [ ] Traits cached and reused on subsequent requests
- [ ] Scenario adaptation preserves extracted traits
- [ ] Adapted prompt includes "PRESERVE" and "ADAPT" sections
- [ ] Database stores extracted traits permanently

### Character Consistency Validation

- [ ] Hermione in Slytherin retains "intelligent, studious" personality
- [ ] Harry in Slytherin retains "brave, loyal" but adapts friendships
- [ ] Ned Stark surviving retains "honorable, just" values
- [ ] Multi-turn conversation maintains consistency (test with 20+ messages)

### Performance

- [ ] Trait extraction < 5s (Gemini 2.5 Flash API call)
- [ ] Cached trait retrieval < 50ms
- [ ] Prompt adaptation with traits < 100ms
- [ ] Batch extraction of 10 characters < 30s
- [ ] VectorDB trait query < 100ms

### Edge Cases

- [ ] Unknown character returns generic traits
- [ ] Character with no relationships handles gracefully
- [ ] Very long trait lists truncated to top 5 per category
- [ ] Scenario with no character_change skips trait injection

### Cost Optimization

- [ ] Trait extraction called only once per character
- [ ] Popular characters pre-extracted in database seeding
- [ ] Cache hit rate >90% after initial extraction

## Estimated Effort

12 hours
