# Duplicate Notes

Record findings that overlap existing tracked items here.

| incoming title | duplicate of | reason |
|---|---|---|
| Live recovery test can leak tcpctl auth token | `F047` | Same title/root cause; H1 already mitigated recovery-test token leak. |
| Broker forwards exclusive root commands without authorization | `F048` | Same title/root cause; H1 already added broker allow-operator/allow-exclusive gates. |
| Predictable /tmp root dd target permits symlink overwrite | `F049` / `F045` | Same duplicate chain; H3 already closed current item as duplicate of F045. |
| Outer soak timeout can orphan live broker processes | `F050` | Same title/root cause; H2 already added process-group timeout cleanup. |
| Default lifecycle run can fail to stop tcpctl listener | `F051` | Same title/root cause; H2 already added shared token propagation for lifecycle commands. |
| NCM broker treats auth OK as command success | `F052` | Same title/root cause; H1 already fixed final tcpctl trailer parsing. |
| NCM preflight may run untrusted cache tcpctl as root | `F053` / `F046` | Same duplicate chain; H3 already closed current item as duplicate of F046. |
