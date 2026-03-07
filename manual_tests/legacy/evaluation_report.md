# MWE Evaluation Report

## Dataset Scope
- Source file: `data/Gilmore_Girls_Lines.csv`
- Evaluated slice: `s01e01_proxy_l0000_0220` (contiguous proxy episode)
- Slice definition: Season 1, `line_index` 0-220 (221 dialogue lines)
- Note: this CSV has no explicit episode-id column, so this evaluation uses a transparent contiguous proxy slice.

## Files
- Gold annotations: `manual_tests/s01e01_proxy_l0000_0220_gold.csv`
- Engine predictions: `manual_tests/s01e01_proxy_l0000_0220_predictions.csv`

## Overall Metrics
- Gold instances: 18
- Predicted instances: 74
- True Positives (TP): 18
- False Positives (FP): 56
- False Negatives (FN): 0
- Precision: 0.2432
- Recall: 1.0000
- F1 score: 0.3913

## By Expression Type
### Phrasal Verbs
- Gold: 16
- Predicted: 72
- TP: 16
- FP: 56
- FN: 0
- Precision: 0.2222
- Recall: 1.0000
- F1: 0.3636

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
- line 66 | phrasal_verb | `stop behind` | Oh, no, don't move. Just ignore the tiny woman pushing the 200-pound instrument around. No, this is good, I like this. After this I'll, uh, bench press a piano, huh? [Drella stops behind a woman bent over tying her shoe.] Oh, that's it, lady, tie your shoe now. Yeah, don't worry, I'll wait.
- line 74 | phrasal_verb | `hang on` | Madame, you have no idea how desperately I'd like to help, but see, I'd have to build a room for you myself, and I am not a man who works with his hands, so the best I can do is suggest that you please, please try for another weekend. Any weekend. [pause] Ah, good, fine, the twenty-first. Hold on, I'll look. [Michel leafs through the reservation book] No, I'm sorry, we're completely booked. [Michel looks at the phone, as apparently the woman has hung up on him]
- line 74 | phrasal_verb | `hang up` | Madame, you have no idea how desperately I'd like to help, but see, I'd have to build a room for you myself, and I am not a man who works with his hands, so the best I can do is suggest that you please, please try for another weekend. Any weekend. [pause] Ah, good, fine, the twenty-first. Hold on, I'll look. [Michel leafs through the reservation book] No, I'm sorry, we're completely booked. [Michel looks at the phone, as apparently the woman has hung up on him]
- line 74 | phrasal_verb | `hang up on` | Madame, you have no idea how desperately I'd like to help, but see, I'd have to build a room for you myself, and I am not a man who works with his hands, so the best I can do is suggest that you please, please try for another weekend. Any weekend. [pause] Ah, good, fine, the twenty-first. Hold on, I'll look. [Michel leafs through the reservation book] No, I'm sorry, we're completely booked. [Michel looks at the phone, as apparently the woman has hung up on him]
- line 74 | phrasal_verb | `have up` | Madame, you have no idea how desperately I'd like to help, but see, I'd have to build a room for you myself, and I am not a man who works with his hands, so the best I can do is suggest that you please, please try for another weekend. Any weekend. [pause] Ah, good, fine, the twenty-first. Hold on, I'll look. [Michel leafs through the reservation book] No, I'm sorry, we're completely booked. [Michel looks at the phone, as apparently the woman has hung up on him]
- line 74 | phrasal_verb | `hold on` | Madame, you have no idea how desperately I'd like to help, but see, I'd have to build a room for you myself, and I am not a man who works with his hands, so the best I can do is suggest that you please, please try for another weekend. Any weekend. [pause] Ah, good, fine, the twenty-first. Hold on, I'll look. [Michel leafs through the reservation book] No, I'm sorry, we're completely booked. [Michel looks at the phone, as apparently the woman has hung up on him]
- line 74 | phrasal_verb | `look at` | Madame, you have no idea how desperately I'd like to help, but see, I'd have to build a room for you myself, and I am not a man who works with his hands, so the best I can do is suggest that you please, please try for another weekend. Any weekend. [pause] Ah, good, fine, the twenty-first. Hold on, I'll look. [Michel leafs through the reservation book] No, I'm sorry, we're completely booked. [Michel looks at the phone, as apparently the woman has hung up on him]
- line 74 | phrasal_verb | `try for` | Madame, you have no idea how desperately I'd like to help, but see, I'd have to build a room for you myself, and I am not a man who works with his hands, so the best I can do is suggest that you please, please try for another weekend. Any weekend. [pause] Ah, good, fine, the twenty-first. Hold on, I'll look. [Michel leafs through the reservation book] No, I'm sorry, we're completely booked. [Michel looks at the phone, as apparently the woman has hung up on him]
- line 78 | phrasal_verb | `be on` | [on phone] Uh huh. I thought you replaced that already. [pause] Well, because you told me you did and I never forget anything, so this one's on you, right? [pause] Pleasure doing business with you. [hangs up]
- line 78 | phrasal_verb | `do with` | [on phone] Uh huh. I thought you replaced that already. [pause] Well, because you told me you did and I never forget anything, so this one's on you, right? [pause] Pleasure doing business with you. [hangs up]
- line 78 | phrasal_verb | `hang up` | [on phone] Uh huh. I thought you replaced that already. [pause] Well, because you told me you did and I never forget anything, so this one's on you, right? [pause] Pleasure doing business with you. [hangs up]
- line 84 | phrasal_verb | `make of` | No, I'm just saying, you couldn't find one made of metal in case anyone has X-ray eyes?
- line 90 | phrasal_verb | `come on` | Come on, Michel. I'll tell all the ladies what a stud you are.
- line 93 | phrasal_verb | `look at` | Leave it. I'll look at it if I get a chance.
- line 96 | phrasal_verb | `go to` | When are you going to let your parents know that you listen to the evil rock music? You're an American teenager, for God's sake.
- line 97 | phrasal_verb | `get over` | Rory, if my parents still get upset over the obscene portion size of American food, I seriously doubt I'm gonna make any inroads with Eminem.
- line 97 | phrasal_verb | `go to` | Rory, if my parents still get upset over the obscene portion size of American food, I seriously doubt I'm gonna make any inroads with Eminem.
- line 98 | phrasal_verb | `go to` | [points to sign] I have to go to that.
- line 98 | phrasal_verb | `point to` | [points to sign] I have to go to that.

## Example False Negatives (up to 20)
- None

## Analysis Summary
- The phrasal-verb detector is high-recall on verb+particle patterns but over-generates many prepositional combinations (`be in`, `go to`, `have on`) as MWEs.
- This creates strong recall but low precision in open-ended detection mode.
- Idiom detection here is evaluated against idioms present in the gold set for this slice.
