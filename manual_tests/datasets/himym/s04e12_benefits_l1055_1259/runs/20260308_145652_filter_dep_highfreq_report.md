# MWE Evaluation Report

## Run Metadata
- Run ID: `20260308_145652_filter_dep_highfreq`
- Generated at (UTC): `2026-03-08T14:56:52.736842+00:00`

## Dataset Scope
- Source file: `data/himym_full_transcripts.csv`
- Evaluated slice: `s04e12_benefits_l1055_1259` (contiguous proxy episode)
- Slice definition: `line_index` 1055-1259 (205 dialogue lines)
- Prediction input lines: 26 gold-covered lines only

## Files
- Gold annotations: `manual_tests/datasets/himym/s04e12_benefits_l1055_1259/gold.csv`
- Engine predictions: `manual_tests/datasets/himym/s04e12_benefits_l1055_1259/runs/20260308_145652_filter_dep_highfreq_predictions.csv`

## Overall Metrics
- Gold instances: 27
- Predicted instances: 41
- True Positives (TP): 22
- False Positives (FP): 19
- False Negatives (FN): 5
- Precision: 0.5366
- Recall: 0.8148
- F1 score: 0.6471

## By Expression Type
### Phrasal Verbs
- Gold: 13
- Predicted: 26
- TP: 8
- FP: 18
- FN: 5
- Precision: 0.3077
- Recall: 0.6154
- F1: 0.4103

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

- line 1091 | phrasal_verb | `read in` |  I was working and I had to take a leap here...reading this magazine. In... the room there.

- line 1116 | phrasal_verb | `sex up` |  Absolutely! Let's multitasking. Use sex to spice up the boring activities.

- line 1116 | phrasal_verb | `use to` |  Absolutely! Let's multitasking. Use sex to spice up the boring activities.

- line 1116 | phrasal_verb | `use up` |  Absolutely! Let's multitasking. Use sex to spice up the boring activities.

- line 1116 | phrasal_verb | `used to` |  Absolutely! Let's multitasking. Use sex to spice up the boring activities.

- line 1164 | phrasal_verb | `get out!` |  No, it's wrong. You must learn to get it out. As we did in my kindergarten class. "The time for emotions", every Tuesday morning.

- line 1183 | phrasal_verb | `come on` |  Come on, Lily. Do not your Ted.

- line 1209 | phrasal_verb | `want in` |  Because of your bickering roommates are always a source of conflict between you two, I wanted to help. In fact, I went to the post. I took you stamps. In about 10 000. That should be enough.

- line 1209 | phrasal_verb | `want to` |  Because of your bickering roommates are always a source of conflict between you two, I wanted to help. In fact, I went to the post. I took you stamps. In about 10 000. That should be enough.

- line 1223 | phrasal_verb | `sleep with` |  No. This is not true, no. This is not true, no. No. Robin is all yours, man. Exploding yourself with it. Now if you'll excuse me, I'll go sleep with other girls.

- line 1228 | phrasal_verb | `sleep with` |  And I went with a bang. Why did I do that? It comes perhaps my father issues, but... basically, I allowed my best friend to sleep with the girl of my dreams. I completely sabotaged. And now, I smoke. I smoke.

- line 1241 | phrasal_verb | `point to` |  Thank you. I would have done well at some point.Sometimes you have to... You have to say and... go there.

- line 1241 | phrasal_verb | `thank you` |  Thank you. I would have done well at some point.Sometimes you have to... You have to say and... go there.

- line 1242 | idiom | `in fact` |  Marshall, I gotta go. In fact, there are toilets here, if you want to use.

- line 1242 | phrasal_verb | `want to` |  Marshall, I gotta go. In fact, there are toilets here, if you want to use.

- line 1255 | phrasal_verb | `hang with` |  Right. It's not like you, you know? In addition, we are friends. I want to complicate matters by committing. Hanging out with friends never works. So... you want to go eat a taco?

- line 1255 | phrasal_verb | `want to` |  Right. It's not like you, you know? In addition, we are friends. I want to complicate matters by committing. Hanging out with friends never works. So... you want to go eat a taco?

- line 1259 | phrasal_verb | `come on` |  Come on, I'm hungry.


## Example False Negatives (up to 20)
- line 1087 | phrasal_verb | `back together` |  You do not care what, guys? You are back together?

- line 1178 | phrasal_verb | `go wrong` |  No. It meant nothing. It was just a reflex when we were a couple. But I did everything go wrong.

- line 1204 | phrasal_verb | `go well` |  Everything was going well. I felt more and more comfortable, more confident. I could conquer the world. One morning I'm in the eighth with a magazine.

- line 1229 | phrasal_verb | `get out of` |  Get out of here.

- line 1245 | phrasal_verb | `look for` |  I go step-louse. If you are looking for Ted, he was released. And... our little arrangement is... completed, by the way.

