import os
import sys
import tempfile
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

    def test_blackjack_messages_are_ignored(self):
        tracker = BettingTracker(base_bets={'cf': 10})
        msg = {
            'author': {'id': '408785106942115850'},
            'content': 'Blackjack result: Tie/Push',
        }

        result = tracker.handle_message(msg)

        self.assertIsNone(result)
        self.assertEqual(tracker.state['cf']['current_bet'], 10)
        self.assertEqual(tracker.net_profit_loss, 0)

    def test_slots_win_is_detected_and_updates_state(self):
        tracker = BettingTracker(base_bets={'cf': 10, 'slots': 10})
        tracker.state['slots']['current_bet'] = 20
        msg = {
            'author': {'id': '408785106942115850'},
            'content': 'Slots x2.5 reward! You won 20 cowoncy.',
        }

        result = tracker.handle_message(msg)

        self.assertEqual(result['game'], 'slots')
        self.assertEqual(result['outcome'], 'win')
        self.assertEqual(tracker.state['slots']['current_bet'], 10)
        self.assertEqual(tracker.net_profit_loss, 20)

    def test_slots_loss_is_detected_and_doubles_bet(self):
        tracker = BettingTracker(base_bets={'cf': 10, 'slots': 10})
        tracker.state['slots']['current_bet'] = 10
        msg = {
            'author': {'id': '408785106942115850'},
            'content': 'You lost 10 cowoncy in slots.',
        }

        result = tracker.handle_message(msg)

        self.assertEqual(result['game'], 'slots')
        self.assertEqual(result['outcome'], 'loss')
        self.assertEqual(tracker.state['slots']['current_bet'], 20)
        self.assertEqual(tracker.net_profit_loss, -10)

    def test_slots_won_nothing_is_not_treated_as_a_win(self):
        tracker = BettingTracker(base_bets={'cf': 10, 'slots': 10})
        tracker.state['slots']['current_bet'] = 20
        msg = {
            'author': {'id': '408785106942115850'},
            'content': 'Slots result: You won nothing.',
        }

        result = tracker.handle_message(msg)

        self.assertIsNone(result)
        self.assertEqual(tracker.state['slots']['current_bet'], 20)
        self.assertEqual(tracker.net_profit_loss, 0)

    def test_slots_emoji_win_is_detected(self):
        tracker = BettingTracker(base_bets={'cf': 10, 'slots': 10})
        tracker.state['slots']['current_bet'] = 20
        msg = {
            'author': {'id': '408785106942115850'},
            'content': 'Slots x2.5 reward! You won <:cowoncy:>.',
        }

        result = tracker.handle_message(msg)

        self.assertEqual(result['game'], 'slots')
        self.assertEqual(result['outcome'], 'win')
        self.assertEqual(tracker.state['slots']['current_bet'], 10)
        self.assertEqual(tracker.net_profit_loss, 0)

    def test_stop_loss_resets_to_base_bet(self):
        tracker = BettingTracker(base_bets={'cf': 10, 'bj': 10, 'slots': 10}, stop_loss_limit=20000)
        tracker.state['cf']['current_bet'] = 20000
        msg = {
            'author': {'id': '408785106942115850'},
            'content': 'You lost it all... :c'
        }

        tracker.handle_message(msg)

        self.assertEqual(tracker.state['cf']['current_bet'], 10)

    def test_stop_loss_warning_callback_is_triggered_and_resets_to_base(self):
        warnings = []
        tracker = BettingTracker(base_bets={'cf': 10, 'bj': 10, 'slots': 10}, stop_loss_limit=20000,
                                 notify_chat=lambda msg: warnings.append(msg))
        tracker.state['cf']['current_bet'] = 20000
        msg = {
            'author': {'id': '408785106942115850'},
            'content': 'You lost it all... :c'
        }

        tracker.handle_message(msg)

        self.assertEqual(tracker.state['cf']['current_bet'], 10)
        self.assertTrue(any('Stop-loss triggered' in warning for warning in warnings))

    def test_conservative_mode_grows_by_base_bet_on_loss(self):
        tracker = BettingTracker(base_bets={'cf': 10, 'bj': 10, 'slots': 10}, betting_mode='capped')
        tracker.state['cf']['current_bet'] = 10
        msg = {
            'author': {'id': '408785106942115850'},
            'content': 'You lost it all... :c'
        }

        tracker.handle_message(msg)

        self.assertEqual(tracker.state['cf']['current_bet'], 20)

    def test_next_suggested_coinflip_command_respects_stop_loss_limit(self):
        tracker = BettingTracker(base_bets={'cf': 10, 'bj': 10, 'slots': 10}, stop_loss_limit=20000)
        tracker.state['cf']['current_bet'] = 20000

        self.assertEqual(tracker.get_next_command_suggestion('cf'), 'owo cf 10')

    def test_persist_analytics_writes_default_file_alias(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = BettingTracker(base_bets={'cf': 10, 'bj': 10, 'slots': 10}, analytics_path=os.path.join(tmpdir, 'token.json'))
            tracker._persist_analytics()

            default_path = os.path.join(tmpdir, 'betting_analytics.json')
            self.assertTrue(os.path.exists(default_path))

    def test_token_analytics_path_is_unique_per_token(self):
        path_a = build_token_analytics_path('token-alpha')
        path_b = build_token_analytics_path('token-beta')

        self.assertNotEqual(path_a, path_b)
        self.assertTrue(path_a.endswith('.json'))


if __name__ == '__main__':
    unittest.main()
