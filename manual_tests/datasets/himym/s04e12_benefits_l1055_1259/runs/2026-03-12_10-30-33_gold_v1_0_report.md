# MWE Evaluation Report

## Run Metadata
- Run ID: `2026-03-12_10-30-33_gold_v1_0`
- Generated at (UTC): `2026-03-12T10:30:33.763390+04:00`
- Run notes: `batch idiom lemmatization` 

## Dataset Scope
- Source: `manual_tests/datasets/himym/s04e12_benefits_l1055_1259/gold_v.1.0.csv (gold_only)`
- Evaluated slice: `s04e12_benefits_l1055_1259` (contiguous proxy episode)
- Slice definition: `line_index` 1061-1259 (199 dialogue lines)
- Prediction input lines: 26 gold-covered lines only
- Match mode: `ignore_type` (`ignore_type` treats same expression text as correct even with different expression_type)

## Files
- Gold annotations: `manual_tests/datasets/himym/s04e12_benefits_l1055_1259/gold_v.1.0.csv`
- Engine predictions: `manual_tests/datasets/himym/s04e12_benefits_l1055_1259/runs/2026-03-12_10-30-33_gold_v1_0_predictions.csv`

## Overall Metrics
- Gold instances: 29
- Predicted instances: 32
- True Positives (TP): 14
- False Positives (FP): 18
- False Negatives (FN): 15
- Precision: 0.4375
- Recall: 0.4828
- F1 score: 0.4590

## By Expression Type
### Phrasal Verbs
- Gold: 15
- Predicted: 16
- TP: 9
- FP: 7
- FN: 6
- Precision: 0.5625
- Recall: 0.6000
- F1: 0.5806

### Idioms
- Gold: 14
- Predicted: 16
- TP: 3
- FP: 13
- FN: 11
- Precision: 0.1875
- Recall: 0.2143
- F1: 0.2000

## Example False Positives (up to 20)
- line 1068 | * | `couple something together` | No, I went there yesterday... Stop it! Stop it! My God, what happens? When we were a couple, we lived together and we almost went insane.
- line 1072 | * | `boil down to` | I explained. I said, Madeline, every international conflict essentially boils down to sexual tension.
- line 1091 | * | `in there` | I was working and I had to take a leap here...reading this magazine. In... the room there.
- line 1093 | * | `at work` | If this is a problem. You've done all the way here to read a magazine? I am willing to bet that there is a place to read this magazine at work. You know, a room with a little man on the door?
- line 1093 | * | `room with someone` | If this is a problem. You've done all the way here to read a magazine? I am willing to bet that there is a place to read this magazine at work. You know, a room with a little man on the door?
- line 1093 | * | `that there` | If this is a problem. You've done all the way here to read a magazine? I am willing to bet that there is a place to read this magazine at work. You know, a room with a little man on the door?
- line 1110 | * | `end in something` | No. It could ruin your friendship. When two former try the "right opportunity", someone always ends in pain.
- line 1164 | * | `time for someone or something` | No, it's wrong. You must learn to get it out. As we did in my kindergarten class. "The time for emotions", every Tuesday morning.
- line 1191 | * | `all for the best` | This is for the best. It was fun, but I do not want it becoming weird.
- line 1191 | * | `for good` | This is for the best. It was fun, but I do not want it becoming weird.
- line 1204 | * | `more and more` | Everything was going well. I felt more and more comfortable, more confident. I could conquer the world. One morning I'm in the eighth with a magazine.
- line 1209 | * | `help someone in something` | Because of your bickering roommates are always a source of conflict between you two, I wanted to help. In fact, I went to the post. I took you stamps. In about 10 000. That should be enough.
- line 1209 | * | `help someone into something` | Because of your bickering roommates are always a source of conflict between you two, I wanted to help. In fact, I went to the post. I took you stamps. In about 10 000. That should be enough.
- line 1211 | * | `take in` | I took it in passing. It's nothing.
- line 1229 | * | `get out` | Get out of here.
- line 1241 | * | `do better` | Thank you. I would have done well at some point.
- line 1255 | * | `hang with` | Right. It's not like you, you know? In addition, we are friends. I want to complicate matters by committing. Hanging out with friends never works. So... you want to go eat a taco?
- line 1255 | * | `in addition to something` | Right. It's not like you, you know? In addition, we are friends. I want to complicate matters by committing. Hanging out with friends never works. So... you want to go eat a taco?

## Example False Negatives (up to 20)
- line 1087 | * | `back together` | You do not care what, guys? You are back together?
- line 1091 | * | `take a leap` | I was working and I had to take a leap here...reading this magazine. In... the room there.
- line 1131 | * | `see a psychiatrist` | You must learn to express your feelings. Perhaps you should see a psychiatrist.
- line 1170 | * | `see you later` | Okay, see you later.
- line 1178 | * | `go wrong` | No. It meant nothing. It was just a reflex when we were a couple. But I did everything go wrong.
- line 1191 | * | `for the best` | This is for the best. It was fun, but I do not want it becoming weird.
- line 1204 | * | `go well` | Everything was going well. I felt more and more comfortable, more confident. I could conquer the world. One morning I'm in the eighth with a magazine.
- line 1211 | * | `in passing` | I took it in passing. It's nothing.
- line 1223 | * | `all yours` | No. This is not true, no. This is not true, no. No. Robin is all yours, man. 
- line 1223 | * | `sleep with` | No. This is not true, no. This is not true, no. No. Robin is all yours, man. 
- line 1228 | * | `go with a bang` | And I went with a bang. Why did I do that? It comes perhaps my father issues.
- line 1241 | * | `at some point` | Thank you. I would have done well at some point.
- line 1241 | * | `go there` | Thank you. I would have done well at some point.
- line 1242 | * | `gotta go` | Marshall, I gotta go. 
- line 1245 | * | `look for` | And... our little arrangement is... completed, by the way.
