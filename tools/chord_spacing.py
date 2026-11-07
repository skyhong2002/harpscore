#!/usr/bin/env python3
"""Space Jianpu StaffText chord labels using native renderer bounds, without changing music.

Standard library only. Prepare a font request, run HarpScore Chord Metrics in
MuseScore, then apply the returned measurements to a new score file.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

SCHEMA = 1
ACC = r"(?:♭{1,2}|♯{1,2}|b{1,2}|#{1,2})"
LABEL = re.compile(r"^([A-G])(" + ACC + r")?([^/]*)(?:/([A-G])(" + ACC + r")?)?$")
SUFFIX = re.compile(r"(?:maj|min|dim|aug|sus|add|m|M|Δ|ø|°|\+|-|\d|[♭♯b#()]|\.)*")
OVERLAY_FIELDS = {"eid", "autoplace", "visible", "family", "size", "sizeIsSpatiumDependent",
                  "fontStyle", "style", "frameType", "align", "offset", "placement",
                  "color", "z", "minDistance", "text"}


def finite(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Non-finite font or spacing value")
    return value


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_score(path):
    path = Path(path)
    raw = path.read_bytes()
    if path.suffix.lower() == ".mscx":
        return raw, None, None, ET.fromstring(raw)
    if path.suffix.lower() != ".mscz":
        raise ValueError("Expected .mscx or .mscz")
    with zipfile.ZipFile(path) as archive:
        files = {n: archive.read(n) for n in archive.namelist()}
    names = [n for n in files if n.endswith(".mscx") and "/" not in n]
    if len(names) != 1:
        raise ValueError("Expected one root MSCX")
    return raw, files, names[0], ET.fromstring(files[names[0]])


def plain(element):
    return "".join(element.itertext()) if element is not None else ""


def chunks(label):
    """Preserve chord spelling; distinguish root/bass accidentals from suffixes."""
    match = LABEL.fullmatch(label)
    if not match or not SUFFIX.fullmatch(match[3]):
        return None
    root, accidental, suffix, bass, bass_accidental = match.groups()
    if suffix.startswith(("b", "#", "♭", "♯")):
        return None
    depth = 0
    for char in suffix:
        depth += (char == "(") - (char == ")")
        if depth < 0:
            return None
    if depth:
        return None
    if not accidental and not bass_accidental:
        return None
    result = [(root, "main")]
    if accidental:
        result.append((accidental, "accidental"))
    tail = suffix + ("/" + bass if bass else "")
    if tail:
        if result[-1][1] == "main":
            result[-1] = (result[-1][0] + tail, "main")
        else:
            result.append((tail, "main"))
    if bass_accidental:
        result.append((bass_accidental, "accidental"))
    return result


def style_for(root, files):
    style = root.find("Score/Style")
    if style is None and files and "score_style.mss" in files:
        style = ET.fromstring(files["score_style.mss"]).find("Style")
    return style if style is not None else ET.Element("Style")


def inventory(path, staves, font=None, accidental_font="Arial", gap_pt=.9):
    raw, files, _, root = read_score(path)
    style = style_for(root, files)
    spatium_pt = finite(style.findtext("spatium", "1.764")) * 72 / 25.4
    gap_pt = finite(gap_pt)
    if spatium_pt <= 0 or gap_pt <= 0 or not accidental_font.strip():
        raise ValueError("Positive spatium/gap and an accidental font are required")
    score_staves = root.findall("Score/Staff")
    definitions = root.findall("Score/Part/Staff")
    if definitions and len(definitions) != len(score_staves):
        raise ValueError("Staff definitions do not match the score staves")
    if not staves or any(s < 1 or s > len(score_staves) for s in staves):
        raise ValueError("Select existing one-based score staves with --staff")
    targets, skipped, queries = [], [], {}
    for si in sorted(set(staves)):
        for mi, measure in enumerate(score_staves[si - 1].findall("Measure")):
            for vi, voice in enumerate(measure.findall("voice")):
                for ti, element in enumerate(voice.findall("StaffText")):
                    label = plain(element.find("text"))
                    parts = chunks(label)
                    if parts is None:
                        # Detached accidentals and uncertain chord-like text are reported.
                        if re.search(r"[♭♯#]", label) or re.match(r"^[A-G]b", label):
                            skipped.append(dict(staff=si, measure=mi + 1, text=label,
                                                reason="not-a-complete-supported-chord"))
                        continue
                    location = dict(staff=si, measure=mi + 1, voice=vi, text_index=ti)
                    text = element.find("text")
                    if (element.findtext("autoplace", "1") != "0"
                            or element.findtext("visible", "1") == "0"
                            or any(child.tag not in OVERLAY_FIELDS for child in element)
                            or any(child.tag != "font" or set(child.attrib) != {"face"}
                                   or len(child)
                                   for child in text)
                            or element.findtext("fontStyle", style.findtext("staffTextFontStyle", "0")) != "0"
                            or element.findtext("style", "Staff") != "Staff"
                            or element.findtext("frameType", style.findtext("staffTextFrameType", "0")) != "0"
                            or (definitions and (
                                definitions[si - 1].findtext("small", "0") != "0"
                                or finite(definitions[si - 1].findtext("mag", "1")) != 1
                                or finite(definitions[si - 1].findtext("StaffType/mag", "1")) != 1))
                            or score_staves[si - 1].find(".//StaffTypeChange") is not None):
                        skipped.append(dict(**location, text=label,
                                            reason="requires-visible-manual-plain-font-overlay"))
                        continue
                    family = font or element.findtext("family")
                    if not family:
                        first_font = text.find("font")
                        family = (first_font.get("face") if first_font is not None else None)
                    family = family or style.findtext("staffTextFontFace", "Edwin")
                    size = finite(element.findtext("size", style.findtext("staffTextFontSize", "10")))
                    dependent = element.findtext("sizeIsSpatiumDependent",
                                                 style.findtext("staffTextFontSpatiumDependent", "1")) == "1"
                    if size <= 0:
                        raise ValueError("Non-positive font size")
                    # MuseScore's nominal reference spatium is 5 points.
                    size_pt = size * spatium_pt / 5 if dependent else size
                    offset = element.find("offset")
                    x, y = (finite(offset.get("x", 0)), finite(offset.get("y", 0))) if offset is not None else (0, 0)
                    members = []
                    for value, role in parts:
                        face = accidental_font if role == "accidental" else family
                        key = json.dumps([face, value, size_pt], ensure_ascii=False, separators=(",", ":"))
                        if key not in queries:
                            queries[key] = dict(key=key, family=face, text=value, size=size,
                                                size_pt=size_pt, staff=si, measure=mi + 1,
                                                voice=vi, x=x + len(members) * 5, y=y)
                        members.append(dict(key=key, family=face, text=value))
                    targets.append(dict(**location, text=label, size_pt=size_pt,
                                        x=x, y=y, members=members))
    selection = dict(staves=sorted(set(staves)), font=font,
                     accidental_font=accidental_font, gap_pt=gap_pt)
    probe_id = digest((digest(raw) + json.dumps(selection, sort_keys=True)).encode())
    return dict(schemaVersion=SCHEMA, score_sha256=digest(raw), probe_id=probe_id,
                selection=selection,
                spatium_pt=spatium_pt, targets=targets, skipped=skipped,
                queries=list(queries.values()))


def layout(target, measurements, spatium_pt, gap_pt):
    """Anchor the first run's origin; put clear ink gaps between subsequent runs."""
    placed, previous_right = [], None
    for member in target["members"]:
        metric = measurements[member["key"]]
        left = finite(metric["leftEm"]) * target["size_pt"] / spatium_pt
        right = finite(metric["rightEm"]) * target["size_pt"] / spatium_pt
        if right <= left:
            raise ValueError("Empty or inverted glyph ink bounds")
        x = target["x"] if previous_right is None else previous_right + gap_pt / spatium_pt - left
        placed.append(dict(member, x=x, ink_left=x + left, ink_right=x + right))
        previous_right = x + right
    return placed


