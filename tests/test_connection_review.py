import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'connection_review', Path(__file__).parents[1] / 'scripts/connection_review.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ConnectionReviewTests(unittest.TestCase):
    def test_all_segments_including_automatic_continuations_remain_in_inventory(self):
        data = dict(spanners=[dict(kind='Slur', visible=True, up=True, track=4,
                                  startTick=0, endTick=1920, segments=[
            dict(system=0, box=dict(w=20), o2=dict(y=1.1), o3=dict(y=1.1)),
            dict(system=1, box=dict(w=2))])])
        report = m.inventory(data)
        self.assertEqual(report['segment_count'], 2)
        self.assertEqual(report['segments'][0]['reasons'], [])
        self.assertIn('continuation-requires-independent-inspection',
                      report['segments'][1]['reasons'])
        self.assertTrue(all(s['requires_visual_inspection'] for s in report['segments']))
        self.assertFalse(report['visual_acceptance'])

    def test_controls_scaled_by_actual_span_not_up_flag(self):
        segment = dict(system=0, box=dict(w=4), o2=dict(y=1.1), o3=dict(y=1.1))
        curve = dict(kind='Tie', visible=True, up=True, track=0,
                     startTick=0, endTick=480, segments=[segment])
        report = m.inventory(dict(spanners=[curve]))
        self.assertIn('short-span-large-control-offset', report['segments'][0]['reasons'])
        self.assertFalse(report['visual_acceptance'])
        curve['visible'] = False
        self.assertEqual(m.inventory(dict(spanners=[curve]))['segment_count'], 0)

    def test_invalid_snapshot_is_not_accepted(self):
        with self.assertRaises(ValueError):
            m.inventory(dict(error='reader failed', spanners=[]))


if __name__ == '__main__':
    unittest.main()
