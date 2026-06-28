import os
import sys
import unittest

os.environ.setdefault('DISCORD_TOKENS', 'token1')
os.environ.setdefault('CHANNEL_IDS', '1')

sys.path.insert(0, '/workspaces/Combius')
from combius import InventoryParser


class InventoryParserGemTests(unittest.TestCase):
    def test_get_best_gems_uses_quantity_and_does_not_pick_empty_gems(self):
        inv_data = {
            'gem_ids': [51, 56],
            'gem_quantities': {51: 3, 56: 0},
        }

        result = InventoryParser.get_best_gems(inv_data, min_tier=3)

        self.assertEqual(result, [51])


if __name__ == '__main__':
    unittest.main()
