
## Software Description

The application will operate on a large **corpus of textual data** consisting of:

* Movie transcripts
* TV series transcripts
* Books
* Scripts and other written materials

The system will allow users to **search the corpus using a word, phrase, idiom, or conceptual query**, and retrieve all relevant occurrences from the dataset.

---

## Retrieval Modes

The application will support two primary search modes:

### 1. Exact Match Search

This mode retrieves **literal matches** of the query in the corpus.
The system will also account for **morphological variations**, including:

* Different verb conjugations
* Plural forms
* Basic inflections of the same word

For example, a search for **“run”** may return:

* run
* runs
* running
* ran

The system may use **lemmatization or morphological normalization** to match different grammatical forms of the same word.

---

### 2. Semantic Search

This mode retrieves results based on **meaning rather than exact wording**.

Using **semantic similarity models** (such as vector embeddings), the system will return passages that are **conceptually related** to the query even if the exact words do not appear.

For example, a query for **“anger”** might return sentences containing:

* rage
* frustration
* furious
* lost his temper

This allows the system to capture **contextually relevant examples** that would not be found through literal matching.

---

## Retrieval of Idioms, Phrasal Verbs, and Collocations

The application will include specialized mechanisms to detect and retrieve **multi-word expressions**, including idioms, phrasal verbs, and collocations. These expressions are often semantically meaningful units that cannot be understood by analyzing each word independently.

### Idioms

Idioms are fixed expressions whose meanings are **non-literal** (e.g., *“kick the bucket,” “spill the beans,” “break the ice”*).

The system will detect idioms through:

* A **precompiled idiom lexicon**
* Pattern-based phrase matching
* Semantic detection for idiomatic usage in context

The system will retrieve occurrences even when the idiom appears with **minor grammatical variations**.

Example:

* “kick the bucket”
* “kicked the bucket”

---

### Phrasal Verbs

Phrasal verbs consist of a **verb combined with a particle** (e.g., *“give up,” “look after,” “run into”*).

The system will account for:

* **Particle separation**

  * “turn the lights off”
  * “turn off the lights”
* **Verb conjugation**

  * give up / gave up / giving up
* **Different syntactic placements**

This ensures that searches return all occurrences even when the phrasal verb is **split within the sentence structure**.

---

### Collocations

Collocations are **frequently co-occurring word combinations** that form natural language patterns (e.g., *“make a decision,” “heavy rain,” “strong argument”*).

The system will detect and retrieve collocations using:

* **Statistical co-occurrence analysis**
* Predefined collocation dictionaries
* Corpus-based frequency metrics (e.g., PMI or similar measures)

Users may search either:

* A **specific collocation** to retrieve the collocation occurance (“make a decision”)
* A **target word** to retrieve its common collocates occurances in the corpus (“decision” → make, reach, final, important)

---

## Output

For each retrieved occurrence, the system will return:

* The **matched text snippet**
* The **source** (movie, episode, book, etc.)
* The **exact location** within the source 
* An optional **context window** surrounding the match

