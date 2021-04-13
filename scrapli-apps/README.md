# scrapli scripts
This directory contains examples of using different libraries in scrapli family.

## Thoughts on scrapli libraries
### scrapli (core)
[Documentation](https://carlmontanari.github.io/scrapli)  
[Source Code](https://github.com/carlmontanari/scrapli)  
[Examples](https://github.com/carlmontanari/scrapli/tree/master/examples)  

`scrapli` (core) is a library for SSH and Telnet connections to network devices. It is an abstraction on top of low-level SSH transport libraries, like paramiko, ssh2-python and others and in its function is similar to [netmiko](https://github.com/ktbyers/netmiko). The library implements for you an interface to send and receive commands instead of writing to and reading bytes from the channel, so you don't have to worry about finding the prompt or privilege levels transitions. I have been using `scrapli` in production since its release and I strongly recommend it. Some of the reasons why I am using it instead of `netmiko`:
* asyncio support (sync/async have the same interface)
* reliable prompt matching without a need to tune timers
* nice API with response objects (similar to requests), rather than receiving strings directly
* great docs
* well tested
* type hints which allow IDEs to do better autocompletion magic
* easy to add support for another platform

The only complaint I have seen towards `scrapli` was that it "supports" a low number of network operating systems and e.g. `netmiko` supports more. And I personally think it is not a bad thing. There are so many different network operating systems and once an author adds support for them to the core of the library, they are ultimate responsible for maintaining it and it is miserable experience - github issues become populated with bugs related to platforms, instead bugs/feature requests for the core itself, they would be spending time stressing out how to get that platform image and how to test it. It is not sustainable.  
Instead `scrapli` offers several ways to deal with this scenario, check out these sections in the docs:
* [Supported Platforms](https://carlmontanari.github.io/scrapli/user_guide/project_details/#supported-platforms)
* [Using Driver](https://carlmontanari.github.io/scrapli/user_guide/advanced_usage/#using-driver-directly)
* [Using GenericDriver](https://carlmontanari.github.io/scrapli/user_guide/advanced_usage/#using-the-genericdriver)

There is also [scrapli_community](https://scrapli.github.io/scrapli_community/user_guide/project_details/) project, where community members add support for their platforms and there is a section in the docs describing how to [add a platform yourself](https://scrapli.github.io/scrapli_community/user_guide/basic_usage/)

### scrapli-netconf
[Documentation](https://scrapli.github.io/scrapli_netconf)  
[Source Code](https://github.com/scrapli/scrapli_netconf)  
[Examples](https://github.com/scrapli/scrapli_netconf/tree/master/examples)  

`scrapli-netconf` is a library which provides a way to interact with devices via NETCONF built on top of `scrapli`. It supports both NETCONF 1.0 and 1.1 and supports many transport methods like `scrapli`. Here are the reasons I am using it instead of `ncclient`:
* asyncio support (sync/async have the same interface)
* easy-to-use public API similar to `scrapli`
* has clean architecture making it much easier to troubleshoot than `ncclient` (the latter abuses signals and duck-typing excessively)
* great docs
* type hints which allow IDEs to do better autocompletion magic

### scrapli-cfg
[Documentation](https://scrapli.github.io/scrapli_cfg)  
[Source Code](https://github.com/scrapli/scrapli_cfg)  
[Examples](https://github.com/scrapli/scrapli_cfg/tree/master/examples)  

`scrapli-cfg` is a library which provides different config operations (e.g. config replace, diff, save/commit) similar to [`napalm`](https://github.com/napalm-automation/napalm). It is built on top of `scrapli` and supports several "core" platforms: Cisco IOS-XE/XR/NX-OS, Arista EOS, Juniper Junos. It is possible to add your own platform, but it might be more complex than adding a platform to `scrapli`. `scrapli-cfg` can also do config operations over telnet (think of console via terminal servers) and uses only SSH or Telnet for all operations (no extra dependencies like pyez, pyeapi, etc). It also has a partial config replacement to leave some config sections untouched. Here are the reasons I am using `scrapli-cfg` instead of `napalm`:
* asyncio support (sync/async have the same interface)
* config operations are possible via Telnet (console via terminal servers - this allows me to replace configs even on devices where I don't have management port connectivity, but I have a console connection)
* partial config replacement if I want to manage only some parts of the config, not all features at once
* no need in getters, it is already covered by `scrapli` textfsm/ttp/genie support

### scrapli-replay
[Documentation](https://scrapli.github.io/scrapli_replay)  
[Source Code](https://github.com/scrapli/scrapli_replay)  
[Examples](https://github.com/scrapli/scrapli_replay/tree/main/examples/simple_test_case)  

Have you ever tried testing your network automation application in CI/CD? The usual way to do it is using `monkeypatch` / `mock`, but it requires a decent amount of effort and looks ugly. This problem was first addressed for testing external HTTP APIs using [vcrpy](https://github.com/kevin1024/vcrpy). The idea is that on tests marked with a specific marker, whenever that test invokes HTTP request(s), the library would save "cassettes" - YAML files containing request/response chain. Then, for subsequent calls to your test, the library would look up the response for a specific request in a YAML file, instead of doing HTTP request. By saving those cassettes to the repo, anyone or anything, including CI/CD, could test your app easily without actually talking to an external service.  
Now imagine this, but for SSH. This is exactly what `scrapli-replay` is. It saves SSH interactions to YAML cassettes and replays them later on subsequent calls.  
Personally, I think it is a big help in the world of network automation applications, as this allows to simplify significantly the testing of network automation applications. It really has no competitor, so here is an [example](https://github.com/dmfigol/netwarden/blob/master/backend/tests/routers/test_devices.py) from my other project - [Network controller NetWarden](https://github.com/dmfigol/netwarden), where my network automation is powered by a web framework:
```python
@pytest.mark.asyncio
@pytest.mark.scrapli_replay
async def test_get_devices():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/devices")
        # /api/devices collect a show command from 10 network devices using scrapli
    assert response.status_code == 200
    assert len(response.json()) == len(INVENTORY)
```

### nornir-scrapli
[Documentation](https://scrapli.github.io/nornir_scrapli)  
[Source Code](https://github.com/scrapli/nornir_scrapli)  
[Examples](https://github.com/scrapli/nornir_scrapli/tree/master/examples)  

`nornir-scrapli` is a nornir plugin for `scrapli` family: `scrapli (core)`, `scrapli-netconf`, `scrapli-cfg` enabling you to use these libraries as `nornir` tasks. There are no examples of this plugin in the repo, however there are some in my [`nornir-apps` repo](https://github.com/dmfigol/nornir-apps)

## Repository
The scripts were tested on **Python 3.9.4**.  
In the repository you can find the following files:
* `constants.py` contains details like username, password and a list of devices to connect to
* `ssh-netmiko.py` collects commands and does a configuration change using netmiko with threads
* `ssh-scrapli.py` collects commands and does a configuration change using scrapli with threads
* `ssh-scrapli-asyncio.py` collects commands and does a configuration change using scrapli with asyncio (these 3 examples have equivalent functionality, so you can compare the code and efficiency)
* `input/nc-config.yaml` contains a configuration in YAML format which will be converted to NETCONF XML payload using `utils.dict_to_xml()` function
* `nc-ncclient.py` collects config with NETCONF get-config and does a configuration change with edit-config taking the input from `input/nc-config.yaml`. This is done with ncclient and threads.
* `nc-scrapli.py` collects config with NETCONF get-config and does a configuration change with edit-config taking the input from `input/nc-config.yaml`. This is done with scrapli-netconf and threads.
* `nc-scrapli-asyncio.py` collects config with NETCONF get-config and does a configuration change with edit-config taking the input from `input/nc-config.yaml`. This is done with scrapli-netconf and asyncio (these 3 examples have equivalent functionality, so you can compare the code and efficiency)
* `input/R1.txt` has a config which will be used to replace the running-config via `scrapli-cfg`. It has a marker for BGP section `{{ bgp }}`, indicating that it should replaced with bgp section from running config
* `scrapli-cfg.py` performs a configuration replacement. BGP section is matched in the running config with regexp and placed inside of the `input/R1.txt` {{ bgp }} block. The resulting configuration is then diff'ed with original and applied.
* `scrapli_replay_sessions` contains YAML cassettes for testing with `scrapli-replay`
* `test-scrapli-replay.py` contains a test with fetches `show license udi` from the box and checks if serial number was correctly extracted. Note, this test should be run with `pytest test-scrapli-replay.py --scrapli-replay-block-network` (the switch indicates that `scrapli-replay` should not try connecting to the device and use only cassettes)
