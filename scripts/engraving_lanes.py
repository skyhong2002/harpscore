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
    for i, spanner in enumerate(data.get('spanners', [])):
        if not spanner.get('visible', True):
            continue
        for j, segment in enumerate(spanner.get('segments', [])):
            system = segment['system']
            if system in systems:
                result.append(dict(id=f'curve:{i}:{j}', kind='curve', track=spanner['track'],
                                   page=systems[system], system=system,
                                   tick=spanner.get('startTick'), box=rectangle(segment['box'])))
    return result


def candidates(items, gap=.2):
    """Broad-phase candidates, including adjacent staves, never a pass/fail oracle."""
    by_system = defaultdict(list)
    for item in items:
        by_system[item['page']].append(item)
    output = []
    target = {'meter', 'tuplet-label', 'tuplet-line', 'articulation', 'octave', 'curve'}
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
                                   'system_b': right['system'],
                                   'cross_system': left['system'] != right['system'],
                                   'cross_staff': left['track']//4 != right['track']//4})
    return output


def tuplet_proposals(items, gap=.25):
    """Separate label ink from its bracket, then keep outer brackets above children.

    Uses measured boxes from the numbered-overlay adapter. Ambiguous label/line
    associations are omitted for manual review. Does not alter musical tuplets.
    """
    groups = defaultdict(list)
    for e in items:
        groups[e['page'], e['system'], e['track']].append(e)
    plans = []
    for key, group in groups.items():
        lines = [e for e in group if e['kind'] == 'tuplet-line']
        assigned = defaultdict(list)
        for label in (e for e in group if e['kind'] == 'tuplet-label'):
            b = label['box']; centre = b[0]+b[2]/2
            options = sorted((abs(b[1]+b[3]-e['box'][1]), e['id'], e)
                             for e in lines if e['box'][0] <= centre <= e['box'][0]+e['box'][2])
            if not options or (len(options)>1 and abs(options[0][0]-options[1][0])<.05):
                continue
            assigned[options[0][1]].append(label)
        placed = []
        for line in sorted(lines, key=lambda e:e['box'][2]):
            labels = assigned[line['id']]
            if len(labels) != 1:
                continue
            label = labels[0]; b = line['box']; lb = label['box']
            # A bracket can enclose a smaller bracket on the same rhythmic span.
            children = [c for c in placed if b[0] <= c['x']+.01
                        and b[0]+b[2] >= c['right']-.01 and b[2] > c['width']+.05]
            near_text = [e['box'] for e in group if e['kind'] in ('text', 'numeral')
                         and overlap(b, e['box'], gap)]
            line_dy = min([0]+[c['top']-gap-(b[1]+b[3]) for c in children]
                          +[t[1]-gap-(b[1]+b[3]) for t in near_text])
            label_dy = min(line_dy, b[1]+line_dy-gap-(lb[1]+lb[3]))
            placed.append(dict(x=b[0], right=b[0]+b[2], width=b[2], top=lb[1]+label_dy))
            if line_dy < -.001 or label_dy < -.001:
                plans.append(dict(page=key[0], system=key[1], track=key[2],
                                  line=line['id'], label=label['id'],
                                  line_dy=line_dy, label_dy=label_dy,
                                  status='proposal-not-applied'))
    return plans


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


def local_mark_proposals(items, gap=.25):
    """Move only colliding marks, using horizontal overlap and neighboring staves.

    Small/low articulations settle before higher articulations. Octave guides
    then clear the settled marks. Reports spacer needs rather than applying them.
    """
    groups = defaultdict(list)
    for e in items:
        groups[e['page'], e['system'], e['track']//4].append(e)
    plans = []
    for key, group in groups.items():
        obstacles = [e['box'][:] for e in group if e['kind'] in
                     ('numeral', 'text', 'tuplet-label', 'tuplet-line', 'curve')]
        changes = []
        for kind in ('articulation', 'octave', 'meter'):
            layer = sorted((e for e in group if e['kind']==kind),
                           key=lambda e:e['box'][1]+e['box'][3], reverse=True)
            for e in layer:
                b = e['box'][:]; original = b[1]
                for _ in range(len(obstacles)+1):
                    hits = [o for o in obstacles if overlap(b,o,gap)]
                    if not hits:break
                    b[1] = min(o[1]-gap-b[3] for o in hits)-.00001
                obstacles.append(b)
                if b[1] < original-.001:
                    changes.append(dict(id=e['id'], dy=b[1]-original, box=b))
        previous = groups.get((key[0],key[1],key[2]-1),[])
        # Even an unchanged guide may already be too close to the preceding staff.
        tops = obstacles
        extra = max([0]+[p['box'][1]+p['box'][3]+gap-b[1]
                    for p in previous
                    for b in tops if xoverlap(p['box'], b, gap)])
        if changes or extra>0:
            plans.append(dict(page=key[0], system=key[1], staff=key[2]+1,
                              changes=changes, extra_previous_staff_gap=extra,
                              status='proposal-not-applied'))
    return plans


def analyze(data):
    if data.get('error'):
        raise ValueError('Renderer inspection failed: '+str(data['error']))
    if not data.get('rows'):
        raise ValueError('Renderer inspection contains no rows')
    items = elements(data)
    if not items:
        raise ValueError('Renderer inspection contains no measurable elements')
    return {'proof_boundary': 'Geometry candidates and lane proposals only; no score edits or visual acceptance.',
            'elements': items, 'candidates': candidates(items),
            'tuplet_proposals': tuplet_proposals(items),
            'local_mark_proposals': local_mark_proposals(items),
            'proposals': lane_proposals(items)}


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
