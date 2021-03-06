import unittest
from pyrules2 import when, rule, RuleBook, anything
from collections import namedtuple

'''This pyrules example goes out to the Prolog enthusiasts.
   It is an implementation of Ivan Bratko's monkey&banana example:
   http://books.google.co.uk/books?id=-15su78YRj8C&pg=PA46&lpg=PA46&dq=monkey+banana+bratko&source=bl&ots=TA22Ve7wHK&sig=a1x6v2nvu7C78wjAs2lGMOKXUt4&hl=en&sa=X&ei=buKdUqioJeWX7QaLloCoAg&ved=0CC8Q6AEwAA#v=onepage&q=monkey%20banana%20bratko&f=false

   Our protagonist monkey is in a room with a door and a window. In the middle of the room,
   a banana is hanging from a rope in the ceiling. The monkey wants the banana, but it can't reach that high.
'''
POSITIONS = ['middle', 'atdoor', 'atwindow']
'''
   Luckily, there's a box at the window that the monkey can push around and climb.
'''
LEVELS = ['onfloor', 'onbox']
'''
   The monkey does not have the banana, but if it climbs the box in the middle of the room
   and grasps the banana, then it will have its banana.
'''
HAS_HASNOT = ['has', 'hasnot']
'''
   Bratko's model of this puzzle takes the form
       (state, move, state2)
   where each state is on the form
       ('state',  monkey_pos, monkey_level, box_pos, has_hasnot)
   and a move is 'grasp', 'climb', ('walk', pos1, pos2) or ('push', pos1, pos2).
'''

State = namedtuple('State', ['monkey_pos', 'monkey_level', 'box_pos', 'has'])

'''These are Bratko's Prolog rules:
move(state(P, onfloor, P, H), climb, state(P, onbox, P, H)).
move(state( middle, onbox, middle, hasnot), grasp, state( middle, onbox, middle, has)).
move(state(Pl, onfloor, Pl, H), push(Pl, P2), state(P2, onfloor, P2, H)).
move(state(Pl, onfloor, B, H), walk(Pl, P2), state(P2, onfloor, B, H)).
canget(Statel) :- move(Statel, Move, State2), canget(State2).

   Below is a pyrules implementation.
'''


class MonkeyBanana(State):
    @staticmethod
    def initial():
        return MonkeyBanana('atdoor', 'onfloor', 'atwindow', False)

    def climb(self):
        if self.monkey_level == 'onfloor' and self.monkey_pos == self.box_pos:
            yield MonkeyBanana(self.monkey_pos, 'onbox', self.monkey_pos, self.has)

    def grasp(self):
        if self == MonkeyBanana('middle', 'onbox', 'middle', False):
            yield MonkeyBanana('middle', 'onbox', 'middle', True)

    def push(self):
        if self.monkey_level == 'onfloor' and self.monkey_pos == self.box_pos:
            for new_pos in POSITIONS:
                if not new_pos == self.monkey_pos:
                    yield MonkeyBanana(new_pos, 'onfloor', new_pos, self.has)

    def walk(self):
        if self.monkey_level == 'onfloor':
            for new_pos in POSITIONS:
                if not new_pos == self.monkey_pos:
                    yield MonkeyBanana(new_pos, 'onfloor', self.box_pos, self.has)


class MonkeyBananaRules(RuleBook):
    @rule
    def can_go(self, state=anything):
        moves = when(move=MonkeyBanana.walk) | when(move=MonkeyBanana.climb) | \
            when(move=MonkeyBanana.push) | when(move=MonkeyBanana.grasp)
        return when(state=MonkeyBanana.initial()) | moves(self.can_go(state))


class Test(unittest.TestCase):
    def test_can_go(self):
        mb = MonkeyBananaRules()
        for s in mb.can_go():
            if s['state'].has:
                return  # Success!
        self.fail('No state with a happy monkey')


if __name__ == "__main__":
    unittest.main()
