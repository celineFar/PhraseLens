# MWE Evaluation Report

## Run Metadata
- Run ID: `20260308_060457_filter_dep_extended`
- Generated at (UTC): `2026-03-08T06:04:57.309505+00:00`

## Dataset Scope
- Source file: `data/Gilmore_Girls_Lines.csv`
- Evaluated slice: `s01e01_proxy_l0000_0220` (contiguous proxy episode)
- Slice definition: `line_index` 0-220 (221 dialogue lines)
- Prediction input lines: 18 gold-covered lines only

## Files
- Gold annotations: `manual_tests/datasets/gilmore_girls/s01e01_proxy_l0000_0220/gold.csv`
- Engine predictions: `manual_tests/datasets/gilmore_girls/s01e01_proxy_l0000_0220/runs/20260308_060457_filter_dep_extended_predictions.csv`

## Overall Metrics
- Gold instances: 18
- Predicted instances: 16
- True Positives (TP): 12
- False Positives (FP): 4
- False Negatives (FN): 6
- Precision: 0.7500
- Recall: 0.6667
- F1 score: 0.7059

## By Expression Type
### Phrasal Verbs
- Gold: 16
- Predicted: 14
- TP: 10
- FP: 4
- FN: 6
- Precision: 0.7143
- Recall: 0.6250
- F1: 0.6667

### Idioms
- Gold: 2
- Predicted: 2
- TP: 2
- FP: 0
- FN: 0
- Precision: 1.0000
- Recall: 1.0000
- F1: 1.0000

## Example False Positives (up to 20)
- line 14 | phrasal_verb | `pass on` | Yeah, I've never been here before. Just, uh, passing through on my way to Hartford.
- line 14 | phrasal_verb | `pass on to` | Yeah, I've never been here before. Just, uh, passing through on my way to Hartford.
- line 138 | phrasal_verb | `get up to` | All right. So, now, let's get you up and to the doctor, on three. One-two-three.
- line 178 | phrasal_verb | `soak in` | KIM: Go upstairs. Tea is ready. I have muffins - no dairy, no sugar, no wheat. You have to soak them in tea to make them soft enough to bite but they're very healthy. So, how was school? None of the girls get pregnant, drop out?

## Example False Negatives (up to 20)
- line 24 | phrasal_verb | `get going` | So I guess I should get going.
- line 27 | phrasal_verb | `screw with` | I'm just screwing with your mind, Joey. It's nice to meet you. Enjoy Hartford.
- line 53 | phrasal_verb | `get to know` | Getting to know my daughter.
- line 75 | phrasal_verb | `attend to` | Has the plumber attended to room four yet?
- line 86 | phrasal_verb | `look at` | Ooh, hey, have Michel look at your French paper before you go.
- line 104 | phrasal_verb | `plan ahead` | Well, my parents like to plan ahead.
