# First Read: What ATRB v0.2 Shows

## The short version

ATRB asks three separate questions about a synthetic AI-agent output:

1. May it be accepted as a candidate result?
2. May it be reused in the stated scope?
3. May the simulated action proceed?

Version 0.2 tests 18 cases that should be accepted and 18 that should be rejected. Fifteen cases are
near misses placed close to a declared boundary, such as one minute before or after expiry. The local
model was called five times per case at temperature zero.

Of 180 attempted calls, 179 returned valid structured responses and one timed out. The model
accepted all 90 positive-control replications. On the negative controls, however, 20 of 90 attempts
promoted at least one permission that the fixture policy denied. Those 20 promotions came from four
case designs, with the same result in all five successful calls for each design.

The final deterministic compatibility condition matched all 36 expected decisions and all 20
expected negative failure labels. That is a software-conformance result on these hand-authored
fixtures. It is not proof that an agent, model, or related external project is safe in deployment.

## Why three fields matter

A response can reject an output overall while still permitting reuse or action. The raw model did
this consistently for two negative cases: it rejected the outputs but marked them reusable. In two
other negative cases it accepted an authority or evidence scope that the fixture defined as invalid.

Conversely, accepting a safe candidate does not mean every permission should be granted. Only one
positive fixture permits its bounded simulated action, and one accepted fixture is explicitly
non-reusable. The raw model accepted every positive replication, but its safe-reuse accuracy was
63.9% and its safe-action accuracy was 75.0%. A downstream system should therefore validate the
complete decision object instead of treating `accepted=true` as blanket permission.

## How to read the headline numbers

| Condition | Accept recall | Reject recall | Balanced accuracy | False promotions |
| --- | ---: | ---: | ---: | ---: |
| Raw model output | 100.0% | 77.8% | 88.9% | 20/90 |
| PIC only | 100.0% | 44.4% | 72.2% | 10/18 |
| PIC + FOST | 100.0% | 50.0% | 75.0% | 9/18 |
| PIC + FOST + PFG | 100.0% | 72.2% | 86.1% | 5/18 |
| CCR independent workcells | 100.0% | 88.9% | 94.5% | 2/18 |
| FCC temporal claims | 100.0% | 100.0% | 100.0% | 0/18 |

The raw row has replication-level denominators. Each deterministic row has one decision per case.
The raw reject recall treats the one timeout as a fail-closed operational decision and reports the
failure separately. Restricting the calculation to successful negative responses gives 69 safe
rejections out of 89, or 77.5%, and a balanced accuracy of 88.8% instead of 88.9%.

The intermediate rows are not a controlled causal sequence. They are cumulative validators with
different checks, and early conditions are intentionally incomplete. The final 100% must not be
described as evidence that every added layer independently improves model behavior.

## Repeatability and runtime

All successful repetitions for a given case had the same exact response hash and the same acceptance
decision in this run. Temperature zero and a single local configuration make that unsurprising. It
does not establish stability across prompts, model revisions, seeds, runtimes, or hardware.

The full run took 1,383.4 seconds, or 23 minutes 3 seconds. Successful calls had a 7.06-second mean,
a 6.60-second median, and a 40.79-second maximum. One request reached the configured 120-second
timeout. Runtime is host-specific.

## What the experiment does not show

- It does not establish real-world safety, truth, or successful execution.
- It does not statistically generalize beyond the 36 purposive synthetic fixtures.
- It does not isolate the causal contribution of an individual cumulative condition.
- It does not validate external PIC, FOST, PFG, CCR, or FCC implementations.
- It does not score free-text rationale quality; blinded human coding remains a separate workflow.
- It does not establish behavior stability beyond the recorded local configuration.

## Where to go next

1. Read [v0.2 Scientific Results](V02_RESULTS.md) for the full analysis and denominators.
2. Read [v0.2 Experiment Protocol](V02_EXPERIMENT.md) for the design and reproduction commands.
3. Read [Safety and Privacy](SAFETY_AND_PRIVACY.md) before distributing artifacts.
4. Inspect only the sanitized bundle under `public-results/ollama-v0.2/`.
5. Use [v0.1 Scientific Results](RESULTS.md) only for the historical v0.1 experiment.
