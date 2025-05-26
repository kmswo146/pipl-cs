# Steps Documentation

## Step 0: Message Categorization

Step 0 uses OpenAI to categorize incoming customer messages and route them appropriately.

### Current Categories

1. **BUG_REPORT** - Customer reporting bugs/issues
   - Action: Send random acknowledgment reply, then pass to step 2
   
2. **NO_FOLLOWUP_REPLY** - Simple acknowledgments ("ok", "thanks")
   - Action: No response needed
   
3. **PROPER_QUESTION** - Genuine questions needing detailed answers
   - Action: Pass to step 1 (FAQ matching)
   
4. **NON_ENGLISH** - Messages not in English
   - Action: Send random "how can we help?" reply
   
5. **GREETING_ONLY** - Just greetings without context
   - Action: Send random "how can we help?" reply
   
6. **UNHAPPY_WITH_ADMIN** - Dissatisfaction with previous admin response
   - Action: No automated response

### Adding New Categories

To add a new category, edit `step0_categorize.py`:

1. **Update the AI prompt** in `STICKY_PROMPT` to include your new category
2. **Add to `CATEGORY_ACTIONS`** dictionary:

```python
"YOUR_NEW_CATEGORY": {
    "action": "action_type",  # See action types below
    "replies": [
        "Reply option 1",
        "Reply option 2"
    ]
}
```

### Action Types

- **`random_reply_only`** - Send random reply, no further processing
- **`random_reply_then_step2`** - Send random reply, then continue to step 2
- **`pass_to_step1`** - No immediate reply, pass to step 1
- **`no_action`** - No reply, no further processing

### Example: Adding a "PRICING_QUESTION" category

```python
# 1. Update STICKY_PROMPT to include:
# 7. PRICING_QUESTION - Customer asking about pricing or plans

# 2. Add to CATEGORY_ACTIONS:
"PRICING_QUESTION": {
    "action": "random_reply_then_step2",
    "replies": [
        "Let me get you our latest pricing information.",
        "I'll help you with pricing details right away."
    ]
}
```

The system will automatically handle the new category once added to the configuration. 