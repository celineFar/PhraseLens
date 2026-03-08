# Root Cause Analysis: MWE Engine False Positives

**Dataset:** s01e01_proxy_l0000_0220 (221 dialogue lines)
**Run:** 20260307_063831
**Key numbers:** Precision 17.3%, Recall 100%, F1 29.5% (86 FP, 0 FN)

---

## Executive Summary

The MWE engine achieves perfect recall but very low precision (17.3%) due to
over-detection of phrasal verbs. The 86 false positives break down into five
root causes. The dominant issue (~48% of FPs) is the engine treating ordinary
**verb + preposition** combinations (e.g., "go to", "be in") as phrasal verbs.
The engine performs pure lemma co-occurrence matching with no syntactic
validation, meaning any sentence containing a verb lemma and a particle lemma
within the gap window triggers a match.

---

## False Positive Categorization

| Category | Count | % of FPs | Example |
|---|---|---|---|
| 1. Prepositional verbs misidentified as phrasal | ~41 | 48% | "go to Hartford", "be in town" |
| 2. Cross-clause/boundary spurious matches | ~9 | 10% | "have...up on him" -> `have up` |
| 3. Stage direction matches | ~7 | 8% | "[pulls the CD out]" -> `pull out` |
| 4. Debatable: genuine PVs not in gold | ~13 | 15% | "hold on", "come on", "go on" |
| 5. Long-line amplification (compounds above) | ~16 | 19% | line 74: 10 FPs from 465-char line |

---

## Root Cause #1: No Distinction Between Phrasal Verbs and Prepositional Verbs (48% of FPs)

**Problem:** The engine treats any `verb + preposition` combination found in
the lexicon as a phrasal verb, but linguistically these are different:

- **Phrasal verb:** "give up" (idiomatic, particle modifies verb meaning)
- **Prepositional verb:** "go to Hartford" (preposition heads a PP complement)

The wecan lexicon contains **3,353 entries** including highly common
prepositional combinations:

| Verb | Lexicon entries | Includes |
|---|---|---|
| get | 70 | get to, get in, get on, get over, ... |
| go | 60 | go to, go in, go on, go with, ... |
| come | 54 | come to, come in, come on, ... |
| be | 27 | be in, be on, be off, be up, ... |
| look | 23 | look at, look to, look for, ... |
| take | 24 | take in, take to, take on, ... |

Entries like `go to`, `be in`, `look at` match in virtually every dialogue line
that contains these extremely common words, producing the top FP expressions:

```
go to:  10 FPs    be in:  5 FPs    be on:  4 FPs
get to:  3 FPs    look at:  2 FPs  look to:  2 FPs
have on:  2 FPs   come to:  2 FPs  have in:  2 FPs
```

