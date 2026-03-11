# MWE Evaluation Report

## Run Metadata
- Run ID: `20260308_145055_filter_none`
- Generated at (UTC): `2026-03-08T14:50:55.843068+00:00`

## Dataset Scope
- Source file: `data/himym_full_transcripts.csv`
- Evaluated slice: `s04e12_benefits_l1055_1259` (contiguous proxy episode)
- Slice definition: `line_index` 1055-1259 (205 dialogue lines)
- Prediction input lines: 26 gold-covered lines only

## Files
- Gold annotations: `manual_tests/datasets/himym/s04e12_benefits_l1055_1259/gold.csv`
- Engine predictions: `manual_tests/datasets/himym/s04e12_benefits_l1055_1259/runs/20260308_145055_filter_none_predictions.csv`

## Overall Metrics
- Gold instances: 27
- Predicted instances: 75
- True Positives (TP): 25
- False Positives (FP): 50
- False Negatives (FN): 2
- Precision: 0.3333
- Recall: 0.9259
- F1 score: 0.4902

## By Expression Type
### Phrasal Verbs
- Gold: 13
- Predicted: 60
- TP: 11
- FP: 49
- FN: 2
- Precision: 0.1833
- Recall: 0.8462
- F1: 0.3014

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
- line 1068 | phrasal_verb | `go it` |  No, I went there yesterday... Stop it! Stop it! My God, what happens? When we were a couple, we lived together and we almost went insane.

- line 1072 | phrasal_verb | `boil down to` |  I explained. I said, Madeline, every international conflict essentially boils down to sexual tension.

- line 1091 | phrasal_verb | `have to` |  I was working and I had to take a leap here...reading this magazine. In... the room there.

- line 1091 | phrasal_verb | `read in` |  I was working and I had to take a leap here...reading this magazine. In... the room there.

- line 1093 | phrasal_verb | `be to` |  If this is a problem. You've done all the way here to read a magazine? I am willing to bet that there is a place to read this magazine at work. You know, a room with a little man on the door?

- line 1093 | phrasal_verb | `have do` |  If this is a problem. You've done all the way here to read a magazine? I am willing to bet that there is a place to read this magazine at work. You know, a room with a little man on the door?

- line 1116 | phrasal_verb | `sex up` |  Absolutely! Let's multitasking. Use sex to spice up the boring activities.

- line 1116 | phrasal_verb | `use to` |  Absolutely! Let's multitasking. Use sex to spice up the boring activities.

- line 1116 | phrasal_verb | `use up` |  Absolutely! Let's multitasking. Use sex to spice up the boring activities.

- line 1116 | phrasal_verb | `used to` |  Absolutely! Let's multitasking. Use sex to spice up the boring activities.

- line 1164 | phrasal_verb | `do in` |  No, it's wrong. You must learn to get it out. As we did in my kindergarten class. "The time for emotions", every Tuesday morning.

- line 1164 | phrasal_verb | `get it` |  No, it's wrong. You must learn to get it out. As we did in my kindergarten class. "The time for emotions", every Tuesday morning.

- line 1164 | phrasal_verb | `get out!` |  No, it's wrong. You must learn to get it out. As we did in my kindergarten class. "The time for emotions", every Tuesday morning.

- line 1183 | phrasal_verb | `come on` |  Come on, Lily. Do not your Ted.

- line 1191 | phrasal_verb | `do it` |  This is for the best. It was fun, but I do not want it becoming weird.

- line 1204 | phrasal_verb | `be in` |  Everything was going well. I felt more and more comfortable, more confident. I could conquer the world. One morning I'm in the eighth with a magazine.

- line 1204 | phrasal_verb | `be with` |  Everything was going well. I felt more and more comfortable, more confident. I could conquer the world. One morning I'm in the eighth with a magazine.

- line 1209 | phrasal_verb | `go to` |  Because of your bickering roommates are always a source of conflict between you two, I wanted to help. In fact, I went to the post. I took you stamps. In about 10 000. That should be enough.

- line 1209 | phrasal_verb | `take in` |  Because of your bickering roommates are always a source of conflict between you two, I wanted to help. In fact, I went to the post. I took you stamps. In about 10 000. That should be enough.

- line 1209 | phrasal_verb | `want in` |  Because of your bickering roommates are always a source of conflict between you two, I wanted to help. In fact, I went to the post. I took you stamps. In about 10 000. That should be enough.


## Example False Negatives (up to 20)
- line 1087 | phrasal_verb | `back together` |  You do not care what, guys? You are back together?

- line 1204 | phrasal_verb | `go well` |  Everything was going well. I felt more and more comfortable, more confident. I could conquer the world. One morning I'm in the eighth with a magazine.

