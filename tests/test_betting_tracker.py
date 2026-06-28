import os
import sys
import unittest

os.environ.setdefault('DISCORD_TOKENS', 'token1')
os.environ.setdefault('CHANNEL_IDS', '1')

sys.path.insert(0, '/workspaces/Combius')
from combius import BettingTracker, build_token_analytics_path


class BettingTrackerTests(unittest.TestCase):
    def test_coinflip_loss_doubles_current_bet_and_updates_net(self):
        tracker = BettingTracker(base_bets={'cf': 10, 'bj': 10, 'slots': 10})
        msg = {
            'author': {'id': '408785106942115850'},
            'content': 'You lost 10 cowoncy in coinflip.'
        }

        result = tracker.handle_message(msg)

        self.assertEqual(result['game'], 'cf')
        self.assertEqual(result['outcome'], 'loss')
        self.assertEqual(tracker.state['cf']['current_bet'], 20)
        self.assertEqual(tracker.net_profit_loss, -10)

    def test_blackjack_tie_keeps_bet_the_same(self):
        tracker = BettingTracker(base_bets={'cf': 10, 'bj': 10, 'slots': 10})
        msg = {
            'author': {'id': '408785106942115850'},
            'content': 'Blackjack result: Tie/Push',
        }

        result = tracker.handle_message(msg)

        self.assertEqual(result['game'], 'bj')
        self.assertEqual(result['outcome'], 'tie')
        self.assertEqual(tracker.state['bj']['current_bet'], 10)
        self.assertEqual(tracker.net_profit_loss, 0)

    def test_slots_win_resets_bet_to_base(self):
        tracker = BettingTracker(base_bets={'cf': 10, 'bj': 10, 'slots': 10})
        tracker.state['slots']['current_bet'] = 20
        msg = {
            'author': {'id': '408785106942115850'},
            'content': 'Slots x2.5 reward! You won 20 cowoncy.'
        }

        result = tracker.handle_message(msg)

        self.assertEqual(result['game'], 'slots')
        self.assertEqual(result['outcome'], 'win')
        self.assertEqual(tracker.state['slots']['current_bet'], 10)
        self.assertEqual(tracker.net_profit_loss, 20)

    def test_stop_loss_resets_to_base_bet(self):
        tracker = BettingTracker(base_bets={'cf': 10, 'bj': 10, 'slots': 10}, stop_loss_limit=20000)
        tracker.state['cf']['current_bet'] = 20000
        msg = {
            'author': {'id': '408785106942115850'},
            'content': 'You lost 10000 cowoncy in coinflip.'
        }

        tracker.handle_message(msg)

        self.assertEqual(tracker.state['cf']['current_bet'], 10)

    def test_token_analytics_path_is_unique_per_token(self):
        path_a = build_token_analytics_path('token-alpha')
        path_b = build_token_analytics_path('token-beta')

        self.assertNotEqual(path_a, path_b)
        self.assertTrue(path_a.endswith('.json'))


if __name__ == '__main__':
    unittest.main()
