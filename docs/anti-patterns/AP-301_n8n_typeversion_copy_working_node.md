# AP-301: New n8n node with guessed typeVersion instead of copying a working node

**Anti-pattern (03/07/2026, BE, HITL 1b build):** created two IF nodes with `typeVersion: 1` but
NEW filter-format conditions. Old IF engine ignores the unknown format and passes EVERYTHING true -
the agent router silently sent all text to Idea Bot and (worse) the agsel gate swallowed ALL
callback families, killing approve/triage buttons until hotfix.

**Why bad:** silent pass-through, no error anywhere; discovered only in Tomasz's tap-test; every
broken production window costs trust and money.

**Correct:** when adding a node to an existing workflow, COPY typeVersion + parameter shape from a
WORKING node of the same type in that workflow (e.g. `Is Cm Callback?` = if 2.2, conditions.options
{version: 2, typeValidation: 'loose'}; postgres = 2.4; httpRequest = 4.2). Verify routing with a
real execution read (executions API, node-by-node), not only structure.
