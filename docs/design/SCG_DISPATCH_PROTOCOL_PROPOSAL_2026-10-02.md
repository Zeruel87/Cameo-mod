# SCG / Dispatch Proposal — Neutral RTS-AI Coalition Communication

**Status:** design proposal for discussion with Cameo, Fransbot and other OpenRA AI developers  
**SCG:** **Supreme Coalition General**  
**Cameo reference master reviewed:** `192ed5701f2bbb16b976e41fbd9d840df1c2de2e` (later `6490e520f03d` is development-log only)  
**Core principle:** **SCG is not another AI brain. SCG is a neutral Dispatch relay.**

## 0. Purpose

Different RTS AIs can cooperate in the same OpenRA team without sharing an architecture.

Fransbot may internally use:

```text
General -> MissionCards -> Commanders -> units
```

Cameo may internally use:

```text
MasterAi -> Situation / Utility / Director / TC-3 / planners -> existing owners -> units
```

A stock AI may have none of those abstractions.

Trying to standardize the internal intelligence would either make the protocol enormous or force every AI to adopt someone else's architecture.

SCG takes the opposite approach:

> **Standardize only the smallest amount of information that must cross the boundary between allied AIs.**

What happens inside each AI after it receives that information is private and entirely controlled by that AI's developers.

---

# 1. Locked design principles

## 1.1 Shared vision communicates reality. Dispatch communicates intent.

OpenRA allies normally share vision. They can already observe the common battlefield state.

Therefore SCG must not create another world model and must not routinely repeat battlefield facts that allied AIs can already see.

Do not send merely because it is known:

```text
I have 14 tanks here.
Enemy building X is visible here.
My refinery count is 4.
My Director tension is 83.
```

Do send what observation cannot reveal:

```text
I intend to expand here.
I have committed to attack this player.
I need air support in this area.
I have accepted that support request.
I am releasing this commitment.
```

The common layer is primarily about **intent, commitment, request and lifecycle**.

## 1.2 AI -> SCG -> AI

Different AI implementations do not require direct interoperability.

```text
Fransbot -> SCG -> Cameo
Cameo    -> SCG -> Fransbot
Stock AI -> SCG -> compatible participants
```

Fransbot does not need to parse Cameo internals. Cameo does not need to parse Fransbot MissionCards.

## 1.3 SCG relays. It does not decide.

SCG does **not**:

- choose the coalition main target;
- choose which AI must answer a request;
- allocate sectors;
- vote on allied plans;
- cancel another AI's strategy;
- decide build orders;
- infer unit orders;
- elect rescue forces;
- maintain a second tactical/strategic brain.

SCG may validate and route a Dispatch according to explicit metadata. That is transport, not strategy.

## 1.4 The receiving AI owns interpretation and action

The same incoming Dispatch may result in completely different internal behavior.

Example:

```text
REQUEST AIR_SUPPORT area X
```

Fransbot may create internal MissionCard candidates and Commander bids.

Cameo may expose it as an advisory/provider input to its existing planning/squad owners.

A stock-AI adapter may map it to one simple behavior or return `UNSUPPORTED`.

All are valid.

## 1.5 Internal architecture is private

SCG must never require common support for concepts such as:

```text
Fransbot MissionCards
Fransbot Best Read
Cameo Director phase/tension
Cameo UtilityAxes
Cameo CoalitionDirective
Cameo ScaleTargets
Cameo BuildOrderKnobs
Cameo field-economy telemetry
specific squad states
specific unit types
```

An adapter may use those internally to decide what to publish or how to react. They are not protocol semantics.

## 1.6 Same-family communication may be richer

Two Fransbots can communicate at a richer Fransbot-specific level.

Two Cameo instances can continue to use TeamBlackboard / TC-3 / any later Cameo-specific team mechanism.

That is natural and desirable.

The common rule is only:

> **When a private decision creates coalition-relevant intent, commitment or need, publish the minimum useful result through the common Dispatch boundary so other AI families are not blind to it.**

