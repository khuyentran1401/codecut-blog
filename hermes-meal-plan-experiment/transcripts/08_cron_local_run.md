# Cron Job: meal-plan-weekly

**Job ID:** 10a0cb531f13
**Run Time:** 2026-07-12 09:32:41
**Schedule:** 0 18 * * 0

## Prompt

[IMPORTANT: The user has invoked the "meal-plan" skill, indicating they want you to follow its instructions. The full skill content is loaded below.]

---
name: meal-plan
description: Generate quick, hands-off, high-protein, low-carb meal plans with verification checks
---

# Meal Plan Skill

This skill generates weekly dinner plans adhering to the user's constraints:
- **Cooking Method**: Oven, air fryer, slow cooker, or pressure cooker only (no stovetop).
- **Protein**: ≥15g per serving (chicken, fish, lean beef, legumes, tofu).
- **Vegetables**: ≥2 sides per meal (e.g., broccoli, asparagus, cauliflower).
- **Carbs**: ≤20g net carbs (use cauliflower rice/zucchini noodles as rice substitutes).
- **Cuisine**: ≥50% Asian meals; max 2 Western meals/week.

## Verification Steps (Run Before Finalizing)
1. **Method Check**: Confirms cooking method is hands-off (via `allowed_methods = ['oven', 'air_fryer', 'slow_cooker', 'pressure_cooker']`).
2. **Protein & Veggies**: Cross-checks ingredient list for protein ≥15g and ≥2 vegetable sides.
3. **Carb Check**: Uses `net_carb_calculator` to ensure ≤20g net carbs (replaces rice with cauliflower).
4. **Cuisine Ratio**: Counts Asian vs. Western meals weekly (e.g., 5 Asian : 2 Western = valid).

## Example Valid Plan
```
Mon: Oven-baked chicken thighs + roasted broccoli/cauliflower (Asian)
Tue: Slow-cooked Korean beef stew + cauliflower rice (Asian)
Wed: Baked salmon + asparagus (Asian)
Thu: Air-fried beef tacos + cabbage (Western)
Fri: Slow-cooked lentil soup + steamed green beans (Asian)
Sat: Pressure-cooked vegetable curry + cauliflower rice (Asian)
Sun: Oven-baked chicken + steamed broccoli (Asian)
```

The user has provided the following instruction alongside the skill invocation: [IMPORTANT: You are running as a scheduled cron job. DELIVERY: Your final response will be automatically delivered to the user — do NOT use send_message or try to deliver the output yourself. Just produce your report/output as your final response and the system handles the rest. SILENT: If there is genuinely nothing new to report, respond with exactly "[SILENT]" (nothing else) to suppress delivery. Never combine [SILENT] with content — either report your findings normally, or say [SILENT] and nothing more.]

Plan next week's dinners for me and include a short grocery list grouped by category.

## Response

Mon: Oven-baked chicken thighs + roasted broccoli/cauliflower (Asian)
Tue: Slow-cooked Korean beef stew + cauliflower rice (Asian)
Wed: Baked salmon + asparagus/green beans (Asian)
Thu: Air-fried beef tacos (lettuce wraps) + cabbage (Western)
Fri: Slow-cooked lentil soup + green beans (Asian)
Sat: Pressure-cooked vegetable curry (mixed veggies) + cauliflower rice (Asian)
Sun: Oven-baked chicken thighs + steamed broccoli (Asian)

Grocery List:
Proteins: Chicken thighs, Ground beef, Salmon fillets, Dried lentils
Vegetables: Broccoli, Cauliflower, Asparagus, Green beans, Cabbage
Seasonings: Korean spice blend, Curry powder, Fresh ginger, Garlic, Lime
