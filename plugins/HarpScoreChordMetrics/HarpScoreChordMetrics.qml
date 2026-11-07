import QtQuick
import MuseScore 3.0
import FileIO 3.0

MuseScore {
    title: "HarpScore Chord Metrics"
    version: "1.0"
    description: "Read native text bounds from the open chord measurement probe. Does not edit scores or export media."
    categoryCode: "composing-arranging-tools"
    function localPath(name) {
        var path = decodeURIComponent(Qt.resolvedUrl(name).toString().replace(/^file:\/\//, ""));
        return /^\/[A-Za-z]:\//.test(path) ? path.slice(1) : path;
    }
    FileIO { id: requestFile; source: localPath("chord-metrics-request.json") }
    FileIO { id: resultFile; source: localPath("chord-metrics.json") }
    function plain(text) { return text.replace(/<[^>]*>/g, ""); }
    onRun: {
        var result = {schemaVersion: 1, measurements: [], error: null,
            environment: {application: Qt.application.name, version: Qt.application.version,
                platform: Qt.platform.os, backend: "native StaffText.bbox", units: "em"}};
        try {
            var request = JSON.parse(requestFile.read());
            if (request.schemaVersion !== 1 || !request.score_sha256 || !Array.isArray(request.queries))
                throw new Error("Invalid chord metrics request");
            result.request = request;
            if (!curScore || curScore.metaTag("harpscoreChordMetricsProbe") !== request.probe_id)
                throw new Error("Open the probe belonging to this request first");
            result.probe_id = request.probe_id;
            var families = Qt.fontFamilies(), measures = [];
            for (var m = curScore.firstMeasure; m; m = m.nextMeasure) measures.push(m);
            for (var query of request.queries) {
                if (families.indexOf(query.family) < 0)
                    throw new Error("Font is not installed: " + query.family);
                var found = [];
                for (var segment of measures[query.measure - 1].segments)
                    for (var a of segment.annotations)
                        if (a.type === Element.STAFF_TEXT && a.visible
                                && a.track === (query.staff - 1) * 4 + query.voice
                                && plain(a.text) === query.text
                                && a.fontFace === query.family
                                && Math.abs(a.fontSize - query.size) < .001
                                && Math.abs(a.offsetX - query.x) < .001
                                && Math.abs(a.offsetY - query.y) < .001) found.push(a);
                if (!found.length) throw new Error("Missing native sample: " + query.key);
                var bounds = found[0].bbox;
                if (!(bounds.width > 0)) throw new Error("Empty native text bounds: " + query.key);
                for (var duplicate of found)
                    if (Math.abs(duplicate.bbox.width - bounds.width) > .001)
                        throw new Error("Ambiguous native samples: " + query.key);
                var scale = request.spatium_pt / query.size_pt;
                result.measurements.push({key: query.key, leftEm: bounds.x * scale,
                    rightEm: (bounds.x + bounds.width) * scale});
            }
        } catch (error) { result.error = String(error); }
        if (!resultFile.write(JSON.stringify(result, null, 2)))
            console.log("HARPSCORE_CHORD_METRICS_ERROR: cannot write beside plugin");
        else console.log("HARPSCORE_CHORD_METRICS: " + (result.error || result.measurements.length + " runs measured"));
        quit();
    }
}
