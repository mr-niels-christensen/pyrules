pyrules
=======
pyrules is a pure-Python library for implementing discrete rule-based models.

My simplest example of a discrete rule-based model is this:
```python
        ( #Rule 0: If X is nice, then ('bacon', X) is good.
         r.rule('good', ('bacon', 'X'))
         .premise('nice', 'X')
        )
        ( #Rule 1: If X is good, then ('eggs', X) is nice.
         r.rule('nice', ('eggs', 'X'))
         .premise('good', 'X')
        )
        r.rule('nice', 'beans') #Rule 2: 'beans' are nice.
        r.rule('good', 'toast') #Rule 3: 'toast' is good.
```

This rulebook generates wonderful facts like

```
('nice', ('eggs', 'toast'))
('good', ('bacon', ('eggs', 'toast')))
('nice', ('eggs', ('bacon', ('eggs', 'toast'))))
```

The full source of this example is here: https://github.com/mr-niels-christensen/pyrules/blob/master/src/test/test_bacon_and_eggs.py

If you know Prolog, pyrules may now look like a Prolog interpreter. 
It's not, but it can do a few Prolog-like things.
For example, it can solve the Monkey & Banana puzzle from Ivan Bratko's book "Prolog
programming for artificial intelligence".
See https://github.com/mr-niels-christensen/pyrules/blob/master/src/test/test_monkey_banana.py

If you're into mathematical logic, pyrules can help you work with axioms systems in Python.
As an example, the following test generates theorems for the Russell-Bernays axiom system
for propositional logic: https://github.com/mr-niels-christensen/pyrules/blob/master/src/test/test_propositional_logic.py
