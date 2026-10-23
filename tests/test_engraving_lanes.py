import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('lanes', Path(__file__).parents[1]/'scripts/engraving_lanes.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def item(i, kind, box, track=0, page=0):
    return dict(id=i, kind=kind, box=box, track=track, page=page, system=0)


class LaneTests(unittest.TestCase):
    def test_page_isolation_and_neighbor_staff(self):
        a = item('a', 'articulation', [0, 0, 1, 1])
        b = item('b', 'numeral', [0, 0, 1, 1], track=4)
        c = item('c', 'numeral', [0, 0, 1, 1], page=1)
        hits = m.candidates([a, b, c])
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0]['cross_staff'])

    def test_tuplet_pair_moves_together_and_neighbor_space_is_reported(self):
        data = [item('prev', 'numeral', [0, 2, 2, 2]),
                item('digit', 'numeral', [0, 5, 2, 2], 4),
                item('label', 'tuplet-label', [0, 4, 1, 1], 4),
                item('bracket', 'tuplet-line', [0, 4, 8, .2], 4),
                item('accent', 'articulation', [0, 4, 1, 1], 4),
                item('eight', 'octave', [0, 4, 8, 1], 4)]
        plan = m.lane_proposals(data)[0]
        self.assertEqual(set(plan['layers'][0]['ids']), {'label', 'bracket'})
        self.assertGreater(plan['extra_previous_staff_gap'], 0)
        self.assertLess(plan['layers'][-1]['dy'], plan['layers'][0]['dy'])

    def test_nested_tuplet_labels_clear_both_brackets(self):
        data = [item('outer', 'tuplet-line', [0, 3, 12, .4]),
                item('outer-label', 'tuplet-label', [3, 2, 1, 1.3]),
                item('inner', 'tuplet-line', [6, 4, 6, .4]),
                item('inner-label', 'tuplet-label', [8, 3, 1, 1.3])]
        plans = {p['line']: p for p in m.tuplet_proposals(data)}
        inner = plans['inner']; outer = plans['outer']
        inner_top = 3+inner['label_dy']
        self.assertLess(3.4+outer['line_dy'], inner_top)
        self.assertLess(4.3+inner['label_dy'], 4+inner['line_dy'])

    def test_local_marks_do_not_move_noncolliding_accents(self):
        data = [item('digit', 'numeral', [0, 5, 1, 1]),
                item('line', 'tuplet-line', [0, 4, 2, .2]),
                item('hit', 'articulation', [0, 4, .8, .5]),
                item('clear', 'articulation', [5, 4, .8, .5])]
        changes = m.local_mark_proposals(data)[0]['changes']
        self.assertEqual([c['id'] for c in changes], ['hit'])
        self.assertLess(changes[0]['box'][1]+.5, 4)

    def test_horizontal_near_contact_requires_neighbor_spacing(self):
        data = [item('dot', 'text', [1, 4, .3, .5]),
                item('accent', 'articulation', [.1, 4, .85, .5], 4),
                item('digit', 'numeral', [.1, 6, 1, 1], 4)]
        plans = m.local_mark_proposals(data)
        self.assertGreater(plans[0]['extra_previous_staff_gap'], 0)

    def test_empty_renderer_cannot_produce_pass(self):
        with self.assertRaises(ValueError):
            m.analyze({'rows': []})

    def test_failed_renderer_cannot_produce_pass(self):
        with self.assertRaises(ValueError):
            m.analyze({'error': 'no score'})


if __name__ == '__main__':
    unittest.main()
