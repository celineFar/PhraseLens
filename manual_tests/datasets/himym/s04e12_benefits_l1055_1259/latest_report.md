# MWE Evaluation Report

## Run Metadata
- Run ID: `20260309_084806_gold-corrected`
- Generated at (UTC): `2026-03-09T08:48:06.742025+00:00`

## Dataset Scope
- Source: `manual_tests/datasets/himym/s04e12_benefits_l1055_1259/gold.csv (gold_only)`
- Evaluated slice: `s04e12_benefits_l1055_1259` (contiguous proxy episode)
- Slice definition: `line_index` 1061-1259 (199 dialogue lines)
- Prediction input lines: 26 gold-covered lines only
- Match mode: `ignore_type` (`ignore_type` treats same expression text as correct even with different expression_type)

## Files
- Gold annotations: `manual_tests/datasets/himym/s04e12_benefits_l1055_1259/gold.csv`
- Engine predictions: `manual_tests/datasets/himym/s04e12_benefits_l1055_1259/runs/20260309_084806_gold-corrected_predictions.csv`

## Overall Metrics
- Gold instances: 29
- Predicted instances: 31
- True Positives (TP): 23
- False Positives (FP): 8
- False Negatives (FN): 6
- Precision: 0.7419
- Recall: 0.7931
- F1 score: 0.7667

## By Expression Type
### Phrasal Verbs
- Gold: 15
- Predicted: 19
- TP: 9
- FP: 10
- FN: 6
- Precision: 0.4737
- Recall: 0.6000
- F1: 0.5294

### Idioms
- Gold: 14
- Predicted: 14
- TP: 14
- FP: 0
- FN: 0
- Precision: 1.0000
- Recall: 1.0000
- F1: 1.0000

## Example False Positives (up to 20)
- line 1072 | * | `boil down to` | I explained. I said, Madeline, every international conflict essentially boils down to sexual tension.
- line 1164 | * | `get out!` | No, it's wrong. You must learn to get it out. As we did in my kindergarten class. "The time for emotions", every Tuesday morning.
- line 1211 | * | `take in` | I took it in passing. It's nothing.
- line 1228 | * | `sleep with` | And I went with a bang. Why did I do that? It comes perhaps my father issues, but... basically, I allowed my best friend to sleep with the girl of my dreams. I completely sabotaged. And now, I smoke. I smoke.
- line 1229 | * | `get out` | Get out of here.
- line 1229 | * | `get out!` | Get out of here.
- line 1241 | * | `do better` | Thank you. I would have done well at some point.
- line 1255 | * | `hang with` | Right. It's not like you, you know? In addition, we are friends. I want to complicate matters by committing. Hanging out with friends never works. So... you want to go eat a taco?

## Example False Negatives (up to 20)
- line 1087 | * | `back together` | You do not care what, guys? You are back together?
- line 1178 | * | `go wrong` | No. It meant nothing. It was just a reflex when we were a couple. But I did everything go wrong.
- line 1204 | * | `go well` | Everything was going well. I felt more and more comfortable, more confident. I could conquer the world. One morning I'm in the eighth with a magazine.
- line 1223 | * | `sleep with` | No. This is not true, no. This is not true, no. No. Robin is all yours, man. 
- line 1241 | * | `go there` | Thank you. I would have done well at some point.
- line 1245 | * | `look for` | And... our little arrangement is... completed, by the way.
