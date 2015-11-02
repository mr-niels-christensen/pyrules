import unittest
from pyrules2 import when, rule, RuleBook
from itertools import islice
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

   I.e. starting from the door, our monkey can get its banana.
'''

State = namedtuple('State', ['monkey_pos', 'monkey_level', 'box_pos', 'has'])

INITIAL = State('atdoor', 'onfloor', 'atwindow', False)


class MonkeyBanana(RuleBook):
    @staticmethod
    def climb(state):
        # move(state(P, onfloor, P, H), climb, state(P, onbox, P, H)).
        if state.monkey_level == 'onfloor' and state.monkey_pos == state.box_pos:
            yield State(state.monkey_pos, 'onbox', state.monkey_pos, state.has)

    @staticmethod
    def grasp(state):
        # move(state( middle, onbox, middle, hasnot), grasp, state( middle, onbox, middle, has)).
        if state == State('middle', 'onbox', 'middle', False):
            yield State('middle', 'onbox', 'middle', True)

    @staticmethod
    def push(state):
        # move(state(Pl, onfloor, Pl, H), push(Pl, P2), state(P2, onfloor, P2, H)).
        if state.monkey_level == 'onfloor' and state.monkey_pos == state.box_pos:
            for new_pos in POSITIONS:
                if not new_pos == state.monkey_pos:
                    yield State(new_pos, 'onfloor', new_pos, state.has)

    @staticmethod
    def walk(state):
        # move(state(Pl, onfloor, B, H), walk(Pl, P2), state(P2, onfloor, B, H)).
        if state.monkey_level == 'onfloor':
            for new_pos in POSITIONS:
                if not new_pos == state.monkey_pos:
                    yield State(new_pos, 'onfloor', state.box_pos, state.has)

    @rule
    def can_go(self, state):
        # canget(Statel) :- move(Statel, Move, State2), canget(State2).
        moves = when(move=MonkeyBanana.walk) | when(move=MonkeyBanana.climb)\
                | when(move=MonkeyBanana.push) | when(move=MonkeyBanana.grasp)
        return when(state=INITIAL) \
            | moves(self.can_go(state))


class Test(unittest.TestCase):
    def test_cls(self):
        print MonkeyBanana

    def test_can_go(self):
        for s in islice(MonkeyBanana().can_go(None).all_dicts(), 100):
            if s['state'].has:
                return  # Success!
        self.fail('No state with a happy monkey')


if __name__ == "__main__":
    unittest.main()
