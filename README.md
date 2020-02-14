# Network programmability stream supporting files
Supporting files for my network programmability stream, mostly code written live on [Twitch stream](https://twitch.tv/dmfigol).
Stream recordings can be found on my [YouTube](https://youtube.com/dmfigol)

The repository contains a bunch of folders corresponding to a specific tool or technology. In each folder there is a README.md which contains some details about that particular project, how to run it, what different files are for. It could also contain technology notes.

For majority of projects I am using Python 3.6 or 3.7 (by the way, the easiest way to install any Python version is [pyenv](https://github.com/pyenv/pyenv)).  
I am also a heavy user of [poetry](https://python-poetry.org) - tool for managing python dependencies. It uses `pyproject.toml` and `poetry.lock` files which you can find throughout the repo. You can install dependencies with `poetry install`. I will also do my best to provide `requirements.txt` as well so you can do `pip install -r requirements.txt` in case you don't want to deal with poetry, but don't be surprised if you don't find one.

Note: Currently the repo files undergo a **major** overhaul.
### Reworked folders
* model-driven-telemetry - contains technology notes and supporting files for gRPC dial-out telemetry and NETCONF dial-in telemetry