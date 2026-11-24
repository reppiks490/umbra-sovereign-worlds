# v9.5 — scale-equivariant weighted graph intervention

Six new 65-parameter synthetic neural candidates, three matched seed pairs, identical starting parameters, identical training graphs and teacher-state curriculum, 300 optimizer steps each (1,800 total), 21,600 graph instances including repeated arms. Fresh seeds disjoint from v94. Independent held-out graphs: 192 base graphs per arm, 576 graph-scale observations per arm at factors 1,3,5 (not 576 independent topologies). Dijkstra reference independently checked at every scale. Scale 5 unseen in both v94 and v95 training. Model wrapper explicitly provides sum-based scale factor and dimensionless input: architectural prior, not learned arithmetic mastery. Same weights, different functional initialization and compute.

| Seed | Unstructured OOD MAE | Homogeneous OOD MAE | Unstructured ID MAE | Homogeneous ID MAE |
|---|---:|---:|---:|---:|
| 12001 | 10.199845 | 0.676631 | 3.318861 | 0.093156 |
| 12002 | 8.049414 | 0.214245 | 2.256785 | 0.044656 |
| 12003 | 5.996532 | 0.064598 | 2.173500 | 0.011466 |

OOD wins 3/3, ID wins 3/3, maximum homogeneous scale equivariance error 1.43e-13. Exact deterministic reference remains superior. Small synthetic experiment; no independent real-domain transfer, retention or semantic mastery claim; no promotion. All six trained candidates retained as numeric arrays in isolated local experiment directory, not added to private PC bank or exported. v94 negative OOD result remains recorded.

v94 CI 23/24 failed because optional NumPy absent in clean Torch environment (run 45487950337 job 138778253274). Reproduced by mocking Tensor.numpy, replaced with standard-library little-endian struct packing preserving previous x86 byte format; regression and full v94/v95 tests 11/11 pass on isolated Linux. v95 RED missing module then 5/5 GREEN; exact source/test blobs 42a6368012c2d0f85fa507aa0c142b1f967a60cf and 0726302e7392c434c75ec1557026da4f832dc08e; repaired v94 blobs 292f4b308c8bff3449ba40a499e2794d5205cb6b and 33827b3930a23ddedb6b47cd0e991b5891ac828d. Exact CI on current HEAD pending. No production authority, merge, paid resources or private source weights.

Next: authenticated duplicate-window admission for numerical trials, proof feedback live comparison when resource admission permits, local skill corpus and native MCP qualification, original weight recovery and broader independent task transfer.
