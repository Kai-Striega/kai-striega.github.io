+++
title = 'Curiously Related Words in Neo4j'
date = 2024-12-08T08:08:07+11:00
+++

## What we have

In the previous [post](https://kaistriega.com/blog/curiously-related-words/curiously-related-words-preprocessing-our-data/)
I showed how to parse EtymDB and convert it into a format usable by the ``admin-import`` tool. We should now have five 
csv files:

* ``vertex/full.csv``
* ``vertex/small.csv``
* ``vertex/with_embedding.csv``
* ``vertex/with_meaning.csv``
* ``relationships.csv``

## Getting Neo4j

### Neo4j in the cloud

Neo4j provides a cloud service with a free tier. Unfortunately, the free tier is capped at 200k nodes and 400k 
relationships. We've 1.8M nodes and 640k relationships. Unfortunately the free tier is not going to cut it.

### Neo4j in Docker

Neo4j provides a database in docker. Since this is running locally, we're able to use as many nodes and 
relationships as we want. I'm going to assume that you already know how to use Docker, if you don't you 
can check out Docker's [official documentation](https://www.docker.com/).

It is now possible to spin up Neo4j docker container with[^1]:

```shell
docker run \
  --publish=7474:7474 \
  --publish=7687:7687 \
  --volume=$HOME/neo4j/data:/data \
  neo4j
```

## Setting up Neo4j

### The finished product

I'm going to do this section back to front. Let's start with the full docker invocation. We'll then go through it 
step by step for the majority of this post. The full docker invocation is:

```shell
docker run --interactive --tty --rm \
  --publish=7474:7474 \
  --publish=7687:7687 \
  --volume=$HOME/neo4j/data:/data \
  --volume=$HOME/neo4j/import:/import \
  neo4j:5.25.1 \
  neo4j-admin database import full \
  --nodes=/import/vertex/full.csv \
  --nodes=/import/vertex/with_embedding.csv \
  --nodes=/import/vertex/with_meaning.csv \
  --nodes=/import/vertex/small.csv \
  --relationships=/import/relationships.csv \
  --multiline-fields=true \
  --array-delimiter="\t"
```

### Ports

```shell
--publish=7474:7474 \
--publish=7687:7687
```

Docker uses the ``--publish`` flag to expose ports to the world. This means that we are _forwarding_ two ports. What 
do these represent?

* ``7474`` allows Neo4j to communicate via HTTP, this allows you to use the web based interface
* ``7687`` allows Neo4j to communicate via the bolt protocol, this allows you to communicate algorithmically

### Bind Volumes

```shell
--volume=$HOME/neo4j/data:/data \
--volume=$HOME/neo4j/import:/import
```

``--volume`` allows the container to access files or directories from outside the Docker container. Here we're 
binding two directories, ``data`` and ``import``. But what do these actually do[^2]?

* ``data``: Allows Neo4j to persist data
* ``import``: Stores data that Neo4j may need to import

Of course to use these directories they have to be created. As I don't want these inside my local directories I have 
created ``~/neo4j/data`` and ``~/neo4j/import``. Now that these are created, we also need to move our five CSVs into 
the ``~/neo4j/import`` directory.

### Actually getting Neo4j

```shell
neo4j:5.25.1
```

This line tells docker which image to run. There are two parts here the image name (``neo4j``) and the tag (``5.25.1``).

### Using the admin-import tool

```shell
neo4j-admin database import full \
--nodes=/import/vertex/full.csv \
--nodes=/import/vertex/with_embedding.csv \
--nodes=/import/vertex/with_meaning.csv \
--nodes=/import/vertex/small.csv \
--relationships=/import/relationships.csv \
--multiline-fields=true \
--array-delimiter="\t"
```

The rest of the instruction is calling the admin-import tool. There are a couple of things here:

* ``--nodes`` tells Neo4j that the following file (that we uploaded to the ``import`` directory) contains node data 
* ``--relationships`` tells Neo4j that the following file contains relationship data
* ``--multiline-fields=true`` tells Neo4j that our fields spread across multiple lines. We need this as our 
  embeddings (which are stored as arrays) can become very long
* ``--array-delimiter="\t"`` overwrites the delimiter used for arrays to ``\t``. This is what we used for the embeddings

## Running the admin-import tool

Let's execute the invocation we defined above. If everything worked it should end with the following:

```shell
IMPORT DONE in 7s 26ms. 
Imported:
  1885104 nodes
  643985 relationships
  8977985 properties
Peak memory usage: 565.2MiB
```

That means it worked! We now have data in Neo4j

## Seeing the data in Neo4j

### Logging into Neo4j
Let's launch Neo4j in docker. We don't need the full invocation this time as we have already imported the data.

```shell
docker run \
  --publish=7474:7474 \
  --publish=7687:7687 \
  --volume=$HOME/neo4j/data:/data \
  neo4j
```

You can now access Neo4j via ``http://localhost:7474/``. Note that if it's your first time you will need to log in. The 
username is ``neo4j`` and the password is ``neo4j``, you will then be prompted for a new password. You should now be 
greeted by a welcome screen that looks as follows:

![Neo4j welcome screen](/images/neo4j.png)

## Conclusion

We've managed to import our data into Neo4j and to access the Neo4j web interface by using a Docker container. I'd 
suggest you play around with the data a bit and see how you go. Maybe you can come up with another solution, or find 
some other interesting relationship between words.

[^1]: We'll cover what this actually does in much more depth later
[^2]: For a full list of mount points see [Neo4j mount points and permissions](https://neo4j.com/docs/operations-manual/current/docker/mounting-volumes/#docker-volumes-mount-points)
