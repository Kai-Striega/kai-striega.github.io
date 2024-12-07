+++
title = 'Curiously Related Words Constructing Our Query'
date = 2024-12-08T08:25:52+11:00
+++

## Querying data

Neo4j uses a query language called [Cypher](https://neo4j.com/docs/cypher-manual/current/introduction/)[^1]. Cypher
was inspired by ASCII art and lets us represent our ideas very intuitively. Nodes are represented as being in
parentheses while relationships are shown as arrows between nodes. If you have some spare time I'd suggest you play 
around with Cypher before continuing to familiarize yourself.

## What did we want?

If we go way back to
the [original post](https://kaistriega.com/blog/curiously-related-words/what-is-a-curiously-related-word/)
we said we wanted two things:

1. The words had to share a common ancestor
2. The words had to have similar meanings

## Finding words with common ancestors

### Finding a word

Let's start with something simpler, how to find a single word. Let's try to find the word "potion"[^2]. To do this we'll
need to match a node $n$ where the ``lexeme`` property is ``potion``. And then return it.

```
MATCH (n: Lexeme)
WHERE n.lexeme = 'potion'
RETURN n
```

The Neo4j web interface gives us a really cool visualisation of the results:

![potion_query](/images/potion.svg)

But wait, why are there two? It turns out that EtymDB stores two versions of the word "potion", one in French and
one in English. We can see this by modifying our query to return both the word and the language

```
MATCH (n: Lexeme)
WHERE n.lexeme = 'potion'
RETURN n.lexeme AS Word, n.language AS Language
```

This query produces the following output:

|   | Word     | Language  |
|:-:|----------|-----------|
| 1 | "potion" | "English" |
| 2 | "potion" | "French"  |

### Finding relationships between words

We saw above that we can find nodes with certain properties. The same can be done for relationships. Cypher let us
query Neo4j with (what is basically) ASCII art. To find a relationship we can use an ``-[r:RELATIONSHIP_LABEL]->``,
where ``r`` allows us to check for properties on the relationship and ``RELATIONSHIP_LABEL`` allows us to filter to
one or more labels on the relationship.

What if we want to find all the words that English version of "potion" inherits from? We can do that with the following
query:

```
MATCH (w1: Lexeme)-[r:INHERITS_FROM]->(w2:Lexeme)
WHERE w1.lexeme = 'potion'
    AND w1.language = 'English'
RETURN w1, w2
```

Again Neo4j returns a pretty, visual representation of the results:

![All the nodes that inherit from potion](/images/potion_inheritance.svg)

That's ok, but we want to find the root words, not just the next word. There are two ways we can improve the
query:

1. [variable length relationship](https://neo4j.com/docs/cypher-manual/5/patterns/reference/#variable-length-relationships)
   to match multiple relationships.
2. Match multiple different labels for our relationships.

```
MATCH (w1: Lexeme)-[r:INHERITS_FROM *]->(w2:Lexeme)
WHERE w1.lexeme = 'potion'
    AND w1.language = 'English'
RETURN w1, w2
```

This gives us the full relationship from the English word "potion" to the Latin word "pōtō":

![potion inheritance from Latin](/images/potion_inheritance_full.svg)

### Finding the modern word with for the same ancestor

Ok, we've found the root word, but what about the modern word that we actually want? Turns out we can utilise the same
pattern in reverse to find a modern word, we're also going to filter the other word to only be English.

```
MATCH (w1: Lexeme) -[:INHERITS_FROM|BORROWS_FROM|der *]-> (root: Lexeme) <-[:INHERITS_FROM|BORROWS_FROM|der *]- (w2: Lexeme)
WHERE
    w1.lexeme = 'potion'
    AND w1.language = 'English'
    AND w2.language = 'English'
    AND w1.lexeme <> w2.lexeme
RETURN w1.lexeme AS source_word,  w2.lexeme AS connected_word
```

And this returns the following table:

|   | source_word | connected_word |
|:-:|-------------|----------------|
| 1 | "potion"    | "poison"       |
| 2 | "potion"    | "potable"      |
| 3 | "potion"    | "potable"      |

### Distinct results and paths

But wait, why does the same word appear twice? What's new here is that we're not only matching the final results,
we're matching the [path](https://en.wikipedia.org/wiki/Path_(graph_theory)) that gets us there. In this case, there
are two unique ways to traverse our graph from "potion" to "potable", so we get two results. We can avoid this
duplication by using the `DISTINCT` keyword. The query would look like:

```
MATCH (w1: Lexeme) -[:INHERITS_FROM|BORROWS_FROM|der *]-> (root: Lexeme) <-[:INHERITS_FROM|BORROWS_FROM|der *]- (w2: Lexeme)
WHERE
    w1.lexeme = 'potion'
    AND w1.language = 'English'
    AND w2.language = 'English'
    AND w1.lexeme <> w2.lexeme
RETURN DISTINCT w1.lexeme AS source_word,  w2.lexeme AS connected_word
```

and give us the same table as before, without the duplicate row. We can now find words with a common ancestor for
any given word. Hooray!

## Finding word similarity

What about the other requirement? The two words need to have dissimilar meanings. Using the embeddings on the node,
we can compute the distance between given pairs of words. Luckily Neo4j already provides the
[vector functions](https://neo4j.com/docs/cypher-manual/current/functions/vector/) which includes two distance
functions:

1. [cosine](https://neo4j.com/docs/cypher-manual/current/functions/vector/#functions-similarity-cosine): Looks at
   the angles between vectors, meaning that the magnitude of the vectors is not taken into account
2. [euclidean](https://neo4j.com/docs/cypher-manual/current/functions/vector/#functions-similarity-euclidean): Looks
   at the "straight line" distance between the points. This is similar to using a ruler to measure the distance
   between points

Our embedding is in a 200 dimensional space, so we're going to suffer from
the [Curse of Dimensionality](https://en.wikipedia.org/wiki/Curse_of_dimensionality)
regardless of the metric. Having our vectors point in the same direction is already pretty good, so lets use that as
our definition of similarity. Cosine distance it is.

```
MATCH (w1: Lexeme) -[:INHERITS_FROM|BORROWS_FROM|der *]-> (root: Lexeme) <-[:INHERITS_FROM|BORROWS_FROM|der *]- (w2: Lexeme)
WHERE
    w1.lexeme = 'potion'
    AND w1.language = 'English'
    AND w2.language = 'English'
    AND w1.lexeme <> w2.lexeme
RETURN DISTINCT w1.lexeme AS source_word,  w2.lexeme AS connected_word, vector.similarity.cosine(w1.embedding, w2.embedding) AS similarity
ORDER BY similarity
```

Here we're modifying our query to include the cosine similarity, we're also ordering by similarity to make it easier
to see which ones are dissimilar. The above query gives the following output:

|   | source_word | connected_word | similarity         |
|:-:|-------------|----------------|--------------------|
| 1 | "potion"    | "poison"       | 0.6835019588470459 |
| 2 | "potion"    | "potable"      | 0.5666762590408325 |


## All connected words

To find __all__ connected words we simply need to remove the ``w1.lexeme = 'potion'`` constraint from our previous 
query. This gives 20250 records. Take a second to play around with the values, do you notice any cool pairs?

## Future Work and Ideas for Improvement

There are still several shortcomings to my algorithm. If __you__ have any ideas on how to fix these I'd be happy to 
hear them.

### Semantic similarity threshold

We are given the similarity for each word, however I haven't yet found a good way to derive a threshold for 
similarity. This should be automated _somehow_.

### Lexicographical similarity threshold

Words that are spelt very similarly are often obviously related. For example the words "though" and "think" both 
share a common ancestor and are very closely related semantically. However, I would not consider this curious, as 
they are very closely related. There should be some way to filter out words with very similar spelling (maybe via the 
[edit distance](https://en.wikipedia.org/wiki/Edit_distance))

### More friendly UX

The solution requires knowing Docker and manually moving files around on your computer. I'd like to wrap this in a 
webapp to make it more accessible to others.

[^1]: and Graph Query Language (GQL)
[^2]: I happen to like magic
[^3]: The records are kind of duplicated for example both "potion" -> "poison" and "poison" -> "potion" appear in 
the results. I'm yet to find a way to filter these out.