**Code location:** [run_mwe_eval.py:337-348](/manual_tests/run_mwe_eval.py#L337-L348) -
every phrasal verb in the lexicon is tested against every line via lemma
matching, with no filtering for syntactic role.

**Code location:** [phrasal_verbs.py:105-139](/app/search/mwe/phrasal_verbs.py#L105-L139) -
`_find_phrasal_verb_positions` matches purely on lemma equality within a gap
window, with no POS tag or dependency parse validation.

### Improvement Options

**Option A: Syntactic filtering via spaCy dependency parse (recommended, high impact)**

Use spaCy's dependency parser to verify that the particle token is syntactically
attached to the verb (dep label `prt`) rather than heading a prepositional
phrase (dep label `prep`). This is the standard NLP approach:

```python
# Pseudocode
for token in doc:
    if token.lemma_ == verb_lemma:
        for child in token.children:
            if child.lemma_ == particle_lemma and child.dep_ == "prt":
                # True phrasal verb
```

- Expected impact: Eliminates ~80% of Category 1 FPs
- Cost: Requires dependency-parsed tokens stored in DB (or on-the-fly parsing)
- Risk: spaCy's parser isn't perfect; some edge cases may slip through

**Option B: Lexicon curation - remove/tag prepositional entries**

Tag lexicon entries as `"type": "prepositional"` vs `"type": "phrasal"` and
only match true phrasal verbs by default. Remove or demote entries like `go to`,
`be in`, `look at`, `come to` that are almost always prepositional.

- Expected impact: Eliminates ~40-60% of Category 1 FPs
- Cost: Manual effort to classify 3,353 entries (could be semi-automated)
- Risk: Some entries are ambiguous (e.g., "look into" can be phrasal or prepositional)

**Option C: Frequency-based filtering**

If a verb+particle pair matches in >X% of lines, it's likely a prepositional
verb. Apply a corpus-frequency penalty or threshold.

- Expected impact: Eliminates the highest-frequency FPs (go to, be in, etc.)
- Cost: Low implementation effort
- Risk: May filter out genuine high-frequency phrasal verbs

---

## Root Cause #2: Excessive Gap Tolerance Causes Cross-Boundary Matches (10% of FPs)

**Problem:** The matching algorithm uses `max_gap=3` for inseparable phrasal
verbs and `max_gap=6` for separable ones
([run_mwe_eval.py:347](manual_tests/run_mwe_eval.py#L347)). This allows
matching a verb and particle that appear in **different clauses** or
**different phrases**.

Examples:
- `have up` on line 74: "have no idea... hung **up** on him" (verb and particle 30+ tokens apart, matched via intermediate co-occurrences)
- `pass on` on line 14: "**pass**ing through **on** my way" (preposition "on" belongs to "on my way", not to "pass")
- `see to` on line 74: "**see**, I'd have **to** build" (comma-separated clause boundary)
- `make with` on line 97: "**make** any inroads **with** Eminem"

**Code location:** [phrasal_verbs.py:127-134](app/search/mwe/phrasal_verbs.py#L127-L134) -
the gap counter resets on each matched token, effectively allowing unbounded
total distance as long as intermediate lemmas match.

### Improvement Options

**Option A: Sentence-boundary enforcement (recommended)**

Split each line into sentences before matching. Only match verb and particle
within the same sentence.

- Expected impact: Eliminates most cross-clause matches in long lines
- Cost: Low (spaCy already provides sentence segmentation)

**Option B: Reduce max_gap values**

Reduce `max_gap` from 3 to 1 for inseparable, and from 6 to 3 for separable.

- Expected impact: Moderate reduction in FPs
- Cost: Very low
- Risk: May increase false negatives for legitimately separated phrasal verbs

**Option C: Absolute token distance cap**

Instead of just a gap counter, also enforce a maximum absolute token distance
between verb and particle (e.g., 8 tokens max).

- Expected impact: Eliminates long-distance spurious matches
- Cost: Very low

---

## Root Cause #3: Stage Directions Parsed as Dialogue (8% of FPs)

**Problem:** Bracket-enclosed stage directions like `[pulls the CD out]`,
`[hangs up]`, `[Drella stops behind a woman]`, `[calls]` are included in the
text and parsed as regular dialogue, generating false phrasal verb matches.

Examples:
- `pull out` on line 41: from `[pulls the CD out of her purse]`
- `stop behind` on line 66: from `[Drella stops behind a woman]`
- `hang up` on line 78: from `[hangs up]`
- `call off` on line 186: "**[calls]**... half **off**"
- `bang on` on line 207: "My **bangs**... Go **on**" (noun "bangs" lemmatized to "bang")

**Code location:** [run_mwe_eval.py:333-335](manual_tests/run_mwe_eval.py#L333-L335) -
the entire `row["line"]` is processed including bracket content.

### Improvement Options

**Option A: Strip stage directions before analysis (recommended)**

Remove `[...]` content from lines before NLP processing:

```python
import re
clean_line = re.sub(r"\[.*?\]", "", row["line"])
```

- Expected impact: Eliminates all Category 3 FPs
- Cost: Very low (one regex)
- Risk: Some datasets may use brackets for other purposes

**Option B: Tag and filter at display time**

Keep stage directions in processing but tag matches that occur within brackets
and let the user filter them.

---

## Root Cause #4: Debatable Cases - Gold Annotation Gaps (15% of FPs)

**Problem:** Some engine predictions appear to be **genuine phrasal verbs**
that the gold standard didn't annotate:

| Expression | Line | Context | Assessment |
|---|---|---|---|
| `hold on` | 74 | "Hold on, I'll look" | Genuine PV (interjection) |
| `come on` | 90, 171 | "Come on, Michel" / "Oh, come on" | Genuine PV (interjection) |
| `go on` | 207, 217 | "Go on, go on" / "What's going on?" | Genuine PV |
| `hang up` | 74, 78 | "[hung up on him]" / "[hangs up]" | Genuine PV (in stage dirs) |
| `start on` | 111 | "start on your essay" | Genuine PV |
| `put on` | 131 | "put it on the waffles" | Likely prepositional, debatable |
| `get in` | 202, 204 | "Rory got in" | Genuine PV (accepted/admitted) |

### Improvement Options

**Option A: Expand gold annotations**

Review and add missing genuine phrasal verbs to the gold standard. This would
convert ~13 FPs into TPs, improving precision from 17.3% to ~34%.

**Option B: Define annotation guidelines more precisely**

Clarify what counts as a "phrasal verb" in the gold standard (e.g., include
interjections like "come on"? include stage directions?).

---

## Root Cause #5: Long Lines Amplify All Other Issues (19% of FPs)

**Problem:** Longer dialogue lines contain more verb and preposition tokens,
leading to combinatorial explosion of matches:

| Line | Chars | FPs | Content |
|---|---|---|---|
| 74 | 465 | 10 | Michel's phone monologue |
| 109 | 111 | 8 | Rory's hayride complaint |
| 178 | 228 | 4 | Mrs. Kim's muffin speech |
| 138 | 80 | 4 | Lorelai's "on three" line |

Line 74 alone accounts for **11.6% of all FPs** because it contains many
verbs and prepositions that get combined across clause boundaries.

### Improvement Options

**Option A: Sentence-level matching (same as RC#2 Option A)**

Process each sentence independently rather than the whole line. This naturally
limits the combinatorial space.

**Option B: Max predictions per line**

Cap the number of phrasal verb predictions per line (e.g., top 3 by confidence).

---

## Recommended Action Plan

Ordered by expected impact and implementation cost:

| Priority | Action | Expected Precision Gain | Effort |
|---|---|---|---|
| P0 | Strip stage directions `[...]` before analysis | +2-3 pp | 1 hour |
| P0 | Expand gold annotations for genuine PVs | +8-10 pp | 2 hours |
| P1 | Add sentence-boundary segmentation | +5-8 pp | Half day |
| P1 | Syntactic filtering via dep parse (`prt` vs `prep`) | +25-35 pp | 1-2 days |
| P2 | Reduce max_gap values (3->1 insep, 6->3 sep) | +3-5 pp | 30 min |
| P3 | Lexicon curation: tag/remove prepositional entries | +10-15 pp | 2-3 days |

**Projected precision after P0+P1 fixes:** ~55-65% (up from 17.3%)
**Projected precision after all fixes:** ~75-85%

---

## Appendix: Full FP Expression Frequency

```
go to:     10    be in:      5    be on:      4    get to:     3
hang up:    2    be off:     2    go on:      2    have in:    2
have on:    2    get in:     2    come to:    2    look at:    2
look to:    2    come on:    2    take in:    1    have up:    1
bundle up:  1    go with:    1    know from:  1    get over:   1
sit for:    1    sit in:     1    sit in for: 1    be on about:1
stick up:   1    bag up:     1    stop behind:1    pull out:   1
pass on:    1    pass on to: 1    hold on:    1    hang on:    1
hang up on: 1    look through:1   see to:     1    try for:    1
do with:    1    make of:    1    make with:  1    key to:     1
let up:     1    get on:     1    get up to:  1    get out:    1
get out!:   1    get it:     1    soak in:    1    know of:    1
come of:    1    come with:  1    call off:   1    call by:    1
bang on:    1    go in:      1    hear from:  1    point to:   1
start on:   1    put on:     1
                                        Total: 86 FPs across 58 unique expressions
```
