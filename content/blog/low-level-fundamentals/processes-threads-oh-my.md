+++
title = 'Processes, Threads, Oh My!'
date = 2024-10-27T13:51:52+11:00
+++

## TLDR

* Processes and threads are an integral part of programming
* They are an essential tool in any developer's toolbox
* Processes is how the OS represents a running program.
* Threads are how the computer groups together instructions from your program and executes them
* You can have multiple processes and threads
* At least one thread runs _inside_ each process
* Tradeoffs of processes vs threads are:
  * Processes are slower to create than threads
  * Processes own their memory, threads share memory between them
  * It is easy to make very difficult to debug errors with threads

## Introduction

I have a friend who is currently trying to transition into software engineering. She is currently completing her masters
in IT. While nerding out together about tech, I mentioned multiprocessing. She said she'd never heard of it. That's not
great, so I tried to explain it, but feel that I didn't do a great job of it. This blog post will be my attempt to
clarify some of the essential concepts that a developer should know about processes and threads, focusing on how they 
work in Linux. I'll do this in a couple of parts:

1. TLDR
2. Introduction
3. Why: Why care at all?
4. Processes: Cover what processes are, and try to explain how they work
5. Threads: Same as processes, but with threads
6. Processes vs Threads: Pros/cons of each and when you would use one vs the other

## Why care about processes and threads?

As a programmer, you're continually building up your technical toolbox. This toolbox is the sum total of all the tools
that you have available to solve any given problem. You know about ``if/then/else`` conditionals or how to split your
code into logical groupings (classes or functions) to make your code more understandable. Processes and threads provide
another, extremely powerful tool to add to your toolbox. 

Processes and threads open your world to two different ideas:

1. You can do things at the same time (parallelism)
2. You can make things look like they are happening at the same time (concurrency)

More than that, processes and threads are fundamental knowledge of how an operating system runs your program.

And if even that doesn't motivate you: Process vs Thread is a very common interview question!

##  Processes

### Defining Processes

You have just written your program, now it's time to run it. Ok. Let's launch it! That's easy, you know how to do that.
But what happened? How did your OS go from "here is a binary/script" to "let's run it"?
It created a process. A process is how the OS represents a running program. A couple of things are usually created when
a process is created. These are:

