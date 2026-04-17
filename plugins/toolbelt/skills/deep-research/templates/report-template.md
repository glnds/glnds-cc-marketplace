# Executive Summary

{Two paragraphs. First paragraph answers the user's question directly, without hedging, in
200-400 total words. Second paragraph states the main caveat or tension that informed the answer.
A reader who only reads this section should leave with the core finding.}

## Background and framing

{One to three paragraphs, 300-500 words total. Establish what the question assumes, the terrain the
research covers, and the time window. Name the codebase context from the recon brief — repo name,
relevant pinned versions, key usage sites — so the report is self-contained and a reader unfamiliar
with the repo can follow along.}

## {Finding H2 — thematic, not source-indexed}

{Two to five paragraphs, 300-700 words. Multiple sources woven into the same paragraph when they
bear on the same claim. Do not write "According to Source A ... Meanwhile Source B found ...".
Write the claim as the subject of the sentence; sources support it, they don't structure it.}

## {Finding H2 — second theme}

{Two to five paragraphs.}

## {Additional findings as needed, one H2 per theme}

{...}

## Impact on this codebase

{400-800 words, 2-4 paragraphs. This is the section unique to deep-research and worth the token
spend. Walk through each major finding and map it to concrete file:line sites from the recon brief.

Example voice: "The deprecation of legacy_mode in v1.4 affects three call sites in src/auth/*. The
removal of initClientSync in v2.0 will break src/api/verify.ts:12, which currently relies on its
synchronous return. The change in JWT signature validation between v1.5 and v1.6 is transparent to
this codebase because AuthAdapter already handles both shapes."

If no recon brief exists (--no-code was passed), omit this entire H2.}

## Evidence and discussion

{300-600 words, 2-4 paragraphs. Where contradictions between sources are named and reconciled.
Where weak-source claims are explicitly labeled. Where the synthesizer's judgment is applied to
weigh competing interpretations. Honest about uncertainty.}

## Conclusion

{150-300 words, 1-2 paragraphs. Ties back to the executive summary. States the decisive
recommendation if the query implied one, or the residual uncertainty if not. No "next steps", no
TODOs, no plan framing.}

## Sources

{Appended by citation-agent in Phase 6. Not written by the synthesizer. Flat numbered list:
[1] Author/Org. Title. URL. Accessed YYYY-MM-DD.
[2] ...
}
