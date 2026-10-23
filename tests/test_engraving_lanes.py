import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('lanes', Path(__file__).parents[1]/'scripts/engraving_lanes.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def item(i, kind, box, track=0, page=0):
    return dict(id=i, kind=kind, box=box, track=track, page=page, system=0)


class LaneTests(unittest.TestCase):
    def test_close_accent_label_is_detected_without_expanding_all_boxes(self):
        label = item('label', 'tuplet-label', [0, 0, 1, 1])
        accent = item('accent', 'articulation', [1.3, .5, .8, .4])
        self.assertFalse(m.candidates([label, accent]))
        self.assertEqual(len(m.accent_label_contacts([label, accent])), 1)
        accent['box'][1] = -1
        self.assertFalse(m.accent_label_contacts([label, accent]))
        accent['box'][1] = .5
        accent['track'] = 4
        self.assertFalse(m.accent_label_contacts([label, accent]))

    def test_system_spacing_uses_ink_and_does_not_compare_pages(self):
        data = []
        for page, tops in ((0, (0, 30, 42)), (1, (0, 70))):
            for system, top in enumerate(tops):
                e = item(str((page, system)), 'numeral', [0, top, 2, 10], page=page)
                e['system'] = system
                data.append(e)
        guide = item('guide', 'octave', [0, 26, 8, 1])
        guide['system'] = 1
        data.append(guide)
        gaps = m.system_spacing(data)
        self.assertEqual([g['gap'] for g in gaps], [16, 2, 60])
        self.assertEqual([g['status'] for g in gaps],
                         ['review-excess-gap', 'measured', 'measured'])

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

    def test_accidental_ink_clears_tuplet_bracket(self):
        data = [item('line', 'tuplet-line', [0, 3, 5, .4]),
                item('label', 'tuplet-label', [2, 1, 1, 1.3]),
                item('flat', 'text', [1, 3.1, .7, 1.4])]
        plan = m.tuplet_proposals(data)[0]
        self.assertLess(3.4+plan['line_dy'], 3.1)

    def test_previous_hairpin_reserves_space(self):
        data = [item('hairpin', 'other-line', [0, 5, 10, 1]),
                item('digit', 'numeral', [0, 6, 1, 1], 4)]
        self.assertGreater(m.local_mark_proposals(data)[0]['extra_previous_staff_gap'], 0)

    def test_candidates_include_adjacent_systems_on_same_page(self):
        a = item('mark', 'articulation', [0, 5, 1, 1])
        b = item('next-digit', 'numeral', [0, 5.5, 1, 1])
        b['system'] = 1
        hits = m.candidates([a,b])
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0]['cross_system'])

    def test_symbol_can_move_down_into_clear_slot(self):
        mark = item('ornament', 'articulation', [1, 2, 1, .5])
        digit = item('digit', 'numeral', [1, 5, 1, 1])
        bracket = item('bracket', 'tuplet-line', [0, 3, 4, .3])
        plan = m.symbol_slot_above(mark, digit, [mark, digit, bracket])
        self.assertEqual(plan['status'], 'proposal-not-applied')
        self.assertGreater(plan['dy'], 0)

    def test_symbol_slot_checks_neighbor_staff_and_system(self):
        mark = item('ornament', 'articulation', [1, 2, 1, .5], 4)
        digit = item('digit', 'numeral', [1, 5, 1, 1], 4)
        neighbor = item('neighbor-dot', 'text', [1, 4.2, .5, .4])
        neighbor['system'] = 1
        plan = m.symbol_slot_above(mark, digit, [mark, digit, neighbor])
        self.assertEqual(plan['status'], 'blocked-slot')
        self.assertEqual(plan['blockers'], ['neighbor-dot'])

    def test_symbol_slot_rejects_unrelated_anchor(self):
        mark = item('ornament', 'articulation', [1, 2, 1, .5])
        digit = item('digit', 'numeral', [9, 5, 1, 1])
        with self.assertRaises(ValueError):
            m.symbol_slot_above(mark, digit, [mark, digit])

    def test_empty_renderer_cannot_produce_pass(self):
        with self.assertRaises(ValueError):
            m.analyze({'rows': []})

    def test_failed_renderer_cannot_produce_pass(self):
        with self.assertRaises(ValueError):
            m.analyze({'error': 'no score'})


if __name__ == '__main__':
    unittest.main()
