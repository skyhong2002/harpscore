"""Read-only collision candidates and vertical lane proposals from renderer boxes.

Input is the JSON produced by the MuseScore geometry reader (rows and
otherSpanners). No score is edited. Coordinates must use page-local staff spaces.
Proposals require visual review, a fresh render, and musical invariant checks.
"""
import argparse
from collections import defaultdict
import hashlib
import html
import json
import re


def rectangle(box):
    return [box['x'] + box.get('bx', 0), box['y'] + box.get('by', 0),
            box['w'], box['h']]


def plain(text):
    return html.unescape(re.sub('<[^>]+>', '', text or '')).strip()


def xoverlap(a, b, gap=0):
    return min(a[0] + a[2], b[0] + b[2]) + gap > max(a[0], b[0])


def overlap(a, b, gap=0):
    return xoverlap(a, b, gap) and min(a[1]+a[3], b[1]+b[3])+gap > max(a[1], b[1])


def elements(data):
    """Exclude transparent note anchors; keep visible text and articulations."""
    result, systems = [], {}
    for row in data['rows']:
        if not row.get('measureBox') or row['measureBox']['w'] <= 0:
            continue
        systems[row['system']] = row['page']
        common = {k: row[k] for k in ('system', 'page', 'measure', 'tick')}
        for i, annotation in enumerate(row['annotations']):
            text = plain(annotation['text'])
            size = annotation.get('size', 0)
            kind = ('meter' if re.fullmatch(r'\d+/\d+', text) else
                    'tuplet-label' if text.isdigit() and size in (8, 8.8) else
                    'numeral' if text in list('01234567xX') else 'text')
            result.append(dict(common, id=f"a:{len(result)}", kind=kind,
                               track=annotation['track'], text=text,
                               box=rectangle(annotation['box']),
                               offset=[annotation['ox'], annotation['oy']]))
        for event in row['events']:
            for i, mark in enumerate(event.get('articulations', [])):
                if mark.get('visible', True):
                    result.append(dict(common, id=f"a:{len(result)}", kind='articulation',
                                       track=event['track'], box=rectangle(mark['box']),
                                       offset=[mark['ox'], mark['oy']]))
    for i, spanner in enumerate(data.get('otherSpanners', [])):
        if not spanner.get('visible', True):
            continue
        text = plain(spanner.get('startText', ''))
        for j, segment in enumerate(spanner['segments']):
            system = segment['system']
            if system not in systems:
                continue
            kind = ('octave' if '⑧' in text else
                    'tuplet-line' if not text and segment.get('offsetY', 0) < 0
                    and spanner['type'] == 94 else 'other-line')
            result.append(dict(id=f's:{i}:{j}', kind=kind, track=spanner['track'],
                               page=systems[system], system=system,
                               tick=spanner.get('startTick'), text=text,
                               box=rectangle(segment['box']),
                               offset=[segment.get('offsetX', 0), segment.get('offsetY', 0)]))
    return result


def candidates(items, gap=.2):
    """Broad-phase candidates, including adjacent staves, never a pass/fail oracle."""
    by_system = defaultdict(list)
    for item in items:
        by_system[item['page'], item['system']].append(item)
    output = []
    target = {'meter', 'tuplet-label', 'tuplet-line', 'articulation', 'octave'}
    for group in by_system.values():
        group.sort(key=lambda e: e['box'][0])
        for i, left in enumerate(group):
            for right in group[i+1:]:
                if right['box'][0] > left['box'][0]+left['box'][2]+gap:
                    break
                if not ({left['kind'], right['kind']} & target):
                    continue
                if overlap(left['box'], right['box'], gap):
                    output.append({'a': left['id'], 'b': right['id'],
                                   'page': left['page'], 'system': left['system'],
                                   'status': 'needs-visual-review',
                                   'cross_staff': left['track']//4 != right['track']//4})
    return output


def lane_proposals(items, gap=.35):
    """Reserve measured vertical bands; do not independently move tuplet labels.

    Every tuplet bracket and label in a staff/system receives one translation.
    This preserves nested tuplet relative geometry but does NOT repair an already
    malformed nested group. Articulations then clear that band, octave ranges
    clear articulations, and meters clear octave ranges. Neighbor clearance is
    reported separately so moving a mark cannot silently invade another staff.
    """
    groups = defaultdict(list)
    for item in items:
        groups[item['page'], item['system'], item['track']//4].append(item)
    proposals = []
    for key, group in sorted(groups.items()):
        digits = [e for e in group if e['kind'] == 'numeral']
        if not digits:
            continue
        baseline = min(e['box'][1] for e in digits)
        # Include nearby upper accidentals/dots in the protected numeral band.
        protected = [e for e in group if e['kind'] in ('numeral', 'text')
                     and e['box'][1]+e['box'][3] >= baseline-2]
        ceiling = min(e['box'][1] for e in protected)
        moved = []
        for kinds in [('tuplet-line', 'tuplet-label'), ('articulation',), ('octave',), ('meter',)]:
            layer = [e for e in group if e['kind'] in kinds]
            if not layer:
                continue
            bottom = max(e['box'][1]+e['box'][3] for e in layer)
            dy = min(0, ceiling-gap-bottom)
            ceiling = min(e['box'][1]+dy for e in layer)
            if dy < -.001:
                moved.append({'kinds': list(kinds), 'dy': dy, 'ids': [e['id'] for e in layer]})
        previous = groups.get((key[0], key[1], key[2]-1), [])
        previous_bottom = max((e['box'][1]+e['box'][3] for e in previous
                               if e['kind'] in ('numeral', 'text')), default=None)
        extra = max(0, previous_bottom+gap-ceiling) if previous_bottom is not None else 0
        if moved or extra:
            proposals.append({'page': key[0], 'system': key[1], 'staff': key[2]+1,
                              'layers': moved, 'extra_previous_staff_gap': extra,
                              'status': 'proposal-not-applied'})
    return proposals


def analyze(data):
    if data.get('error'):
        raise ValueError('Renderer inspection failed: '+str(data['error']))
    if not data.get('rows'):
        raise ValueError('Renderer inspection contains no rows')
    items = elements(data)
    if not items:
        raise ValueError('Renderer inspection contains no measurable elements')
    return {'proof_boundary': 'Geometry candidates and lane proposals only; no score edits or visual acceptance.',
            'elements': items, 'candidates': candidates(items), 'proposals': lane_proposals(items)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('geometry')
    parser.add_argument('report')
    args = parser.parse_args()
    with open(args.geometry, 'rb') as stream:
        raw = stream.read()
    report = analyze(json.loads(raw))
    report['geometry_sha256'] = hashlib.sha256(raw).hexdigest()
    with open(args.report, 'w') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(f"{len(report['candidates'])} review candidates; {len(report['proposals'])} lane proposals")
