#!/usr/bin/env python3
"""Measure Jianpu articulation centres in a live renderer geometry snapshot.

Read-only proposals, not an automatic engraving pass. Element type IDs must be
confirmed against the installed renderer. Excludes ornaments and ambiguous or
missing overlays; it never borrows a numeral from another event or staff.
"""
import argparse
import hashlib
import html
import json
import re


def plain(text):
    return html.unescape(re.sub(r"<[^>]*>", "", text)).strip()


def bounds(box):
    left = box["x"] + box.get("bx", 0)
    return left, left + box["w"]


def measure(data, articulation_type, minimum_size=9, tolerance=.02):
    pairs, skipped = [], []
    # MuseScore can emit several segment types at one musical tick. Text and
    # its chord need not be in the same segment row. Join only exact musical
    # locations; never substitute text from a neighbouring onset or staff.
    annotations = {}
    for row in data["rows"]:
        location = tuple(row[k] for k in ("page", "system", "measure", "tick"))
        annotations.setdefault(location, []).extend(row["annotations"])
    for row in data["rows"]:
        location = tuple(row[k] for k in ("page", "system", "measure", "tick"))
        for event in row["events"]:
            articulations = [a for a in event.get("articulations", [])
                             if a.get("visible") and a["box"]["type"] == articulation_type]
            if not articulations:
                continue
            key = dict(page=row["page"] + 1, system=row["system"],
                       measure=row["measure"] + 1, tick=row["tick"], track=event["track"])
            digits = [a for a in annotations[location]
                      if a["track"] == event["track"] and a.get("size", 0) >= minimum_size
                      and plain(a["text"]) in tuple("1234567xX")]
            # A non-octave double stop has a shared horizontal centre. Multiple
            # horizontally separated digits indicate an ambiguous overlay.
            centres = [sum(bounds(a["box"])) / 2 for a in digits]
            if not digits or max(centres) - min(centres) > .35:
                skipped.append(dict(**key, reason="missing-or-ambiguous-event-overlay",
                                    articulation_count=len(articulations)))
                continue
            left = min(bounds(a["box"])[0] for a in digits)
            right = max(bounds(a["box"])[1] for a in digits)
            target = (left + right) / 2
            for index, articulation in enumerate(articulations):
                al, ar = bounds(articulation["box"])
                error = (al + ar) / 2 - target
                pairs.append(dict(**key, articulation_index=index,
                                  glyphs=[plain(a["text"]) for a in digits],
                                  numeral_bounds=[left, right], articulation_bounds=[al, ar],
                                  centre_error=error, proposed_delta_x=-error,
                                  needs_review=abs(error) > tolerance))
    return dict(pairs=pairs, skipped=skipped, pair_count=len(pairs),
                review_count=sum(p["needs_review"] for p in pairs),
                visual_acceptance=False,
                proof_boundary="Renderer bounding-box measurements only. Verify visible ink, "
                "vertical clearance and event identity in MuseScore after any revision.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geometry")
    parser.add_argument("report")
    parser.add_argument("--articulation-type", type=int, required=True)
    parser.add_argument("--minimum-numeral-size", type=float, default=9)
    parser.add_argument("--tolerance", type=float, default=.02)
    args = parser.parse_args()
    with open(args.geometry, "rb") as source:
        raw = source.read()
    data = json.loads(raw)
    if data.get("error"):
        parser.error("renderer snapshot has an error")
    result = measure(data, args.articulation_type, args.minimum_numeral_size, args.tolerance)
    result["geometry_sha256"] = hashlib.sha256(raw).hexdigest()
    result["parameters"] = vars(args)
    with open(args.report, "w") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
    print(f"{result['pair_count']} measured; {result['review_count']} candidates; "
          f"{len(result['skipped'])} unmatched events")


if __name__ == "__main__":
    main()
