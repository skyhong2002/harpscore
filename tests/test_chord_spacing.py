"""Semantic/format checks; synthetic bounds here do not certify rendered appearance."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('chord_spacing', ROOT/'tools/chord_spacing.py')
chords = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chords)


def label(value, x=1, size=9, dependent=0, extra=''):
    return (f'<StaffText><eid>original-{x}</eid><autoplace>0</autoplace>'
            f'<family>Avenir Next</family><size>{size}</size>'
            f'<sizeIsSpatiumDependent>{dependent}</sizeIsSpatiumDependent>'
            f'<align>center,baseline</align><offset x="{x}" y="3.05"/>{extra}'
            f'<text><font face="Avenir Next"/>{value}</text></StaffText>')


def fixture(labels, spatium=1.764):
    # A single semantic case, not a replacement engraving reference or exercise.
    return (f'<museScore version="4.60"><Score><Style><spatium>{spatium}</spatium></Style>'
            '<Part><Staff id="1"><StaffType group="pitched"/></Staff></Part>'
            '<Staff id="1"><Measure><voice><TimeSig><sigN>4</sigN><sigD>4</sigD></TimeSig>'
            '<Chord><durationType>whole</durationType><Note><pitch>60</pitch><velocity>72</velocity>'
            '</Note></Chord><Harmony><name>Ab7</name></Harmony>'
            + labels + '</voice></Measure></Staff></Score></museScore>').encode()


def measurements(request):
    return dict(schemaVersion=1, probe_id=request['probe_id'], request=request, error=None,
                environment=dict(backend='native StaffText.bbox'),
                measurements=[dict(key=q['key'], leftEm=.1, rightEm=.7)
                              for q in request['queries']])


def semantic(node):
    return (node.tag, tuple(sorted(node.attrib.items())), (node.text or '').strip(),
            (node.tail or '').strip(), tuple(semantic(c) for c in node))


class ChordSpacingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.source = self.folder/'source.mscx'
        self.source.write_bytes(fixture(label('A♭7') + label('A♭7', 7) + label('F♯dim', 12)
                                        + label('E♭maj7/B♭', 17) + label('1', 21)))

    def request(self):
        return chords.inventory(self.source, [1])

    def test_spelling_and_slash_bass(self):
        for text in ['A♭7', 'Ab7', 'F#dim', 'G♯m7(b5)', 'E♭maj7/B♭', 'C/Bb', 'Bbb7']:
            with self.subTest(text=text):
                parts = chords.chunks(text)
                self.assertIsNotNone(parts)
                self.assertEqual(''.join(p[0] for p in parts), text)
        for text in ['Fm', '♭', '7', 'A♭ text', 'A♭7)', 'A♭(7', 'Ab#7', 'A♭7/B/C', 'tr']:
            self.assertIsNone(chords.chunks(text), text)

    def test_native_probe_samples_and_unique_queries(self):
        request = self.request()
        self.assertEqual(len(request['targets']), 4)
        self.assertEqual(len([q for q in request['queries'] if q['text'] == 'A']), 1)
        probe = self.folder/'probe.mscx'
        chords.write_candidate(self.source, request, probe)
        root = chords.read_score(probe)[3]
        self.assertEqual(root.findtext('Score/metaTag'), request['probe_id'])
        for query in request['queries']:
            matches = [e for e in root.findall('.//StaffText')
                       if chords.plain(e.find('text')) == query['text']
                       and abs(float(e.find('offset').get('x')) - query['x']) < 1e-7]
            self.assertTrue(matches, query)

    def test_apply_preserves_every_non_target_and_anchor(self):
        request = self.request()
        out = self.folder/'out.mscx'
        report = chords.apply(self.source, measurements(request), out)
        before, after = chords.read_score(self.source)[3], chords.read_score(out)[3]
        v1, v2 = before.find('.//voice'), after.find('.//voice')
        original = list(v1)
        rendered = list(v2)
        index = 0
        for item in original:
            if item.tag != 'StaffText' or chords.chunks(chords.plain(item.find('text'))) is None:
                self.assertEqual(semantic(item), semantic(rendered[index]))
                index += 1
                continue
            parts = chords.chunks(chords.plain(item.find('text')))
            members = rendered[index:index + len(parts)]
            self.assertEqual(''.join(chords.plain(m.find('text')) for m in members),
                             chords.plain(item.find('text')))
            self.assertEqual(members[0].findtext('eid'), item.findtext('eid'))
            self.assertTrue(all(m.find('eid') is None for m in members[1:]))
            self.assertEqual(members[0].find('offset').get('x'),
                             f'{float(item.find("offset").get("x")):.8f}')
            index += len(parts)
        self.assertEqual(index, len(rendered))
        self.assertFalse(report['visual_acceptance'])
        self.assertEqual(report['changed_labels'], 4)
        rerun = chords.inventory(out, [1])
        self.assertEqual(rerun['targets'], [])
        no_op = self.folder/'no-op.mscx'
        chords.apply(out, measurements(rerun), no_op)
        self.assertEqual(out.read_bytes(), no_op.read_bytes())

    def test_bounds_clearance_and_spatium_scaling(self):
        request = self.request()
        metrics = {m['key']: m for m in measurements(request)['measurements']}
        for target in request['targets']:
            positions = chords.layout(target, metrics, request['spatium_pt'], .9)
            for left, right in zip(positions, positions[1:]):
                self.assertAlmostEqual((right['ink_left'] - left['ink_right']) * request['spatium_pt'], .9)
        self.source.write_bytes(fixture(label('D♭7', size=10, dependent=1), spatium=2.54))
        request = self.request()
        self.assertAlmostEqual(request['spatium_pt'], 7.2)
        self.assertAlmostEqual(request['targets'][0]['size_pt'], 14.4)

    def test_size_identity_and_supported_font_switches(self):
        self.source.write_bytes(fixture(label('A♭7') + label('A♭7', 7, size=12)))
        request = self.request()
        self.assertEqual(len(request['queries']), 6)
        self.assertNotEqual(request['targets'][0]['members'][0]['key'],
                            request['targets'][1]['members'][0]['key'])
        self.source.write_bytes(fixture(label('A<font face="Arial"/>♭<font face="Avenir Next"/>7')))
        self.assertEqual(self.request()['targets'][0]['text'], 'A♭7')

    def test_unsupported_overlays_reported_without_guessing(self):
        for extra in ['<fontStyle>1</fontStyle>', '<autoplace>1</autoplace>', '<visible>0</visible>',
                      '<frameType>1</frameType>', '<style>Expression</style>',
                      '<channelSwitch voice="0" name="pizzicato"/>', '<linkedMain/>']:
            # Replace rather than duplicate an existing field.
            text = label('A♭7', extra=extra)
            for tag in ['autoplace']:
                if f'<{tag}>' in extra:
                    text = text.replace(f'<{tag}>0</{tag}>', '')
            self.source.write_bytes(fixture(text))
            request = self.request()
            self.assertEqual(request['targets'], [], extra)
            self.assertEqual(len(request['skipped']), 1)
        self.source.write_bytes(fixture(label('A<font size="12"/>♭7')))
        self.assertEqual(len(self.request()['skipped']), 1)

    def test_stale_incomplete_invalid_measurements_refused(self):
        request = self.request()
        for change in ['probe', 'backend', 'missing', 'duplicate', 'error', 'nan', 'inverted']:
            metrics = measurements(request)
            if change == 'probe': metrics['probe_id'] = 'stale'
            if change == 'backend': metrics['environment']['backend'] = 'Qt TextMetrics'
            if change == 'missing': metrics['measurements'].pop()
            if change == 'duplicate': metrics['measurements'].append(metrics['measurements'][0])
            if change == 'error': metrics['error'] = 'Font is not installed'
            if change == 'nan': metrics['measurements'][0]['leftEm'] = float('nan')
            if change == 'inverted': metrics['measurements'][0]['rightEm'] = 0
            with self.subTest(change=change), self.assertRaises(ValueError):
                chords.apply(self.source, metrics, self.folder/'rejected.mscx')
        self.source.write_bytes(self.source.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'changed since prepare'):
            chords.apply(self.source, measurements(request), self.folder/'stale.mscx')

    def test_new_destinations_checked_before_mutation(self):
        for outputs in [[self.source, self.folder/'new.json'],
                        [self.folder/'same', self.folder/'same']]:
            with self.assertRaises(ValueError):
                chords.new_destinations([self.source], outputs)
        result = subprocess.run([sys.executable, str(ROOT/'tools/chord_spacing.py'), 'prepare',
                                 str(self.source), str(self.source), '--staff', '1',
                                 '--probe', str(self.folder/'probe.mscx')], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.folder/'probe.mscx').exists())

    def test_mscz_other_members_preserved(self):
        source = self.folder/'source.mscz'
        with zipfile.ZipFile(source, 'w') as archive:
            archive.writestr('source.mscx', self.source.read_bytes())
            archive.writestr('META-INF/container.xml', b'container')
            archive.writestr('audio/settings.json', b'{"unchanged":true}')
        request = chords.inventory(source, [1])
        out = self.folder/'out.mscz'
        chords.apply(source, measurements(request), out)
        with zipfile.ZipFile(source) as before, zipfile.ZipFile(out) as after:
            self.assertEqual(before.namelist(), after.namelist())
            for name in before.namelist():
                if not name.endswith('.mscx'):
                    self.assertEqual(before.read(name), after.read(name))


if __name__ == '__main__':
    unittest.main()
