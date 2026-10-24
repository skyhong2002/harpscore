#!/usr/bin/env python3
"""Inventory visible renderer curve segments for manual engraving review.

Controls and bounding boxes identify risks, never prove the curve's shape.
This reader makes no score edits and deliberately does not recommend offsets.
"""
import argparse
import hashlib
import json
import math


def inventory(data, short_span=10, control_ratio=.1):
    if data.get('error'):
        raise ValueError('renderer snapshot has an error')
    result = []
    for index, curve in enumerate(data['spanners']):
        if curve.get('kind') not in ('Tie', 'Slur') or not curve.get('visible'):
            continue
        for segment_index, segment in enumerate(curve['segments']):
            width = segment['box']['w']
            if not math.isfinite(width) or width <= 0:
                raise ValueError('curve segment requires a positive finite width')
            controls = [segment.get(k, {}).get('y', 0) for k in ('o2', 'o3')]
            ratio = max(abs(v) for v in controls) / width
            reasons = []
            if width < short_span and ratio >= control_ratio:
                reasons.append('short-span-large-control-offset')
            if segment_index > 0:
                reasons.append('continuation-requires-independent-inspection')
            if not segment.get('up', curve.get('up')):
                reasons.append('not-upper-direction')
            result.append(dict(curve_index=index, segment_index=segment_index,
                               kind=curve['kind'], track=curve['track'],
                               start_tick=curve['startTick'], end_tick=curve['endTick'],
                               start_pitch=curve.get('startPitch'),
                               system=segment['system'], width=width,
                               control_offset_ratio=ratio, reasons=reasons,
                               requires_visual_inspection=True))
    return dict(segments=result, segment_count=len(result),
                priority_count=sum(bool(s['reasons']) for s in result),
                visual_acceptance=False,
                proof_boundary='All visible segments still require ink inspection. '
                'No risk flag does not mean no bowl, collision or excessive rise. '
                'Hidden playback ties must be preserved independently.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('geometry')
    p.add_argument('report')
    p.add_argument('--short-span', type=float, default=10)
    p.add_argument('--control-ratio', type=float, default=.1)
    args = p.parse_args()
    if args.short_span <= 0 or args.control_ratio <= 0:
        p.error('thresholds must be positive')
    with open(args.geometry, 'rb') as source:
        raw = source.read()
    report = inventory(json.loads(raw), args.short_span, args.control_ratio)
    report['geometry_sha256'] = hashlib.sha256(raw).hexdigest()
    report['parameters'] = vars(args)
    with open(args.report, 'w') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
    print(f"{report['segment_count']} visible segments; "
          f"{report['priority_count']} priority reviews; visual acceptance pending")


if __name__ == '__main__':
    main()
