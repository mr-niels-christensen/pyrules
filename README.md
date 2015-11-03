pyrules
=======
pyrules is a pure-Python library for implementing discrete rule-based models.

An example of a discrete rule-based model is this:
```python
class DanishRoyalFamily(RuleBook):
    @rule
    def children(self, parent, child):
        return \
            (when(parent=FRED) | when(parent=MARY)) \
            & \
            (when(child=CHRIS) | when(child=ISA) | when(child=VINCE) | when(child=JOSIE))

    @rule
    def spouse(self, x, y):
        return when(x=FRED, y=MARY) | when(x=JOE, y=MARIE) | self.spouse(y, x)

    @rule
    def sibling(self, x, y):
        return when(x=FRED, y=JOE) | self.sibling(y, x)

    @rule
    def aunt(self, aunt, niece, x=None, y=None):
        return (self.children(x, niece) &
                ((self.sibling(aunt, x) & when(y=None)) |
                (self.spouse(aunt, y) & self.sibling(y, x))))
```

This rulebook generates wonderful facts like

```
{'aunt': MARIE, 'niece': ISA}
{'aunt': JOE, 'niece': CHRIS}
```

With a bit more code, we could also distinguish boys from girls :)

The full source of this example is here: https://github.com/mr-niels-christensen/pyrules/blob/master/src/test/test_family.py

If you know Prolog, pyrules may now look like a Prolog interpreter. 
It's not, but it can do a few Prolog-like things.
For example, it can solve the Monkey & Banana puzzle from Ivan Bratko's book "Prolog
programming for artificial intelligence".
See https://github.com/mr-niels-christensen/pyrules/blob/master/src/test/test_monkey_banana.py
