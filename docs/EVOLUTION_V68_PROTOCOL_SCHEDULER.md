# MYRIAD v6.8 paired-protocol scheduler integration

Baseline: v6.7 commit de4cdb446ebf10fcb4b7d3a91494d4c4051173b3; all 24 PR-triggered workflow runs succeeded at that commit. The existing Windows scheduler and v6.7 files were found on the authorized PC, but the supervisor and launcher did not admit a protocol_research phase.

- Reproduced on the original PC: schedule count 0 rather than 6, and explicit dispatch fell into legacy credential-gated orchestration.
- Fixed in a staged copy: six UTC worker slots per day (02:05, 06:05, 10:05, 14:05, 18:05, 22:05) routed to v6.7 paired research. All existing fleet, teacher, tool, distillation, agent-evolution and benchmark window counts are preserved; six ordinary worker windows are reassigned. CLI admits the new phase.
- Eleven focused local tests passed in an isolated copy of the Windows source (two schedule/dispatch, two supervisor, four resource admission, three protocol tests). No live inference or production admission is established by this test result.
- Live update deferred because the scheduled task was active. Before activation, verify scheduler idle, compare local source against this revision, update the PowerShell phase allowlist to include protocol_research, run focused tests, and activate only through the existing private ACL-protected launcher. Do not read or export HMAC keys or raw receipts. Verify a real paired result and independent replay; if resources are insufficient, record deferral, not completion.
- Preserve draft PR #21 and no-Codex, no-production, no-trading, no-auto-merge restrictions. Full fleet, semantic ability, algorithm and weight-bank targets remain outstanding.