def put(element, name, value):
    child = element.find(name)
    if child is None:
        child = ET.Element(name)
        text = element.find("text")
        element.insert(list(element).index(text) if text is not None else len(element), child)
    child.text = value


def write_candidate(path, request, output, measurements=None):
    raw, files, name, root = read_score(path)
    if request["score_sha256"] != digest(raw):
        raise ValueError("Score changed since prepare; prepare fresh measurements")
    selection = request["selection"]
    fresh = inventory(path, **selection)
    if fresh != request:
        raise ValueError("Request does not match the current score inventory")
    output = Path(output)
    if output.exists() or output.resolve() == Path(path).resolve():
        raise ValueError("Output must be a new file")
    if output.suffix.lower() != Path(path).suffix.lower():
        raise ValueError("Keep the input score format")
    staves = root.findall("Score/Staff")
    # Resolve every target before replacing any sibling; repeated labels stay distinct.
    edits = []
    for target in request["targets"]:
        voice = staves[target["staff"] - 1].findall("Measure")[target["measure"] - 1].findall("voice")[target["voice"]]
        element = voice.findall("StaffText")[target["text_index"]]
        placed = (layout(target, measurements, request["spatium_pt"], selection["gap_pt"])
                  if measurements is not None else
                  [dict(member, x=target["x"] + j * 5) for j, member in enumerate(target["members"])])
        edits.append((voice, element, placed, target))
    for voice, element, placed, target in edits:
        index = list(voice).index(element)
        for j, member in enumerate(placed):
            new = deepcopy(element)
            if j:
                for eid in new.findall("eid"):
                    new.remove(eid)  # MuseScore assigns valid native IDs on normal save.
            put(new, "family", member["family"])
            put(new, "align", "left,baseline")
            offset = new.find("offset")
            if offset is None:
                offset = ET.Element("offset")
                new.insert(list(new).index(new.find("text")), offset)
            offset.attrib = dict(x=f'{member["x"]:.8f}', y=f'{target["y"]:.8f}')
            text = new.find("text")
            text.clear()
            ET.SubElement(text, "font", dict(face=member["family"])).tail = member["text"]
            voice.insert(index + j, new)
        voice.remove(element)
    if measurements is None:
        ET.SubElement(root.find("Score"), "metaTag", name="harpscoreChordMetricsProbe").text = request["probe_id"]
    if not edits and measurements is not None:
        payload = raw
    else:
        payload = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    if files is None or (not edits and measurements is not None):
        output.write_bytes(payload)
    else:
        files[name] = payload
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for entry, data in files.items():
                archive.writestr(entry, data)
    return dict(changed_labels=len(edits), skipped=request["skipped"],
                source_sha256=digest(raw), output_sha256=digest(output.read_bytes()),
                visual_acceptance=False,
                proof_boundary="Text-only candidate. Save/reopen in MuseScore and inspect ink, "
                "neighboring rhythm, staves and page geometry; music and playback are not re-engraved.")


