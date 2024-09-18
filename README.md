# What is this:
This is an attempt at building an asyncio compatible event loop that is multithreaded. I.e. you will finally be able to use asyncio and actually have it be multithreaded !
I've written a [blog post](https://www.neilbotelho.com/blog/multithreaded-async.html) explaining more about the why and how of this project.


# Requirements:
The only thing you'll need is the free threaded Python 3.13 release. I recommend using pyenv to get it.

```bash
pyenv install 3.13t-dev
```

# How to try it out:
I have a couple of scripts in the tests folder that you can use to test out basic functionality as well as a basic fastapi server. 
Feel free to submit more interesting tests as PR's and open issues that you come across. I won't commit to fixing them, but it'll be useful to others looking at this.

- `tests/basic.py` : contains a simple async function, with sleeping and `asyncio.gather`
- `tests/get_request.py` : contains an example async GET request with `httpx`
- `tests/listen.py` : contains sample code for listening for incoming connections in an async manner
