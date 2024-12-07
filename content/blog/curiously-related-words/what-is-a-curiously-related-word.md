+++
title = 'What is a Curiously Related Word?'
date = 2024-12-07T12:53:46+11:00
+++

## Contents:

1. [What brought this on?](#what-brought-this-on)
2. [Defining a curiously related word pair](#an-informal-definition-of-curiously-related-words)
3. [Common Ancestors](#common-ancestors)
4. [Similar Meanings](#similar-meanings)
5. [The big ideas](#the-big-idea-of-our-algorithm)


## What brought this on?

Did you know that the words "Galaxy" and "Lactose" are related? They both derive from the Proto-Indo-European word 
"glakt" which means "Milk". I didn't. And, when a friend told me this, I was intrigued. As a computer nerd, this 
brought up another question: can I automate finding such words?

## An informal definition of curiously related words

Before automating something I need to define what I want to do. Which is, for a given English word, I want to find 
all the English words that are __curiously connected__. What does this mean?

Let's consider a pair of words we'll consider the pair as curiously connected iff:

1. They share a common ancestor
2. Their meanings are similar

Going back to our example I'd intuit the words "Galaxy" and "Lactose" to be curiously connected as the pair meet 
both conditions.

## Common ancestors

Etymology studies the origin of a word and the historical development of its meaning. That sounds like exactly what 
we want. After a quick Google I found [EtymDB](https://paperswithcode.com/dataset/etymdb-2-0), a database that 
contains many words, from different languages and their etymological relationships. From EtymDB, for a given word, 
we can find all of that words contemporary related words. For example, consider the pair "potion" and "poison". In 
EtymDB we can see that they share the same root word:

![The graph of the relationship between the words "poison" and "potion"](/images/poison-potion.svg "poison-potion-relationship")

Turns out the common ancestor is the Latin word "pōtiō". The words have then evolved into their respective 
words over time. Data in this format (things and relationships between them) is often called a _Graph_. While it is 
possible to analyse Graph data in Python, it required reconstructing the graph from EtymDB everytime. This took a 
long time (~30 mins) which isn't great. I'm planning to use [Neo4j](https://neo4j.com/) a databased designed to work 
efficiently with graphs. 

## Similar meanings

We've established that "potion" and "poison" share a common ancestor. They are connected. But are they _curiously_ 
connected? The second part of the definition is that their meanings need to be similar. This is easy to intuit, 
but hard to quantify. For that we need to computationally find the meaning of a word, and define some kind of 
distance metric between words. Now, if the distance between the two words is high enough, we consider them to be 
_curiously connected_.

How can I tell a computer what a word means? Ideally we'd want words that intuitively have similar meanings (to us) to 
be "close" to each other. This is called the [semantic similarity](https://en.wikipedia.org/wiki/Semantic_similarity)
where the distance between words tends to be based on their meaning. One way to analyse semantic similarity is to embed
the words in a [vector space](https://en.wikipedia.org/wiki/Vector_space). The big idea is that words with similar 
meanings influence the surrounding words in the similar ways.

Implementing this isn't too hard (maybe in another blog post!) but it is expensive, so I won't be training the model 
myself. Luckily these models (known collectively as [Word2vec](https://en.wikipedia.org/wiki/Word2vec)) are readily 
available. We can use these through the [gensim](https://radimrehurek.com/gensim/) Python library.

## The big idea of our algorithm

What are we actually going to be doing? Let's outline it:

1. Get a word from the user
   1. Validate that it is in EtymDB
   2. Validate that it is in English
2. Find the root word for the user's word
3. Find all leaf words for the root word
   1. Make sure each leaf word is in English
   2. Make sure each leaf word is not the user's word
4. For each leaf word calculate the similarity to the user's word
5. Select the word with the highest similarity

## Conclusion

I've talked about an idea I've recently come across, and how (I think) I can automate it. The problem has been 
defined reasonably accurately. We've created the concept of a curiously related word and defined it covering each 
property in depth. We've also highlighted the technology we'll need to implement the solution. 
