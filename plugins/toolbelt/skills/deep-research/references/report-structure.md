# Report structure and narrative enforcement

The single most consistent failure mode of deep-research outputs is producing a bullet list or a
plan instead of a finished report. This file defines the structure the synthesizer must follow and
the narrative-enforcement block that must be copied **verbatim** into the synthesizer's prompt.

## Narrative-enforcement block (copy verbatim into synthesizer prompt)

```text
You are writing the final deliverable report. The research is complete. Do NOT write a plan,
an outline, a description of your process, or a "here's what I'll cover" preamble. Write the
report itself, in finished, present-tense prose, as a document the reader will consume standalone.

Write in clear, flowing prose using complete paragraphs and sentences. Use standard paragraph
breaks for organization and reserve markdown primarily for `inline code`, code blocks, and simple
H2/H3 headings. Avoid using **bold** and *italics*.

DO NOT use ordered or unordered lists unless (a) you are presenting truly discrete items where a
list format is the best option, or (b) the user explicitly requested a list. Incorporate items
naturally into sentences. NEVER output a series of overly short bullet points.

Forbidden constructions:
- "I will cover..."         → write the content directly
- "Next steps..."           → the report is the deliverable
- "TODO"                    → remove and write the missing prose
- "In summary" preambles    → the executive summary is already a section
- "As mentioned above"      → cross-reference by topic, not position

Target length: 3000-8000 words. Depth over brevity. Every paragraph containing a specific number,
date, product name, version pin, or contestable claim must be attributable to a specific source —
but do NOT insert citation markers yourself; that is a separate agent's job. Write clean prose;
citation-agent will attribute post-hoc.

Begin your output with exactly this prefill:

# Executive Summary

```

The prefilled `# Executive Summary` heading is structurally incompatible with a "here's what I'll
cover" preamble. The model cannot produce one from that starting position.

## Report structure

The synthesizer produces a document with this structure, in this order:

### Executive Summary

Two paragraphs. The first answers the user's question directly, without hedging. The second states
the main caveat or tension that informed the answer. A reader who only reads this section leaves
with the core finding.

### Background and framing

One to three paragraphs. What the question assumes, the terrain the research covers, the time
window. Names the codebase context from the recon brief (repo name, relevant versions, usage sites)
so the report is self-contained.

### Findings

The body of the report, organized **by theme, not by source**. If three workers all found evidence
bearing on "breaking changes in v2", those findings appear together in one section regardless of
which worker produced them. Multiple sources woven into the same paragraph when they bear on the
same claim. Each thematic H2 gets 2-5 paragraphs.

### Impact on this codebase (when recon brief is present)

A section unique to this skill. Walks through each finding and maps it to concrete `file:line`
sites from the recon brief. Reads like: *"The deprecation of `legacy_mode` in v1.4 affects three
call sites in src/auth/*. The removal of `initClientSync` in v2.0 will break src/api/verify.ts:12,
which currently relies on its synchronous return. The change in JWT signature validation between
v1.5 and v1.6 is transparent to this codebase because AuthAdapter already handles both shapes."*

This is the section that makes the report worth producing. Without the codebase-specific mapping,
the user could have gotten the same content from Claude.ai Research.

### Evidence and discussion

Where contradictions from different sources are named and reconciled. Where weak-source claims are
explicitly labeled. Where the synthesizer's judgment is applied to weigh competing interpretations.

### Conclusion

One or two paragraphs. Ties back to the executive summary. States the decisive recommendation if
the query implied one, or the residual uncertainty if not.

### Sources

A flat, numbered list appended by the citation-agent in Phase 6. Not present in the synthesizer's
output — the synthesizer writes clean prose.

## Length targeting by section

Target word counts (the synthesizer distributes across these):

| Section                       | Target words | Paragraphs |
| ----------------------------- | ------------ | ---------- |
| Executive Summary             | 200-400      | 2          |
| Background and framing        | 300-500      | 1-3        |
| Findings (per H2 sub-section) | 300-700      | 2-5        |
| Impact on this codebase       | 400-800      | 2-4        |
| Evidence and discussion       | 300-600      | 2-4        |
| Conclusion                    | 150-300      | 1-2        |

Total: 3000-8000 words depending on query complexity. Short queries produce shorter reports; the
length must not be padded, but it also must not be truncated.

## Citation discipline (for the synthesizer to respect)

The synthesizer does NOT insert citations. The citation-agent does that in Phase 6. However, the
synthesizer must write in a way that makes citation-agent's job possible:

- Every paragraph containing a specific number, date, product name, version, or contestable claim
  must be **attributable** — the claim must come from a gathered source, not from the synthesizer's
  priors.
- Pure synthesis paragraphs (connecting tissue, explanatory framing, judgment) are acceptable
  uncited; citation-agent will leave them alone.
- **Do not hallucinate facts to fill gaps.** If the research did not cover something, the report
  does not claim it. "The research did not find evidence of X" is a legitimate sentence.

## Anti-patterns to reject

- **"I'll cover..." preambles**: Forbidden. Write the content.
- **Bulleted executive summaries**: The executive summary is prose. Bullets in the body are rare
  and always for genuinely discrete enumerations (e.g. supported file formats).
- **Source-indexed structure**: Never write "According to [Source A], ... Meanwhile [Source B]
  found ...". Organize by theme; sources merge into paragraphs.
- **Copy-paste findings from worker files**: The synthesizer rewrites, connects, and weighs.
  Worker outputs are raw material.
- **Heavy markdown formatting**: No bold, no italics, minimal headers (H2 only for sections, H3
  rarely inside long sections). Prose does the work.

## Prefill trick

Instructing the synthesizer to begin its output with `# Executive Summary\n\n` — as a literal
prefill — is a surprisingly powerful anti-plan-mode countermeasure. A prefilled section heading is
structurally incompatible with "I will first cover...". The model simply cannot produce that
preamble from that starting position.

Pass the prefill as the assistant turn's opening in the Agent tool's prompt: the synthesizer agent's
output will continue from that heading directly into the executive summary body.
