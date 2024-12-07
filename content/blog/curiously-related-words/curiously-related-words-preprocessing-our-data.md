+++
title = 'Curiously Related Words Preprocessing Our Data'
date = 2024-12-07T15:32:41+11:00
+++

[Previously](https://kaistriega.com/blog/curiously-related-words/what-is-a-curiously-related-word/) I've made up the
concept of a curiously connected word and a high level plan for finding such words. This post outlines the 
interesting parts of how I parse EtymDB. For those who are interested in all the code, it is available on my
[GitHub](https://github.com/Kai-Striega/curiously-connected-words/tree/main/src/neo4j_helper).

## The data we have, and why that's not enough

As outlined previously we have two sources of data:
1. [EtymDB](https://paperswithcode.com/dataset/etymdb-2-0) a database of words and their etymological relationships
2. [gensim](https://radimrehurek.com/gensim/) a library of [Word2vec](https://en.wikipedia.org/wiki/Word2vec) 
   models that model the semantic relationship between words

Our goal is to combine these two datasets into something nerdy. But just __having__ data isn't enough. We need to be 
able to retrieve, analyse and work with our datasets efficiently. Furthermore, our data isn't really tabular. What 
we have are words, with some associated properties, and relationships between them. When you hear "relationships" 
you may be tempted to think of a relational database. While these are often the right choice, our data is a 
[graph](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics)) which can be difficult to work with in relational 
databases [^1]. [Neo4j](https://neo4j.com/https://neo4j.com/) provides a database that is specialised on graphs. 
This seems like the right tool for the job. Plus I want to try a new tool[^2].


## The Plan

EtymDB provides it's data as several ``csv`` files. This isn't ideal, and we want to get it into Neo4j. The 
[admin-import tool](https://neo4j.com/docs/operations-manual/current/tutorial/neo4j-admin-import/) allows us to 
import the data we want, however it needs to be in their own, very particular, format. We will need to write a 
conversion script and combine it with the gensim embeddings. EtymDB stores the vertices and edges separately these files
are:

* [etymdb_values.csv](https://github.com/clefourrier/EtymDB/blob/master/data/split_etymdb/etymdb_values.csv) for the 
  vertices (or nodes, if you're not a mathematician)
* [etymdb_links_info.csv](https://github.com/clefourrier/EtymDB/blob/master/data/split_etymdb/etymdb_links_info.csv) 
  for the relationships between words

### Parsing Vertices

Each row in etymdb_values.csv represents a word, followed by properties for each word. These are:

1. The EtymDB ID
2. The language code
3. The field[^3]
4. The lexeme
5. The meaning of the word, in English

One or more of these fields may be missing. We'll need to think of a strategy to manage these. We'll also 
want to:

* convert the language code to a recognisable language
* add another property, the gensim embedding
* encode the data into the format required by the admin-import tool

### Parsing Edges

Parsing edges looks much simpler. Each row in etymdb_links_info.csv contains three items:

1. The relationship type
2. The parent's EtymDB ID
3. The child's EtymDB ID


## Implementation
*Note*: I'll be focusing on parsing the vertices here. This is the more interesting problem, and I don't see the 
benefit in doubling up on the classes - they are nearly identical.

### Modelling the data in Python

#### Representing our Vertex as a dataclass

To represent our data I'm going to construct a [dataclass](https://docs.python.org/3/library/dataclasses.html) that 
represents the fields we want.

```python
@dataclass(frozen=True)
class Vertex:
    etymdb_id: int
    language: str
    field: int
    lexeme: str
    meaning: Optional[str] = None
    embedding: Optional[np.ndarray] = None
```

#### Representing Word2Vec

... and a [protocol](https://docs.python.org/3/library/typing.html#typing.Protocol) that represents the different 
classes of Word2Vec models we may want to use. This protocol defines a single method ``get_vector`` that, for a given
word, returns the embedding of that word (as a NumPy array).

```python
class Word2VecModel(Protocol):

    def get_vector(self, word: str) -> np.ndarray:
        ...
```

#### And some utilities

Lastly we'll need a couple of utility functions.

##### ``_get_language``

I borrowed the language code to language conversion from EtymDB's [code_to_lang.py](https://github.com/clefourrier/EtymDB/blob/878e5a55627048c6ed414a7b23739fe2385bd723/analysis_notebooks/code_to_langs.py)
file. Unfortunately this file doesn't contain all the codes that are in EtymDB. When looking up the language, we're 
going to try and find the language, unless the code isn't present. In that case, let's call it "Unknown".

```python
def _get_language(language_code: str, code_to_lang: dict[str, str]) -> str:
    try:
        return code_to_lang[language_code]
    except KeyError:
        return "Unknown"
```

##### ``_get_embedding``

gensim, does not include all words in EtymDB. That's ok. We don't require embeddings for all words. But we don't 
want the script to error when a word is missing, so I've wrapped it in a ``try..except`` clause.

```python
def _get_embedding(word: str, model: Word2VecModel) -> Optional[np.ndarray]:
    try:
        return model.get_vector(word)
    except KeyError:
        return None
```

### Tying all the datastructures together

I wrote a function ``parse_vertices`` that takes an opened file, reads each line and tries to parse it. Rather than
return a big list, I've created a [generator](https://docs.python.org/3/glossary.html#term-generator-iterator), this way
we don't define a massive list in memory.

```python
def parse_vertices(fp: TextIO, code_to_lang: dict[str, str], model: Word2VecModel) -> Iterable[Vertex]:
    for row in fp:
        entries = [e for e in row.rstrip("\n").split("\t") if e != ""]

        match len(entries):
            case 5:
                idx, language_code, field, lexeme, meaning = entries
            case 4:
                idx, language_code, field, lexeme = entries
                meaning = None
            case _:
                continue

        language = _get_language(language_code, code_to_lang)
        embedding = _get_embedding(lexeme, model)

        yield Vertex(
            etymdb_id=int(idx),
            language=language,
            field=int(field),
            lexeme=lexeme,
            meaning=meaning,
            embedding=embedding,
        )
```

### Making our data Neo4j compatible

#### Defining our data model

The admin-import tool allows us to import CSV data to Neo4j. As we've already parsed EtymDB, we need to turn this 
data into a format that the admin-import tool can parse. The [csv header format](https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/#import-tool-header-format)
tells us what this format is. If you didn't here's the tldr:

* Files containing node data can have an ``ID`` field, a ``LABEL`` field, and properties.
* Properties are strings by default, but can be any of the [Property data types](https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/#import-tool-header-format-properties)
* Arrays are defined by appending `[]` to the type and delimited by a special value, ``--array-delimiter``

#### Example

The vertex class should therefore have a header of ``etymdb_id:ID,lexeme,field:int,language,embedding:double[],meaning,:LABEL``
where:

* ``etymdb_id`` is the vertex's ID 
* ``lexeme``,``language`` and ``meaning`` are strings 
* ``field`` is an integer
* ``meaning`` is an array of doubles.

I haven't touched on the ``:LABEL`` yet. This is the "type" of the vertex.

#### Implementation in Python

I chose to extend the ``Vertex`` class to include a ``to_neo4j_dict`` method. I'm doing something funny with the 
``meaning`` here. It turns out the admin-import tool doesn't understand what a NumPy arrays is. We need to format 
the embedding as a string of values seperated by ``--array-delimiter`` (in this case a ``\t``).

```python
def to_neo4j_dict(self) -> dict:
    fields = {
        "etymdb_id:ID": self.etymdb_id,
        "language": self.language,
        "field:int": self.field,
        "lexeme": self.lexeme,
    }

    if self.meaning is not None:
        fields["meaning"] = self.meaning

    if self.embedding is not None:
        fields["embedding:double[]"] = "\t".join(str(x) for x in self.embedding)

    return fields
```

## Actually parsing EtymDB

Now that we have our data model sorted, we can start actually parsing EtymDB. There is one complication, our data 
contains words with a different number of properties (some don't have embeddings or meanings or both) the admin-import
tool requires each row in the CSV file to have the same data, but can parse multiple CSVs with different number of rows.

To do this, I'm going to define a bunch of sets that contain the exact headers we're looking for and a suffix, which 
is the file we're going to store them in:

```python
CSV_HEADER_FILENAMES = {
    frozenset(["etymdb_id:ID", "language", "field:int", "lexeme", ":LABEL"]): "small",
    frozenset(["etymdb_id:ID", "language", "field:int", "lexeme", "meaning", ":LABEL"]): "with_meaning",
    frozenset(["etymdb_id:ID", "language", "field:int", "lexeme", "embedding:double[]", ":LABEL"]): "with_embedding",
    frozenset(["etymdb_id:ID", "language", "field:int", "lexeme", "meaning", "embedding:double[]", ":LABEL"]): "full",
}
```

From here, let's create a dictionary of each type of vertex entry:

```python
csv_vertex_groups = defaultdict(list)
with open(etymdb_vertices_path) as fp:
    for vertex in parse_vertices(fp, WIKI_CODE_TO_LANG, MODEL):
        row_values = vertex.to_neo4j_dict() | {":LABEL": "Lexeme"}
        row_key = frozenset(row_values.keys())
        csv_vertex_groups[row_key].append(row_values)
```

This stores all the vertices by its header. Having all the rows we can go through each value in the dictionary and 
write the values to a CSV:

```python
for header, file_suffix in CSV_HEADER_FILENAMES.items():
    filename = Path(outdir) / "neo4j_import_data"/ "vertex" / f"{file_suffix}.csv"

    with open(filename, "w+") as fp:
        csv_writer = csv.DictWriter(fp, header)
        csv_writer.writeheader()

        for row_values in csv_vertex_groups[header]:
            csv_writer.writerow(row_values)
```

## Conclusion

Hooray! This blog has shown you how to parse the data in EtymDB and store it in a format that can be parsed by Neo4j's
admin-import tool. Next up we'll look a bit more into Neo4j and how to actually load our data.


[^1]: It is possible, but querying graphs in relational databases becomes cumbersome very quickly
[^2]: This is a side project, I'm allowed to pick whichever tools I want!
[^3]: I have no idea what this represents. 