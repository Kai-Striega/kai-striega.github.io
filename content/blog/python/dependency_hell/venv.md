+++
title = 'Virtual Environments'
date = 2024-10-19T18:14:18+11:00
+++

Last night I helped a junior developer from [SheCodes](https://shecodes.com.au/) debug an issue. She
had moved her Python virtual environment within her project to where she thought it was "supposed to be". While 
helping her to correct all the pathing issues, I realised that her understanding of what a virtual environment is and 
why we need them wasn't fantastic. I took some time to explain, but wanted to give a more indepth explanation of how
a virtual environment actually works. 

In this post, I'll be talking about virtual environments within the Python ecosystem and how they work on Linux systems.
The big ideas behind it are similar for mac/Windows, however, there is some extra complication (especially on Windows) 
in the implementation. Note that I have installed Python using [pyenv](https://github.com/pyenv/pyenv), this will make
my output slightly different from if you had installed it differently

## The need for virtual environments

Python comes installed with many common operating systems including MacOS, Ubuntu, CentOS. This Python is often referred
to as the "system Python". As the system Python is managed by the OS, it is available to _any_ process that is run by 
the OS (which includes your program). 

That's great! Right? Well not really. Because your OS relies on the system Python, any changes to the system Python
could potentially break your OS. You really want to avoid that. The solution is to creat a _virtual environment_ (or 
venv, for short). A venv is a directory that contains its own version of Python and required dependencies. Now any
changes you make to your virtual environment are __only__ in that environment. This leads to a couple of other benefits:

1. You can manage each project independently
2. You avoid polluting the system Python with all the packages you install
3. You can manage your Python version and dependencies more easily
4. You can reproduce your environments more easily by using requirement files

By this point, I hope to have convinced you that venvs are important. And that, yes, you should be using one. What I
intend for the rest of this post is to explain __how__ venvs actually work. To do that we need to understand how your 
computer actually runs Python, which I'll talk about now.

## How your computer runs Python

When most budding Python developers start with learning python they are taught to invoke Python from the command line, 
which looks something like the following

```bash
python your_script.py
```

This tells the OS that you want to run a command (``python``) with an argument (``your_script.py``). But how does
your computer know what to do with ``python``? After all, it is only text! Your computer has to find the underlying
executable to run. In the simplest case a _fully qualified path_ to an executable is used. This tells your computer
exactly where to look for the executable. Using a fully qualified path can have disadvantages. You need to know the 
full path for every possible system under all possible circumstances. Often this isn't feasible. When your computer 
isn't provided a fully qualified path it will resort to looking at the ``PATH`` [environment variable](https://en.wikipedia.org/wiki/Environment_variable).
This is a colon seperated list of all the directories that your computer should search for when looking for executables.

You can check your ``PATH`` environment variable as follows:

```shell
$ echo $PATH
/home/kai/miniconda3/condabin:/home/kai/.pyenv/shims:/home/kai/.cargo/bin:/home/kai/.pyenv/bin:/home/kai/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/snap/bin:/home/kai/.local/share/JetBrains/Toolbox/scriptsexport:/.local/bin
```

From this list we can see that it will search for executables in the following order:

1. /home/kai/miniconda3/condabin
2. /home/kai/.pyenv/shims
3. /home/kai/.cargo/bin

...and so on.

## How paths relate to venvs

What does searching for executables have to do with venvs? Well lets construct a venv, activate it, and see how the path
changes. First, we use the ``venv`` module to construct a virtual environment in the ``.venv`` directory.

```shell
python -m venv .venv
```

We will now have a new ``.venv`` directory. Let's source it ``source .venv/bin/activate`` and see how the path changes.

```shell
$ echo $PATH
/home/kai/Projects/example/.venv/bin:/home/kai/miniconda3/condabin:/home/kai/.pyenv/shims:/home/kai/.cargo/bin:/home/kai/.pyenv/bin:/home/kai/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/snap/bin:/home/kai/.local/share/JetBrains/Toolbox/scriptsexport:/.local/bin
```

It probably doesn't stand out to you immediately, but ``PATH`` has changed. ``/home/kai/Projects/example/.venv/bin`` is
now at the beginning of ``PATH``. This means that our computer will search ``/home/kai/Projects/example/.venv/bin`` 
_before_ looking at other directories. 

This means that the OS will look into our new virtual environment before looking at other solutions. But why does this
matter? To answer this question let's take a look at what we have actually created in our virtual environment.

```shell
$ tree -L 2 .venv/
.venv/
├── bin
│   ├── activate
│   ├── activate.csh
│   ├── activate.fish
│   ├── Activate.ps1
│   ├── pip
│   ├── pip3
│   ├── pip3.12
│   ├── python -> /home/kai/.pyenv/versions/3.12.7/bin/python
│   ├── python3 -> python
│   └── python3.12 -> python
├── include
│   └── python3.12
├── lib
│   └── python3.12
├── lib64 -> lib
└── pyvenv.cfg
```

There are a couple of different directories here:

* ``bin`` which stores executable files (more on this later)
* ``include`` which stores information used for the CPython C-API (won't be getting into too much detail for this blog post)
* ``lib`` which stores the Python standard library and any packages you have installed
* ``lib64`` which is an alias for ``lib``
* ``pyvenv.cfg`` which stores metadata about the virtual environment

Our path changed to include the ``bin`` directory, let's begin by looking into that. There are three types of files here:

* ``activate`` which turns on the environment
* ``pip`` which installs packages
* ``python`` which is Python itself

Notice how some of the directories/files have an ``->`` after them pointing to another file? That's called an alias. 
There isn't really a file there. The name is simply a moniker for another file. For example using the ``python3.12``
command will redirect to the ``python`` command, which in turn redirects to
``/home/kai/.pyenv/versions/3.12.7/bin/python``. This is the path to the original Python we used to create our venv. 
Many, many people will say that creating a venv copies the original Python. **This is wrong** it creates an alias.

## Installing packages

Remember that one of the key features of venvs is to isolate your environment for each project. So what happens when a
new package is installed? Well, lets try it! I'm going to install the package [NumPy](https://numpy.org/)

```shell
pip install numpy
```

Let's explore how this changes our ``.venv`` directory

```shell
$ tree -L 4 .venv/
venv/
├── bin
│   ├── activate
│   ├── activate.csh
│   ├── activate.fish
│   ├── Activate.ps1
│   ├── f2py
│   ├── numpy-config
│   ├── pip
│   ├── pip3
│   ├── pip3.12
│   ├── python -> /home/kai/.pyenv/versions/3.12.7/bin/python
│   ├── python3 -> python
│   └── python3.12 -> python
├── include
│   └── python3.12
├── lib
│   └── python3.12
│       └── site-packages
│           ├── numpy
│           ├── numpy-2.1.2.dist-info
│           ├── numpy.libs
│           ├── pip
│           └── pip-24.2.dist-info
├── lib64 -> lib
└── pyvenv.cfg
```

There now exist several changes to our `.venv/` directory.

* `f2py` and `numpy-config` now exist inside `dir/`, these are tools installed by NumPy
* The directory `lib/python3.12/site-packages/` now includes several entries for NumPy

What's significant is that the venv stores our version of NumPy _independently of any other environment_ meaning
that this particular version of NumPy won't interfere with any other project's version.

## Moving venvs is a very bad idea...

How is this all relevant to my SheCodes friend? As we now know, a virtual environment isolates packages by changing
where they are stored. For you project to know where the venv is, the editor will have to be told where they are. She
did this beforehand. However once she moved her venv the path value store by her IDE was outdated - the IDE couldn't
find the environment anymore and errors started to occur. The solution turned out to be straightforward: reinstall the
virtual environment and tell the IDE where to find it (again).

## Conclusion

I've talked about what a virtual environment is, why you should use them, how they work, and why moving them can be a 
bad idea. This post isn't supposed to be super deep. There's a lot more depth that I could go into, but I think I've 
covered enough to be useful.