---

# 2. Relationship to current Cameo TC-3

At current Cameo master, TC-3 is real runtime code:

```text
TeamBroadcast
    -> CoalitionFold
    -> CoalitionDirective
       (MainTarget / Phase / RescueAssignments / SectorAnchors)
    -> Cameo consumers
```

That is **Cameo's internal same-family coordination**.

It is not SCG.

TC-3 is free to understand Cameo-specific concepts such as:

```text
Director phase
MainTarget votes
ArmyCentroid
ExpansionClaim
SectorAnchors
Cameo rescue elections
```

SCG deliberately does not understand these.

Recommended boundary:

```text
          Cameo internal AI / TC-3
                    |
              Cameo SCG Adapter
                    |
             Dispatch protocol
                    |
                   SCG
                    |
             Dispatch protocol
                    |
            Fransbot SCG Adapter
                    |
           Fransbot internal AI
```

Do **not** feed SCG into `CoalitionFold` as another coalition brain.

Do **not** export the whole `TeamBroadcast` to SCG.

The adapter exports only the small cross-family meaning that actually matters.

---

# 3. Why the new FE/BO systems should stay out of SCG

The 2026-10-02 Cameo merge adds rich internal information:

```text
field coverage
refinery anchors
crawl-vs-MCV direction
build-order opening
build-order knob vector
mid-match reaction state
scale targets
production width
```

These are excellent **Cameo inputs and diagnostics**.

They are not useful common protocol fields merely because they exist.

For example, SCG should not receive:

```text
Cameo greed knob = 1173
Cameo coverage_milli = 642
Cameo opening = fast_tech
```

If those internals produce a cross-coalition decision, publish the result instead:

```text
INTENT EXPAND area X
REQUEST DEFEND area X
COMMITMENT ATTACK player Y
```

This is the abstraction boundary.

---

# 4. Participant registration — capability, not intelligence

A participant registers only what SCG needs for routing.

Example:

```json
{
  "schema": "scg-dispatch/0.1",
  "kind": "HELLO",
  "participant_id": "Multi2",
  "ai_family": "cameo",
  "can_send": ["INTENT", "COMMITMENT", "REQUEST", "RESPONSE", "RELEASE"],
  "can_receive": ["INTENT", "COMMITMENT", "REQUEST", "RESPONSE", "RELEASE"],
  "capabilities": ["GROUND", "AIR", "EXPANSION", "CAPTURE"]
}
```

The declared capabilities are routing metadata, **not promises that the AI will accept a request**.

Use a stable match-local participant identity. Do not define SCG identity as OpenRA `ClientIndex`; map-side bots may share the host client index.

Suitable identity is an explicit match participant id / player slot / stable `Player.InternalName`-derived key.

---

# 5. Core Dispatch kinds

Keep the common vocabulary intentionally small.

## INTENT

> I am considering / intending to do this.

Examples:

```text
INTENT EXPAND area X
INTENT ATTACK player Y
INTENT SECURE area Z
```

An INTENT is not ownership and may change.

## COMMITMENT

> I have actually committed internal responsibility/resources to this.

Example:

```text
COMMITMENT SECURE area X
```

The resources and implementation stay private.

## REQUEST

> I want compatible allies to consider helping with this.

Example:

```text
REQUEST AIR_SUPPORT area X
```

SCG forwards it. SCG does not choose the helper.

## RESPONSE

A response to a specific request/dispatch.

Minimal values:

```text
ACCEPT
DECLINE
PARTIAL
UNSUPPORTED
```

`ACCEPT` means only that the receiver has chosen to handle the information internally. It does not standardize how.

## RELEASE

> This intent, commitment or request is no longer active.

Possible reasons:

```text
COMPLETED
ABANDONED
FAILED
SUPERSEDED
NO_LONGER_NEEDED
```

The reason is informative. The receiver still decides what it means.

## Optional STATUS

