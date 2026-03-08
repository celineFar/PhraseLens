# MWE Evaluation Report

## Run Metadata
- Run ID: `20260308_052938_dep_parse_filter`
- Generated at (UTC): `2026-03-08T05:29:38.876830+00:00`

## Dataset Scope
- Source file: `data/Gilmore_Girls_Lines.csv`
- Evaluated slice: `s01e01_proxy_l0000_0220` (contiguous proxy episode)
- Slice definition: `line_index` 0-220 (221 dialogue lines)
- Prediction input lines: 18 gold-covered lines only

## Files
- Gold annotations: `manual_tests/datasets/gilmore_girls/s01e01_proxy_l0000_0220/gold.csv`
- Engine predictions: `manual_tests/datasets/gilmore_girls/s01e01_proxy_l0000_0220/runs/20260308_052938_dep_parse_filter_predictions.csv`

## Overall Metrics
- Gold instances: 18
- Predicted instances: 10
- True Positives (TP): 9
- False Positives (FP): 1
- False Negatives (FN): 9
- Precision: 0.9000
- Recall: 0.5000
- F1 score: 0.6429

## By Expression Type
### Phrasal Verbs
- Gold: 16
- Predicted: 8
- TP: 7
- FP: 1
- FN: 9
- Precision: 0.8750
- Recall: 0.4375
- F1: 0.5833

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
- line 138 | phrasal_verb | `get up to` | All right. So, now, let's get you up and to the doctor, on three. One-two-three.

## Example False Negatives (up to 20)
- line 24 | phrasal_verb | `get going` | So I guess I should get going.
- line 27 | phrasal_verb | `screw with` | I'm just screwing with your mind, Joey. It's nice to meet you. Enjoy Hartford.
- line 53 | phrasal_verb | `get to know` | Getting to know my daughter.
- line 72 | phrasal_verb | `look for` | Okay. I am a great harp player, and this is my great harp, okay. So if you're looking for someone to just be nice to the guests, get a harmonica player, or maybe some guy who whistles through his nose. Okay? Capisce?
- line 75 | phrasal_verb | `attend to` | Has the plumber attended to room four yet?
- line 77 | phrasal_verb | `talk to` | Hi Marco, Lorelai. Talk to me about room four. What was wrong with it?
- line 86 | phrasal_verb | `look at` | Ooh, hey, have Michel look at your French paper before you go.
- line 104 | phrasal_verb | `plan ahead` | Well, my parents like to plan ahead.
- line 141 | phrasal_verb | `step on` | Stepped on my thumb. I'm fine. On three. Okay.
