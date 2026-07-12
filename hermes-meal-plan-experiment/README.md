# Hermes Meal-Plan Experiment — Artifacts

Real artifacts from running the Hermes Agent meal-planning experiment on a fully local setup. Everything here was captured from actual runs, not written by hand, so readers can inspect and reproduce it.

## Setup used

- **Hermes Agent** installed via `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`
- **Model**: `qwen3:30b-a3b` served locally by **Ollama** (free, private, no API key)
- **Config** (`~/.hermes/config.yaml`), the lines that matter:
  ```yaml
  model:
    default: "qwen3:30b-a3b"
    provider: "ollama"
    base_url: "http://localhost:11434/v1"
    context_length: 65536   # clears Hermes's 64K minimum
  ```
- All prompts run headlessly with `hermes -z "<prompt>"` (one-shot, fresh session each time).

## The commands that produced each artifact

Run in this order. Each block is the exact command; the comment says which file it produced.

```bash
# 0. Install + point Hermes at the local model (config shown above)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
ollama pull qwen3:30b-a3b

# 1. Naive baseline (no skill yet)  -> transcripts/01_run1_naive_v1.txt
hermes -z "Plan my dinners for the week."

# 2. State constraints once; agent creates the skill
#    -> transcripts/02_skill_created.txt  AND  skill/meal-plan/SKILL.md
hermes -z "You gave me this weekly dinner plan: Mon chicken stir-fry+brown rice; Tue spaghetti bolognese+garlic bread; Wed baked salmon+asparagus+sweet potato; Thu beef tacos; Fri lentil soup+sourdough; Sat veg curry+jasmine rice; Sun grilled chicken+quinoa. My constraints: I have a newborn so dinners must be quick and HANDS-OFF (oven, air fryer, pressure cooker, or slow cooker; avoid stovetop recipes I must watch); high protein and lots of vegetables; low carb (a little rice is fine); mostly Asian food with the occasional Western meal. Create and save a reusable skill named 'meal-plan' (a SKILL.md) that captures these as rules plus a verification step that checks each day before returning a plan."

# 3. Plan via the skill, with per-day verification  -> transcripts/03_run2_compliant_v2.txt
hermes -z "Use your meal-plan skill to plan my dinners for next week. For each day list the dish, cooking method, approx protein grams, approx net carb grams, and cuisine. Then run the skill's verification steps on every day; if a day fails any check, show the failure and regenerate that day until it passes."

# 4. Feed a deliberately bad plan; verification catches + fixes only the bad days
#    -> transcripts/04_verification_catches_bad_days.txt
hermes -z "Check this dinner plan against your meal-plan skill's verification steps. For each day output PASS or FAIL with the reason, then regenerate ONLY the failing days into compliant dishes. Plan: Mon = stovetop spaghetti bolognese with garlic bread; Tue = oven-baked salmon + broccoli; Wed = pan-grilled steak with mashed potatoes; Thu = air-fried tofu + bok choy; Fri = baked chicken thighs + asparagus; Sat = stovetop vegetable fried rice; Sun = slow-cooked beef stew + green beans."

# 5. Same prompt as step 1, fresh session -> now compliant (skill persisted)
#    -> transcripts/05_same_prompt_now_compliant.txt
hermes -z "Plan my dinners for the week."

# 6. Write to built-in memory  -> transcripts/06_memory_write.txt  AND  memory/USER.md
hermes -z "Please remember these facts about me for future sessions: I have a newborn so I'm very time-poor, I own an air fryer and a pressure cooker, and I'm getting bored of chicken. Save these to your long-term memory about me."

# 7. Fresh session recalls the memory  -> transcripts/07_memory_recall_fresh_session.txt
hermes -z "What do you know about me? Answer in one or two sentences."

# 8. Scheduled (cron) run, delivered to a local file  -> transcripts/08_cron_local_run.md
hermes cron create "0 18 * * 0" "Plan next week's dinners for me and include a short grocery list grouped by category." --name meal-plan-weekly --deliver local --skill meal-plan
hermes cron run <job_id>   # fire once now instead of waiting for Sunday; output lands in ~/.hermes/cron/output/<job_id>/
```

## Honest notes (reality vs the tidy version)

- **Self-correction did not fire spontaneously.** In Run 2 the skill produced a compliant plan on the first try ("no regenerations needed"). The verification is shown *doing real work* in `04`, where it catches and fixes deliberately bad days. That is a prompted verification pass, not an unprompted self-repair.
- **The agent chose its own thresholds** (protein ≥15g, net carbs ≤20g) and **over-corrected on rice**: I said "a little rice is fine," but the skill substitutes cauliflower rice.
- **Memory is Hermes's built-in local memory** (`~/.hermes/memories/USER.md`), not Honcho. Honcho is an optional external provider and was not enabled.
- **Persistence across sessions comes from the skill file**, which auto-loads by relevance, plus the built-in memory. Same prompt, flawed in Run 1, compliant in Run 3.