Only add STATUS if implementations have a demonstrated need that cannot be represented by COMMITMENT/RELEASE.

Do not make periodic progress chatter mandatory in v0.1.

---

# 6. Small common action/capability vocabulary

Describe strategic effects, not units.

Suggested first action vocabulary:

```text
ATTACK
DEFEND
EXPAND
SECURE
RECON
SUPPORT
```

Suggested first capability vocabulary:

```text
GROUND
AIR
SEA
TRANSPORT
CAPTURE
EXPANSION
```

Avoid faction-specific semantics.

Bad common message:

```text
SEND 8 MIGS
BUILD MCV
SEND TANYA
```

Better:

```text
REQUEST AIR_SUPPORT
REQUEST TRANSPORT
REQUEST CAPTURE_SUPPORT
```

Each AI maps the abstract capability to its own faction, doctrine and architecture.

Only standardize a new word when at least two independent implementations need the same meaning.

---

# 7. Dispatch envelope

A minimal OpenRA-oriented shape:

```json
{
  "schema": "scg-dispatch/0.1",
  "game_uid": "...",
  "dispatch_id": "d-000184",
  "sender": "Multi0",
  "audience": "capability:AIR",
  "kind": "REQUEST",
  "action": "SUPPORT",
  "capability": "AIR",
  "target_player": null,
  "target_actor_id": null,
  "area": {
    "x": 91,
    "y": 44,
    "radius": 12
  },
  "urgency": "HIGH",
  "reply_to": null,
  "created_tick": 32150,
  "expires_tick": 33650
}
```

Not every field is required for every kind.

Important rules:

- location uses common OpenRA map coordinates, not AI-private region ids;
- player identity uses stable match-local player identity;
- `target_actor_id` is optional and only for a genuinely shared specific actor/objective;
- every live Dispatch has a bounded lifetime;
- responses correlate through `reply_to`;
- extensions are optional and never required for basic interoperability.

---

# 8. Audience/routing without SCG making a strategic choice

The **sender**, not SCG, states the routing intent.

Examples:

```text
audience: coalition
```

Forward to every compatible ally.

```text
audience: participant:Multi3
```

Forward to that participant.

```text
audience: capability:AIR
```

Forward to every registered ally that declared `AIR` and can receive this Dispatch kind.

SCG does not pick “the best” air AI. It forwards to the declared audience set.

If two AIs accept, both responses are returned to the requester. The requester decides what to do.

This keeps routing mechanical rather than strategic.

---

# 9. Dispatch lifecycle

A stale intent is worse than no intent.

Every live Dispatch should carry:

```text
created_tick
expires_tick
```

and may be closed early with `RELEASE`.

SCG may maintain an **active Dispatch ledger**, but that ledger is message lifecycle state, not a battlefield model.

SCG may:

- discard expired messages from the active set;
- correlate replies;
- log traffic;
- deliver replacement/revision messages.

SCG must not infer that expiry means success/failure or invent a replacement decision.

---

# 10. What SCG actually does

## SCG MAY

1. validate schema/version;
2. register participant/capability metadata;
3. validate or assign message ids;
4. track active Dispatch lifecycle until release/expiry;
5. forward to the explicit audience;
6. relay responses to the original sender;
7. log Dispatch traffic for debugging/replay analysis;
8. ignore/forward opaque optional extension blocks without understanding them.

## SCG MUST NOT

1. choose a coalition main target;
2. choose which ally is strategically best for a request;
3. resolve competing expansion claims itself;
4. assign sectors;
5. elect rescue responders;
6. rank allied intents;
7. change another AI's build order;
8. maintain a second enemy/world intelligence model;
9. issue gameplay orders;
10. require the receiver to act.

If two AIs publish conflicting `INTENT EXPAND` messages, SCG forwards those intents to their declared audience. **The AI implementations decide how to react.**

---

# 11. Stock AI participation

Stock AI must be able to participate honestly at a lower communication level.

## Level 0 — publish-only observer adapter

