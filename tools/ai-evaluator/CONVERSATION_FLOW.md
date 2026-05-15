# AI Conversation Flow

## How the Alternating Conversation Works

```
┌─────────────────────────────────────────────────────────────┐
│  YOU: Provide initial tech brief                            │
│  (via file: --prompt my_brief.md OR inline text)           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │  AGENT 1: Gemini 3 Flash     │
         │  Role: Technical Evaluator    │
         │                               │
         │  • Analyzes technical details │
         │  • Assesses patentability     │
         │  • Reviews innovation claims  │
         └───────────┬───────────────────┘
                     │ Response 1
                     ▼
         ┌───────────────────────────────┐
         │  AGENT 2: GPT-4o / Claude 3.5│
         │  Role: Strategic Analyst      │
         │                               │
         │  • Evaluates business value   │
         │  • Reviews market strategy    │
         │  • Assesses IP positioning    │
         └───────────┬───────────────────┘
                     │ Critique/Refinement
                     ▼
         ┌───────────────────────────────┐
         │  AGENT 1: Gemini 3 Flash     │
         │  Addresses feedback          │
         │  Refines technical aspects   │
         └───────────┬───────────────────┘
                     │ Refined version
                     ▼
         ┌───────────────────────────────┐
         │  AGENT 2: GPT-4o / Claude 3.5│
         │  Reviews refinements         │
         │  Adds strategic input        │
         └───────────┬───────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │  Continue?  │
              └──┬───────┬──┘
                 │       │
        ┌────────┘       └──────────┐
        │                           │
        ▼ YES                       ▼ NO
   More rounds              ┌───────────────┐
   (back to Agent 1)        │  CONVERGENCE  │
                            │  or MAX ROUNDS│
                            └───────┬───────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  FINAL OUTPUT                │
                    │  • Final document            │
                    │  • Full transcript           │
                    │  • Conversation log (JSON)   │
                    └──────────────────────────────┘
```

## Convergence Detection

The conversation ends when:

1. **Agreement detected**: Both AIs use phrases like:
   - "I agree"
   - "Looks good" 
   - "Approved"
   - "Final version"
   - "No changes needed"
   - "Ready for submission"

2. **Similar responses**: Response lengths become very similar (>85% similarity)

3. **Max rounds reached**: Default 10 rounds (configurable with `--rounds`)

## Key Points

✓ **Only Agent 1 sees your original prompt**  
✓ **Agent 2 sees Agent 1's response**, not your original  
✓ **They alternate** back and forth, building on each other's feedback  
✓ **Not simultaneous** - they take turns, each seeing the previous response  
✓ **Iterative refinement** - each round improves the brief based on the other's critique

## Example Round Flow

**Round 1:**
- Agent 1 (Gemini 3 Flash) reads your brief → Creates initial technical evaluation

**Round 2:**
- Agent 2 (GPT-4o/Claude 3.5) reads Agent 1's evaluation → Adds strategic perspective

**Round 3:**
- Agent 1 reads Agent 2's additions → Refines technical details based on feedback

**Round 4:**
- Agent 2 reads refined version → Confirms or suggests more improvements

**Round 5-N:**
- Continue until both approve OR max rounds reached
