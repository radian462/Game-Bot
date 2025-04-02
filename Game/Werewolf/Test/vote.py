import Modules.global_value as g
from Game.Werewolf.manager import Game, NightManager

g.werewolf_games = {}

g.werewolf_games[0] = Game()


def test_decide_kill_target():
    results = [11111, 22222, 56564, 11111, 22222, 11111, 22222, 64645]
    target = NightManager(id=0)._decide_kill_target(results)
    assert target == 11111 or target == 22222