An adapter observes clear stock-AI commitments and emits coarse messages:

```text
COMMITMENT ATTACK player X
COMMITMENT EXPAND area Y
RELEASE ...
```

It receives nothing.

This is still valuable: sophisticated allies learn what the stock AI intends and can plan around it.

## Level 1 — basic receive

The adapter understands a small subset of incoming requests, e.g. support at a map position.

Anything else returns `UNSUPPORTED` or is ignored according to the registered contract.

## Level 2 — full common protocol

An advanced AI can publish and consume the whole common v0.x vocabulary.

No implementation is required to pretend it supports semantics it does not actually implement.

---

# 12. Same-family fast paths remain valid

A mixed team may look like:

```text
Fransbot A <==== rich Fransbot channel ====> Fransbot B
     |                                         |
     +--------------- Dispatch ----------------+
                         |
                        SCG
                         |
     +--------------- Dispatch ----------------+
     |                                         |
 Cameo A   <===== Cameo TC-3 / blackboard ===> Cameo B
```

The same-family paths may be much richer and faster.

The SCG boundary is the **coalition lingua franca**, not a replacement for those paths.

---

# 13. Suggested Cameo adapter boundary

Do not modify TC-3 to become SCG.

A separate Cameo adapter can publish coalition-relevant outcomes of Cameo's internal decisions.

Illustrative outbound mappings:

```text
Cameo actually intends/commits to a main enemy
    -> INTENT / COMMITMENT ATTACK target_player

ExpansionPlanner commits an MCV/base expansion
    -> INTENT / COMMITMENT EXPAND area

Cameo's own logic decides outside support would be useful
    -> REQUEST <capability> area

Cameo abandons/completes the commitment
    -> RELEASE reference
```

Do not automatically export:

```text
TeamBroadcast
CoalitionDirective
Director tension
Utility axes
ArmyCentroid
BuildOrderKnobs
ScaleTargets
field coverage telemetry
```

For inbound traffic, use a small **advisory inbox/provider seam** conceptually like:

```text
IBotExternalCoalitionInbox
```

Existing Cameo decision owners may read it. The adapter itself should not issue gameplay orders.

The exact interface name is Cameo's choice; the ownership rule is the important part.

---

# 14. Suggested Fransbot adapter boundary

Fransbot publishes only coalition-relevant results of its private strategic process:

```text
General intends SECURE area
    -> INTENT SECURE

General commits through its own MissionCard/Commander process
    -> COMMITMENT SECURE

General needs a capability it cannot or does not want to satisfy locally
    -> REQUEST

General no longer needs/can hold it
    -> RELEASE
```

Inbound Dispatches become information for Fransbot's own General / Best Read / MissionCard logic **only if Fransbot chooses to use them**.

SCG does not create Fransbot MissionCards.

---

# 15. Versioning and extension rule

Start deliberately small:

```text
scg-dispatch/0.1
```

Rules:

- unknown optional fields are ignored;
- unsupported semantic requests may receive `UNSUPPORTED`;
- breaking semantic changes increment the major version;
- AI-private data never becomes mandatory merely because one implementation has it.

Optional same-family extension data may be relayed opaquely:

```json
"extensions": {
  "cameo": { "...": "opaque to SCG" }
}
```

SCG must not depend on it.

Direct same-family channels remain valid and may be preferable.

---

# 16. What success looks like

A coalition contains:

```text
2 x Fransbot
2 x Cameo
1 x stock AI
```

The two Fransbots may coordinate richly with each other.

The two Cameos may coordinate richly through TC-3.

The stock AI may only publish obvious commitments.

All five can still share the minimum common layer:

```text
what I intend to do
what I have actually committed to
what I need allies to consider
how I answer a request
when the intent/commitment/request ends
```

No new shared brain is required.

The core sentence remains:

> **Shared vision communicates reality. Dispatch communicates intent. SCG relays the Dispatch. The receiving AI decides.**
