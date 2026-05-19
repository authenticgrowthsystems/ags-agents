# Brand Canon

Source of truth for each brand's voice, positioning, and visual identity. Every agent loads the relevant canon before generating content.

## Active brands

- `ags.md` - Authentic Growth Systems (main, English-first, US/EU/UK markets)

## Planned

- `tnm.md` - Ty Nie Musisz (Polish, lifestyle/wellness for solo entrepreneurs - awaiting Tomasz Wave 0 completion)
- `rdc.md` - Royal Dance Center (Polish, local Opole, voice agent Pawel already deployed)
- `personal.md` - Tomasz Nawrocki personal brand (LinkedIn personal, multi-language)

## Versioning

Each canon file has a version number at the top (e.g., AGS is v1.2 as of 17/05/2026).

When canon updates, bump version + add changelog entry at top. Agents check version on load.

## Anti-pattern enforcement

Each canon includes a "what we never do" section. Agents must screen output against this before HITL preview.
