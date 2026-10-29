"""Plan/apply local minimum spacing for adjacent one-line Jianpu overlay staves.

Standard library only. Uses a fresh HarpScore renderer snapshot, not hidden note
anchors. Applying a plan never launches MuseScore; render and inspect afterward.
"""
import argparse
from collections import defaultdict
import hashlib
import html
import json
import math
from pathlib import Path
import re
import statistics
import xml.etree.ElementTree as ET
import zipfile

OWNER = 'harpscoreAdaptiveStaffSpacing'
VERSION = 1


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_score(path):
    with zipfile.ZipFile(path) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    names = [n for n in files if n.endswith('.mscx') and '/' not in n]
    if len(names) != 1:
        raise ValueError('Expected one root MSCX in an MSCZ score')
    return files, names[0], ET.fromstring(files[names[0]])


def number(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Non-finite geometry or spacing value')
    return value


def rectangle(b):
    values = [number(b['x']) + number(b.get('bx', 0)),
              number(b['y']) + number(b.get('by', 0)),
              number(b['w']), number(b['h'])]
    if values[2] < 0 or values[3] < 0:
        raise ValueError('Negative bounding-box extent')
    return values


def plain(text):
    return html.unescape(re.sub('<[^>]+>', '', text or '')).strip()


def staff_pair(root, upper, lower):
    score = root.find('Score')
    staves = score.findall('Staff')
    if not (1 <= upper < lower <= len(staves) and lower == upper + 1):
        raise ValueError('Select adjacent staves using one-based indices')
    parts = score.findall('Part/Staff')
    if len(parts) != len(staves):
        raise ValueError('Part/staff mapping is ambiguous')
    for index in (upper - 1, lower - 1):
        # Older files omit staff IDs; their score/part staff order is canonical.
        if parts[index].get('id') and staves[index].get('id'):
            if parts[index].get('id') != staves[index].get('id'):
                raise ValueError('Part/staff IDs disagree')
        if parts[index].findtext('StaffType/lines', '5') != '1':
            raise ValueError('Only adjacent one-line Jianpu overlay staves are supported')
    return score, staves[lower - 1], parts[lower - 1]


def propose(geometry, upper, lower, base, clearance):
    """Return per-measure requirements independent of existing vertical spacing.

    Input indices are one-based. Page + system isolate coordinates. StaffText
    pagePos.y - offsetY supplies the baseline only for manual text overlays.
    """
    base, clearance = number(base), number(clearance)
    if base <= 0 or clearance < 0 or lower != upper + 1 or upper < 1:
        raise ValueError('Invalid staff pair, base spacing or clearance')
    if geometry.get('error'):
        raise ValueError('Geometry reader failed: ' + str(geometry['error']))
    if geometry.get('coordinateUnits', 'staff-space') != 'staff-space':
        raise ValueError('Geometry must use staff-space units')
    if not geometry.get('rows'):
        raise ValueError('Empty geometry snapshot')
    origins, items, measures = defaultdict(list), defaultdict(list), {}
    system_pages = defaultdict(set)
    for row in geometry['rows']:
        key = (row['page'], row['system'])
        system_pages[row['system']].add(row['page'])
        measures[key, row['measure']] = rectangle(row['measureBox'])
        for a in row['annotations']:
            staff = a['track'] // 4 + 1
            if staff not in (upper, lower) or not a.get('visible', True):
                continue
            if a.get('alpha', 255) == 0 or not plain(a.get('text')):
                continue
            if a.get('type') == 54:  # StaffText, not dynamics or native noteheads
                origins[key, staff].append(number(a['box']['y']) - number(a['oy']))
            items[key, staff].append((rectangle(a['box']), row['measure']))
        for event in row.get('events', []):
            staff = event['track'] // 4 + 1
            if staff in (upper, lower):
                for mark in event.get('articulations', []):
                    if mark.get('visible', True):
                        items[key, staff].append((rectangle(mark['box']), row['measure']))
    baselines = {}
    for key in {k for k, _ in measures}:
        for staff in (upper, lower):
            values = origins[key, staff]
            if not values or max(values) - min(values) > .02:
                raise ValueError('Missing/inconsistent overlay baseline at ' + str((key, staff)))
            baselines[key, staff] = statistics.median(values)
    for s in geometry.get('spanners', []) + geometry.get('otherSpanners', []):
        staff = s['track'] // 4 + 1
        if staff not in (upper, lower) or not s.get('visible', True):
            continue
        for segment in s['segments']:
            pages = system_pages[segment['system']]
            page = segment.get('page')
            if page is None:
                if len(pages) != 1:
                    raise ValueError('Spanner segment needs an unambiguous page')
                page = next(iter(pages))
            key = (page, segment['system'])
            if (key, staff) not in baselines:
                raise ValueError('Spanner segment has no matching system')
            items[key, staff].append((rectangle(segment['box']), None))
    targets, systems = {}, []
    for key in sorted({k for k, _ in measures}):
        required = base
        for a, _ in items[key, upper]:
            for b, measure in items[key, lower]:
                left, right = max(a[0], b[0]), min(a[0] + a[2], b[0] + b[2])
                if left >= right:
                    continue
                need = (a[1] + a[3] - baselines[key, upper]
                        - b[1] + baselines[key, lower] + clearance)
                if need <= base + .001:
                    continue
                # Anchor a spanning collision to every affected measure so that
                # moving the line to another system cannot discard its spacer.
                affected = [measure] if measure is not None else [
                    m for (k, m), box in measures.items()
                    if k == key and min(right, box[0] + box[2]) > max(left, box[0])]
                if not affected:
                    raise ValueError('Cannot map collision to a measure')
                need = math.ceil((need - 1e-9) * 20) / 20
                required = max(required, need)
                for m in affected:
                    targets[m] = max(targets.get(m, base), need)
        systems.append(dict(page=key[0], system=key[1], minimum_sp=required,
                            current_sp=baselines[key, lower] - baselines[key, upper]))
    return targets, systems


def make_plan(score_path, geometry_path, upper, lower, base, clearance, reset=False):
    raw = Path(score_path).read_bytes()
    _, _, root = read_score(score_path)
    _, staff, part = staff_pair(root, upper, lower)
    geom_bytes = Path(geometry_path).read_bytes()
    geometry = json.loads(geom_bytes)
    count = len(staff.findall('Measure'))
    seen = {row['measure'] for row in geometry.get('rows', [])}
    if seen != set(range(count)):
        raise ValueError('Geometry measure coverage does not match the score')
    offset = number(part.findtext('distOffset', '0'))
    if offset and not reset:
        raise ValueError('Existing global offset: use --reset-global-offset to replace it explicitly')
    targets, systems = propose(geometry, upper, lower, base, clearance)
    return dict(version=VERSION, score_sha256=digest(raw), geometry_sha256=digest(geom_bytes),
                upper_staff=upper, lower_staff=lower, base_sp=number(base),
                clearance_sp=number(clearance), reset_global_offset=reset,
                targets={str(m + 1): v for m, v in sorted(targets.items())}, systems=systems,
                status='requires-rendered-review',
                scope='one-line manual Jianpu overlays; snapshot-driven, not live editing')


def apply_plan(source, plan, destination):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError('Output must be a new file, distinct from the source')
    if plan.get('version') != VERSION or digest(source.read_bytes()) != plan['score_sha256']:
        raise ValueError('Plan is stale or incompatible; re-render and plan again')
    files, name, root = read_score(source)
    score, staff, part = staff_pair(root, plan['upper_staff'], plan['lower_staff'])
    measures = staff.findall('Measure')
    targets = {int(m): number(v) for m, v in plan['targets'].items()}
    if any(m < 1 or m > len(measures) or v < number(plan['base_sp']) for m, v in targets.items()):
        raise ValueError('Invalid spacer target')
    tag = score.find(f"metaTag[@name='{OWNER}']")
    owned = json.loads(tag.text) if tag is not None else {}
    key = str(plan['lower_staff'])
    # Remove only our own unchanged spacers. Preserve user edits/manual spacers.
    for m, value in owned.get(key, {}).items():
        mi = int(m) - 1
        if 0 <= mi < len(measures):
            for spacer in measures[mi].findall('vspacerUp'):
                if abs(number(spacer.text) - number(value)) < .001:
                    measures[mi].remove(spacer)
    if plan['reset_global_offset']:
        for offset in part.findall('distOffset'):
            part.remove(offset)
    new_owned = {}
    manual = [i + 1 for i, measure in enumerate(measures) if measure.find('vspacerUp') is not None]
    for m, value in targets.items():
        measure = measures[m - 1]
        existing = measure.find('vspacerUp')
        if existing is not None:
            # Never silently replace a manual spacing decision, even if smaller.
            continue
        ET.SubElement(measure, 'vspacerUp').text = str(value)
        new_owned[str(m)] = value
    owned[key] = new_owned
    if tag is None:
        tag = ET.SubElement(score, 'metaTag', name=OWNER)
    tag.text = json.dumps(owned, sort_keys=True)
    files[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    # Exclusive creation prevents accidentally replacing an existing score.
    with destination.open('xb') as handle, zipfile.ZipFile(handle, 'w', zipfile.ZIP_DEFLATED) as archive:
        for member, content in files.items():
            archive.writestr(member, content)
    return dict(output_sha256=digest(destination.read_bytes()), applied_measures=sorted(map(int, new_owned)),
                preserved_manual_spacer_measures=manual, status='requires-rendered-review')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    plan = sub.add_parser('plan')
    plan.add_argument('score'); plan.add_argument('geometry'); plan.add_argument('report')
    plan.add_argument('--upper', type=int, required=True); plan.add_argument('--lower', type=int, required=True)
    plan.add_argument('--base', type=float, required=True, help='Preferred normal baseline distance in staff spaces')
    plan.add_argument('--clearance', type=float, default=.35)
    plan.add_argument('--reset-global-offset', action='store_true')
    apply = sub.add_parser('apply')
    apply.add_argument('score'); apply.add_argument('plan'); apply.add_argument('output')
    args = parser.parse_args()
    try:
        if args.command == 'plan':
            result = make_plan(args.score, args.geometry, args.upper, args.lower,
                               args.base, args.clearance, args.reset_global_offset)
            with Path(args.report).open('x') as handle:
                json.dump(result, handle, ensure_ascii=False, indent=2)
        else:
            result = apply_plan(args.score, json.loads(Path(args.plan).read_text()), args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
