# Router eval: proposed inputs (15 cases)

Changes from `cases.json`: **case_09** relabeled `billing` → `account`; **case_03, case_07, case_11** replaced (originals were verbatim few-shot examples in `router.py`).

| id | expected | source | note |
|---|---|---|---|
| case_01 | billing | banking77 | |
| case_02 | cards | banking77 | |
| case_03 | top-up | **new** | replaces "My top up is pending." |
| case_04 | account | banking77 | |
| case_05 | transfers | banking77 | |
| case_06 | billing | banking77 | |
| case_07 | cards | **new** | replaces "I lost my card" |
| case_08 | transfers | banking77 | |
| case_09 | account | banking77 | **relabeled** from billing |
| case_10 | account | banking77 | |
| case_11 | billing | **new** | replaces "Can I have a refund?" |
| case_12 | top-up | banking77 | ambiguous: mentions a charge (billing) but is about adding money (top-up) |
| case_13 | cards | banking77 | |
| case_14 | transfers | banking77 | |
| case_15 | top-up | banking77 | |

Label counts: billing 3, cards 3, top-up 3, transfers 3, account 3. Majority-class baseline = 20%.

## case_01 (billing)
```
I have been charged twice
```
## case_02 (cards)
```
How do I track my card?
```
## case_03 (top-up), new
```
Can I add money to my account with Apple Pay?
```
## case_04 (account)
```
Please delete my account.
```
## case_05 (transfers)
```
Why did my transfer fail?
```
## case_06 (billing)
```
What is this $1 charge on my statement?
```
## case_07 (cards), new
```
How do I activate my new card?
```
## case_08 (transfers)
```
I tried to send someone money but they haven't received it.
```
## case_09 (account), relabeled
```
I forgot my password
```
## case_10 (account)
```
How to change my address.
```
## case_11 (billing), new
```
Do you charge a monthly fee for the account?
```
## case_12 (top-up)
```
i was charged when i used a us issued card. why and what cards are free to use to add money
```
## case_13 (cards)
```
The ATM ate my card.
```
## case_14 (transfers)
```
How can I cancel a transfer?
```
## case_15 (top-up)
```
My top up failed.
```
