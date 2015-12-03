pyrules
=======
pyrules is a pure-Python library for implementing discrete rule-based models.

Here's an example of a discrete rule-based model.
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

This rulebook generates wonderful facts like

```
for scenario in d.viable():
    # There will be 16 of these
    rt = scenario['rt']
    print rt.milk(max) # Will be 28 or 30
    print rt.distance() # Will be around 380km, in meters
    print rt.duration() # Will be around 5 hours, in seconds
```

The full source of this example is here: https://github.com/mr-niels-christensen/pyrules/blob/master/src/test/test_roundtrips.py

If you know Prolog, pyrules may now look like a Prolog interpreter. 
It's not, but it can do a few Prolog-like things.
For example, it can solve the Monkey & Banana puzzle from Ivan Bratko's book "Prolog
programming for artificial intelligence".
See https://github.com/mr-niels-christensen/pyrules/blob/master/src/test/test_monkey_banana.py