1. An image of the executable machine code associated with a program.
2. Memory which typically holds the executable code, process specific data, a call stack (to keep track of active subroutines and/or other events) and some heap memory.
3. File descriptors of operating system resources
4. Security attributes (e.g. who owns the process and permissions)
5. Processor state (what's the CPU currently doing?)

### Seeing info about processes

We can see a snapshot of the processes currently running using the [ps](https://man7.org/linux/man-pages/man1/ps.1.html)
command. Let's give that a try:
 
```shell
$ ps u
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
kai         4507  0.0  0.0 235708  5568 tty2     Ssl+ 12:58   0:00 /usr/libexec/gdm-wayland-session env GNOME_SHELL_SESSION_MODE=ubuntu /usr/bin/gnome-session --session=ubuntu
kai         4519  0.0  0.0 298212 16320 tty2     Sl+  12:58   0:00 /usr/libexec/gnome-session-binary --session=ubuntu
kai        25122  0.0  0.0  11932  5760 pts/0    Ss+  13:50   0:00 /bin/bash --rcfile /home/kai/.local/share/JetBrains/Toolbox/apps/pycharm-professional/plugins/terminal/shell-integrations/bash/bash-integration.bash -i
kai        25655  0.0  0.0  11532  5184 pts/2    Ss   13:54   0:00 bash
kai        28495  0.0  0.0  11532  5376 pts/3    Ss   14:27   0:00 bash
kai        29599  0.0  0.0  14016  4416 pts/2    R+   14:33   0:00 ps u
```

Now this gives us a lot of things:

* USER: Who owns the process?
* PID: What is the process ID?
* %CPU: How much CPU is the process using, as a percentage of total available?
* %MEM: How much memory is the process using, as a percentage of total available?
* VSZ: virtual memory size of the process in KiB
* RSS: resident set size, the non-swapped physical memory that a task has used
* TTY: which terminal controls the process?
* STAT: multi-character process state. What state is the process currently in?
* START: When did the process start?
* TIME: How much CPU time has the process used?
* COMMAND: What command was used to launch the process?

### Creating our own process

Let's assume we have a very simple Python program, called ``main.py``:

```python
if __name__ == "__main__":
    name = input("Enter your name: ")
```

Now let's launch it from the terminal (note: just let it run. Don't close it, or actually enter the data):

```shell
python main.py
```

What happens to our list of processes? Let's print out all the lines that contain the word "python" (this is what ``grep python`` does...)

```shell
$ ps u | grep python
kai        30492  0.0  0.0  19180  9408 pts/3    S+   14:48   0:00 python main.py
kai        30494  0.0  0.0   9148  2112 pts/2    S+   14:48   0:00 grep --color=auto python
```

We have created two processes. The first is the process we created by calling Python. The second is our call to grep. We can ignore this one.

### Creating multiple processes

That's great. But we mentioned the power of processing is parallelism. What happens if we launch our program multiple times, in different terminals?

```shell
$ ps u | grep python
kai        30837  0.0  0.0  19180  9408 pts/4    S+   14:54   0:00 python main.py
kai        30838  0.0  0.0  19180  9408 pts/3    S+   14:54   0:00 python main.py
```

Hooray! We now have two Python processes. But launching a distinct terminal for each process you want to launch isn't very convenient.
Luckily for us Python has the [multiprocessing](https://docs.python.org/3/library/multiprocessing.html) module. This
module can launch processes for us. Let's expand our simple program from before to utilise multiple processes:

```python
from multiprocessing import Pool
from time import sleep


def say_hello(name):
    """Say hello and sleep for 10 seconds"""
    print(f"Hi {name}!")
    sleep(10)


def main():
    with Pool(3) as p: # Create a pool of 3 processes
        # map the `say_hello` function across the provided names
        p.map(say_hello, ["Kai", "Tessa", "Jess"])


if __name__ == "__main__":
    main() # Actually do the stuff
```

A quick quiz: how long does the program sleep? We're telling the computer to sleep for 10 seconds three times. In non-parallel code (usually called _serial_ code), this
should sleep for 30 seconds. How long does our program sleep for? Try it out. You might be surprised.

Now what processes are created? Let's take a look:

```shell
$ ps u | grep python
kai        35499  0.8  0.0 245100 14976 pts/3    Sl+  15:21   0:00 python main_processes.py
kai        35500  0.0  0.0  23856 10436 pts/3    S+   15:21   0:00 python main_processes.py
kai        35501  0.0  0.0  23856 10628 pts/3    S+   15:21   0:00 python main_processes.py
kai        35502  0.0  0.0  23856 10632 pts/3    S+   15:21   0:00 python main_processes.py
```

We now have _four_ python processes:

* the three processes that handle each of our inputs
* the initial ("parent") process that launched ("spawned") the child processes

We can see several differences. The most prominent one being the `l` in the stat output. `l` means that the process is
multithreaded (we'll get to what that means in a bit) and we've allocated less memory for the child processes than the
parent process.

### Summary of Processes (checkin)

We've covered a lot so far. Let's take a second to revise what I've covered so far. We have:

* defined processes as the operating system's representation of a running program
* seen that we can show processes using the ``ps`` command
* explained the output of (some) of the ``ps`` command's outputs
* shown how to launch multiple processes, both through the terminal and via Python
* shown that using multiple processes can introduce parallelism, allowing us to run many functions at the same time

## Threads

We've talked a lot about _processes_, but this blog post has a second topic: _threads_. Let's talk about threads for a 
bit.

### Defining a Thread

When you first learnt programming you were taught that your computer reads you code from top to bottom and executes each
line as it chugs along. This is a _thread_ of execution. What's cool is that we can have multiple threads of execution.
Each process starts with one thread, the main thread. The main thread can create other threads to do multiple things,
seemingly at once. This is called concurrency.

### Seeing threads in action

Remember our multiprocessing script? We can modify it to use threads instead.

```python
from multiprocessing.pool import ThreadPool
from time import sleep


def say_hello(name):
    """Say hello and sleep for 10 seconds"""
    print(f"Hi {name}!")
    sleep(10)


def main():
    with ThreadPool(3) as p:
        p.map(say_hello, ["Kai", "Tessa", "Jess"])


if __name__ == "__main__":
    main()
```

Now let's print out the processes again:

```shell
$ ps u | grep python
kai        38342  0.7  0.0 466396 15168 pts/3    Sl+  15:58   0:00 python main_threading.py
```

What do we notice here?

* Only one process appears
* The `l` flag is back
* The processes' ``VSZ`` is much higher (466396 vs 245100)

Well, that kind of makes sense, it is possible for ``ps`` to show threads. We need to pass  the ``-T`` flag. Let's run
the command again:

```shell
$ ps u -T | grep python
kai        39009   39009  1.0  0.0 466396 14976 pts/3    Sl+  16:04   0:00 python main_threading.py
kai        39009   39010  0.0  0.0 466396 14976 pts/3    Sl+  16:04   0:00 python main_threading.py
kai        39009   39011  0.0  0.0 466396 14976 pts/3    Sl+  16:04   0:00 python main_threading.py
kai        39009   39012  0.0  0.0 466396 14976 pts/3    Sl+  16:04   0:00 python main_threading.py
kai        39009   39013  0.0  0.0 466396 14976 pts/3    Sl+  16:04   0:00 python main_threading.py
kai        39009   39014  0.0  0.0 466396 14976 pts/3    Sl+  16:04   0:00 python main_threading.py
kai        39009   39015  0.0  0.0 466396 14976 pts/3    Sl+  16:04   0:00 python main_threading.py
```

### Threads run _inside_ processes

The ``PID`` (the leftmost numeric column) hasn't changed. We have an extra column. This column, ``SPID`` is the ID of
the thread. **This means is that we have multiple threads running within the same process**. That's significant. As the
threads run in the same process, they do not own the resources of the process. The resources are shared between threads.


## Processes vs Threads

I've defined a processes as a running program and a thread as a thread of execution. And we've talked a bit about
resource ownership. Let's look at how processes and threads differ.

### Speed

A process needs to manage its own memory, the process of spawning (or creating) a process is much slower than spawning
a thread. Let us test this with the below Python snippet. Here we have set up a couple of things:

1. A decorator ``timed``, to keep track of how long the function takes
2. A function ``dummy_work``, this is the simplest function I could think of. We're doing the least amount of work to isolate the time taken by the process/thread itself
3. A function ``run_thread``, that creates, runs and joins a thread.
4. A function ``run_process``, that creates, runs and joins a process.

```python
from threading import Thread
from multiprocessing import Process
from functools import wraps
from time import time_ns


def timed(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_ns = time_ns()
        result = f(*args, **kwargs)
        end_ns = time_ns()
        total_time_s = (end_ns - start_ns) / (10 ** 9)
        print(f.__name__, total_time_s)
        return result

    return wrapper


def dummy_work():
    """ A function that does as little work as possible"""
    return None


@timed
def run_thread():
    t = Thread(target=dummy_work)
    t.start()
    t.join()


@timed
def run_process():
    p = Process(target=dummy_work)
    p.start()
    p.join()


def main():
    run_thread()
    run_process()


if __name__ == "__main__":
    main()

```

Running this script gives the following output:

```shell
$ python process_vs_thread.py
run_thread 0.000241258
run_process 0.003551371
```

The thread is ~15x faster than the process. That's significant.

### Memory usage

Making copies of memory requires more memory (duh). But by how much? Let's set up a simple experiment and measure it.

```python
import time
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool

def dummy_work(xs):
    time.sleep(10)  # Give me some time to measure
    return [x + 1 for x in xs]


def main():
    thing_to_test = "Thread"
    xs = [x for x in range(1_000_000)]

    if thing_to_test == "Thread":
        with ThreadPool(3) as pool:
            pool.map(dummy_work, [xs, xs, xs])
    if thing_to_test == "Process":
        with Pool(3) as pool:
            pool.map(dummy_work, [xs, xs, xs])



if __name__ == "__main__":
    main()
```

Running this script with ``thing_to_test = "Thread"`` gives the following output:

```shell
$ ps u -T  | grep "python"
kai        63646   63646  1.7  0.0 285176 59336 pts/3    Sl+  17:43   0:00 python process_vs_thread_memory.py
kai        63646   63650  0.0  0.0 285176 59336 pts/3    Sl+  17:43   0:00 python process_vs_thread_memory.py
kai        63646   63651  1.3  0.0 285176 59336 pts/3    Sl+  17:43   0:00 python process_vs_thread_memory.py
kai        63646   63652  0.0  0.0 285176 59336 pts/3    Sl+  17:43   0:00 python process_vs_thread_memory.py
```

That is we have created one process with 4 threads (the main thread and our three worked threads) which use a total of 
59336 KB, what about running it with ``thing_to_test = "Process"``

```shell
$ ps u   | grep "python"
kai        63669  4.2  0.0 285176 59196 pts/3    Sl+  17:43   0:00 python process_vs_thread_memory.py
kai        63670  1.0  0.1 103820 89132 pts/3    S+   17:43   0:00 python process_vs_thread_memory.py
kai        63671  1.0  0.1 103820 88856 pts/3    S+   17:43   0:00 python process_vs_thread_memory.py
kai        63672  0.5  0.1 103820 89104 pts/3    S+   17:43   0:00 python process_vs_thread_memory.py
```

This creates 4 processes which require 326288 KB of memory. That's 5x as much. This is
due to each process making a copy of the large list we created AND all the information that is required of a process.

### Bugs

While processes "own" their memory, threads share memory between them. This leads to many new classes of bugs which are
usually _very_ hard to debug. Some examples of bugs that occur with multiple threads are:

* Race Conditions
* Deadlocks
* Livelocks
* Thread Starvation
* Priority Starvation
* Memory Consistency Errors
* Atomicity Violations
* Order Violations

Multi-threading bugs are often [Heisenbugs](https://en.wikipedia.org/wiki/Heisenbug). The bug can occur all the time,
rarely or only sometimes. They are very hard to detect, as they may pass tests but can lead to serious consequences.

## Conclusion

I hope that this post has helped you to realise that processes and threads exist, and a quick introduction to them. You
won't be an expert at this point. I'd suggest you read up a bit more when you have time.
