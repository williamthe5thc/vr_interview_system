# LLM Integration Optimization Guide

This document outlines the optimizations made to the Ollama LLM integration for the soft skills training application.

## Implemented Optimizations

### 1. Configuration Settings
- Switched to the Mistral model for better instruction following and performance
- Increased context window to 8192 to maintain longer conversation history
- Optimized parameters:
  - `temperature`: 0.8 - Slightly increased to give more naturalistic responses
  - `top_p`: 0.92 - Fine-tuned to balance creativity and coherence
  - `top_k`: 45 - Increased for more diverse responses
  - `repeat_penalty`: 1.15 - Added to reduce repetitive phrasing
  - `num_predict`: 150 - Increased to allow for more complete responses
  - Optional seed value for reproducible responses during testing

### 2. Enhanced Caching System
- Implemented metadata-rich cache entries for better analytics
- Intelligent cache pruning based on usage patterns
- Scenario and interaction stage aware caching
- Improved disk persistence with atomic file operations
- Cache hit/miss analytics for performance monitoring
- Auto-scaling cache size (200 entries max)

### 3. Prompt Management
- Added scenario-specific system prompts (interview, conflict resolution, feedback, negotiation)
- Created stage-specific prompt injection for more contextual responses
- Improved context truncation strategy to preserve important conversation history
- Dynamic stopping criteria based on scenario type

### 4. Response Templates
- Added structured response templates for different interaction types
- Templates for various soft skill training scenarios
- Support for template application with fallbacks

### 5. Performance Improvements
- Increased thread pool workers for better concurrent performance
- Reduced default timeout for faster failure recovery
- Added cache simulation for streaming responses
- Intelligent context window management
- Error resilience improvements in cache loading/saving

## Using the New Features

### Setting the Scenario Type
Update the config file to set the scenario type:
```json
"scenario_type": "interview"  // Options: "interview", "conflict_resolution", "feedback", "negotiation"
```

### Using Stage-Specific Prompts
When calling the LLM, include the interaction stage parameter:
```python
response = llm_client.generate_response(
    prompt="Tell me about your experience", 
    context=conversation_history,
    interaction_stage="technical_question"  // Options: "greeting", "technical_question", "behavioral_question", "wrap_up"
)
```

### Applying Response Templates
Use the template application method to format responses consistently:
```python
formatted_message = llm_client.apply_template(
    "follow_up",
    follow_up_question="Can you tell me more about your role in that project?"
)
```

### Monitoring Cache Performance
The system now logs cache performance metrics automatically. You'll see entries like:
```
Cache performance: 72.5% hit rate (145 hits, 55 misses)
```

### Extending to New Soft Skills Scenarios
To add a new scenario type:

1. Add a new system prompt in `templates/response_templates.py`:
```python
SYSTEM_PROMPTS["new_scenario"] = """Your new scenario system prompt here..."""
```

2. Add relevant response templates:
```python
NEW_TEMPLATES = {
    "template_name": "Template content with {placeholder}"
}
TEMPLATES.update(NEW_TEMPLATES)
```

3. Update the config file to use the new scenario:
```json
"scenario_type": "new_scenario"
```

## Performance Considerations

- The cache size is now 200 entries by default, which balances memory usage with performance
- Cache pruning happens intelligently based on both recency and frequency of use
- Streaming responses are simulated from the cache to maintain consistent UI behavior
- First-run requests might be slower, but subsequent interactions will be faster due to caching
- The system preserves key context from conversation history while avoiding context window overflow

## Troubleshooting

- If responses become repetitive, try clearing the cache directory (`data/cache`)
- If you notice slowdowns, check the logs for cache hit rates - below 50% may indicate cache tuning is needed
- For memory issues, adjust the `max_cache_size` parameter in the OllamaClient initialization
- The system is backward compatible with previous cache formats, but for best results, start with a fresh cache

---

These optimizations should result in:
1. Faster response times (especially for common interactions)
2. More natural and contextually appropriate responses
3. Better handling of long conversations
4. More consistent training experiences across sessions
5. Improved resilience to network and service issues