def apply(path, metrics, output):
    if metrics.get("error") or metrics.get("schemaVersion") != SCHEMA:
        raise ValueError("Font measurement failed or schema is unsupported")
    request = metrics["request"]
    if metrics.get("probe_id") != request["probe_id"]:
        raise ValueError("Renderer did not measure the requested probe")
    if metrics.get("environment", {}).get("backend") != "native StaffText.bbox":
        raise ValueError("Native MuseScore StaffText measurements are required")
    measurements = {m["key"]: m for m in metrics["measurements"]}
    if len(measurements) != len(metrics["measurements"]):
        raise ValueError("Duplicate font measurements")
    if set(measurements) != {q["key"] for q in request["queries"]}:
        raise ValueError("Missing or unrelated font measurements")
    result = write_candidate(path, request, output, measurements)
    result["measurement_environment"] = metrics.get("environment")
    return result


def new_destinations(inputs, outputs):
    """Check every CLI destination before writing either member of an output pair."""
    sources = {Path(p).resolve() for p in inputs}
    destinations = [Path(p).resolve() for p in outputs]
    if len(set(destinations)) != len(destinations) or sources.intersection(destinations):
        raise ValueError("Input and output paths must all be distinct")
    if any(p.exists() for p in destinations):
        raise ValueError("Outputs must be new files")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Inventory chord labels and write a native measurement probe")
    prepare.add_argument("score")
    prepare.add_argument("request")
    prepare.add_argument("--probe", required=True, help="New disposable score for native text measurement")
    prepare.add_argument("--staff", dest="staves", type=int, action="append", required=True)
    prepare.add_argument("--font", help="Root/suffix font; otherwise preserve the label's main font")
    prepare.add_argument("--accidental-font", default="Arial")
    prepare.add_argument("--gap-pt", type=float, default=.9)
    change = commands.add_parser("apply", help="Write a new score using measured ink bounds")
    change.add_argument("score")
    change.add_argument("metrics")
    change.add_argument("output")
    change.add_argument("--report", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            new_destinations([args.score], [args.request, args.probe])
            result = inventory(args.score, args.staves, args.font, args.accidental_font, args.gap_pt)
            write_candidate(args.score, result, args.probe)
            Path(args.request).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            print(f'{len(result["targets"])} labels; {len(result["queries"])} unique font runs; {len(result["skipped"])} skipped')
        else:
            new_destinations([args.score, args.metrics], [args.output, args.report])
            result = apply(args.score, json.loads(Path(args.metrics).read_text()), args.output)
            Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            print(f'{result["changed_labels"]} labels spaced; candidate needs MuseScore save/reopen and visual inspection')
    except (ValueError, KeyError, OSError, ET.ParseError, zipfile.BadZipFile) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
