pyrules: The Planning Starter Kit
=======
pyrules is a starter kit for planning problems like planning itineraries, making schedules or playing board games.

Example:
A dairy (based in Erslev) needs to collect milk from four farms each day.
Each farm produces a different amount of milk per day.
The milk truck will go back to Erslev once during its daily roundtrip.
```python
BASE = place('Erslev, Denmark', milk=RESET)
LARS = place('Snedsted, Denmark', milk=18)
TINA = place('Bedsted Thy, Denmark', milk=20)
LISA = place('Redsted, Denmark', milk=10)
KARL = place('Rakkeby, Denmark', milk=6)
ROUNDTRIP = driving_roundtrip(BASE, LARS, TINA, BASE, LISA, KARL)
```

Until today, the schedule has been as indicated in ```ROUNDTRIP```.
But alas, one of the truck's tanks was broken, and now it cannot
transport more than 30 units of milk:
```python
class Dairy(RuleBook):
    @rule
    def roundtrip(self, rt=anything):
        return when(rt=ROUNDTRIP) | reroute(self.roundtrip(rt))

    @rule
    def viable(self, rt=anything):
        return limit(milk=30)(self.roundtrip(rt))
```

The original ```ROUNDTRIP``` requires a capacity of at least 38 units, so alternative routes must be explored.
Luckily, pyrules can provide these:
```python
d = Dairy()
for scenario in d.viable():
    # There will be 16 of these
    rt = scenario['rt']
    print rt.milk(max) # Will be 28 or 30
    print rt.distance() # Will be around 380km, in meters
    print rt.duration() # Will be around 5 hours, in seconds
```

The full source of this example is here: https://github.com/mr-niels-christensen/pyrules/blob/master/src/test/test_roundtrips.py

## Architecture

![Architecture diagram](docs/psk-diagram.jpg?raw=true)

You can use pyrules just like any other Python library, but pyrules also intends to support high-powered cloud deployments as per the diagram above. The basic idea is to allow parallel worker processes to crunch a problem in coordination using a task queue and an eventually consistent database like MongoDB or similar.
On top of this, a REST API allows control of planning tasks
if you prefer JavaScript to Python.

This architecture is work in progress. The current version of pyrules only supports a single, memory-backed worker.

## Inspired by Prolog


If you know Prolog, pyrules may now look like a Prolog interpreter. 
It's not, but it can do a few Prolog-like things.
For example, it can solve the Monkey-Banana puzzle from Ivan Bratko's book "Prolog
programming for artificial intelligence".
See https://github.com/mr-niels-christensen/pyrules/blob/master/src/test/test_monkey_banana.py
