# audit_fransbot_orders

Scanned 143 bot-module source files for direct actor `CancelActivity`/`QueueActivity` calls.

PASS — zero direct-activity sites. Bots drive actors exclusively through the order stream; multiplayer stays in sync and the order gate (§19.6) sees every issuer/lease pairing.
