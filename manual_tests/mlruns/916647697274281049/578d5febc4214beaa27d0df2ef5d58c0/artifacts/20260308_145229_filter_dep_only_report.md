# MWE Evaluation Report

## Run Metadata
- Run ID: `20260308_145229_filter_dep_only`
- Generated at (UTC): `2026-03-08T14:52:29.300661+00:00`

## Dataset Scope
- Source file: `data/himym_full_transcripts.csv`
- Evaluated slice: `s04e12_benefits_l1055_1259` (contiguous proxy episode)
- Slice definition: `line_index` 1055-1259 (205 dialogue lines)
- Prediction input lines: 26 gold-covered lines only

## Files
- Gold annotations: `manual_tests/datasets/himym/s04e12_benefits_l1055_1259/gold.csv`
- Engine predictions: `manual_tests/datasets/himym/s04e12_benefits_l1055_1259/runs/20260308_145229_filter_dep_only_predictions.csv`

## Overall Metrics
- Gold instances: 27
- Predicted instances: 24
- True Positives (TP): 19
- False Positives (FP): 5
- False Negatives (FN): 8
- Precision: 0.7917
- Recall: 0.7037
- F1 score: 0.7451

## By Expression Type
### Phrasal Verbs
- Gold: 13
- Predicted: 9
- TP: 5
- FP: 4
- FN: 8
- Precision: 0.5556
- Recall: 0.3846
- F1: 0.4545

### Idioms
- Gold: 14
- Predicted: 15
- TP: 14
- FP: 1
- FN: 0
- Precision: 0.9333
- Recall: 1.0000
- F1: 0.9655

## Example False Positives (up to 20)
- line 1072 | phrasal_verb | `boil down to` |  I explained. I said, Madeline, every international conflict essentially boils down to sexual tension.

- line 1164 | phrasal_verb | `get out!` |  No, it's wrong. You must learn to get it out. As we did in my kindergarten class. "The time for emotions", every Tuesday morning.

- line 1183 | phrasal_verb | `come on` |  Come on, Lily. Do not your Ted.

- line 1242 | idiom | `in fact` |  Marshall, I gotta go. In fact, there are toilets here, if you want to use.

- line 1259 | phrasal_verb | `come on` |  Come on, I'm hungry.


## Example False Negatives (up to 20)
- line 1068 | phrasal_verb | `live together` |  No, I went there yesterday... Stop it! Stop it! My God, what happens? When we were a couple, we lived together and we almost went insane.

- line 1087 | phrasal_verb | `back together` |  You do not care what, guys? You are back together?

- line 1110 | phrasal_verb | `end in` |  No. It could ruin your friendship. When two former try the "right opportunity", someone always ends in pain.

- line 1169 | phrasal_verb | `lie around` |  Sure, it was a good one. Personal memo: leave it lying around the pizza box more often.

- line 1178 | phrasal_verb | `go wrong` |  No. It meant nothing. It was just a reflex when we were a couple. But I did everything go wrong.

- line 1204 | phrasal_verb | `go well` |  Everything was going well. I felt more and more comfortable, more confident. I could conquer the world. One morning I'm in the eighth with a magazine.

- line 1229 | phrasal_verb | `get out of` |  Get out of here.

- line 1245 | phrasal_verb | `look for` |  I go step-louse. If you are looking for Ted, he was released. And... our little arrangement is... completed, by the way.

