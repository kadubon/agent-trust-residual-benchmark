# Full Ollama Experiment Runtime Estimate

On the calibration host, the expected duration for 18 serial Ollama calls is approximately six
minutes with a warm model and approximately seven minutes when the earlier startup-sensitive
observation is substituted for the first call. Reserve nine to ten minutes operationally.

| Quantity | Estimate |
| --- | --- |
| Three observed calibration calls | 17.04–19.98 seconds each |
| Warm central full-run estimate | 6.0 minutes |
| Warm empirical planning range | 5.4–6.3 minutes |
| Startup-adjusted estimate | 7.1 minutes |
| Recommended reserved time | 9–10 minutes |
| Eighteen 120-second timeouts | 36 minutes |

This is an empirical planning extrapolation, not a confidence interval. The calibration contains
three purposively selected cases on one host. The separate 85.1-second observation had uncontrolled
cache state and is not labeled a cold-start measurement. Model loading, hardware, thermals, memory
pressure, prompt length, and other workload can materially change runtime.
