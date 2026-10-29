import QtQuick
import MuseScore 3.0
import FileIO 3.0

MuseScore {
    title: "HarpScore Geometry"
    version: "4.7"
    description: "Read current renderer positions for the open score. Does not change music or export media."
    categoryCode: "composing-arranging-tools"
    // Output beside the installed plugin; no machine-specific path.
    function outputPath() {
        var path = decodeURIComponent(Qt.resolvedUrl("renderer-geometry.json").toString().replace(/^file:\/\//, ""));
        if (/^\/[A-Za-z]:\//.test(path)) path = path.slice(1);
        return path;
    }
    FileIO { id: resultFile; source: outputPath() }
    function box(el) {
        if (!el) return null;
        var p=el.pagePos, b=el.bbox;
        return {type:el.type, x:p.x,y:p.y,bx:b.x,by:b.y,w:b.width,h:b.height};
    }
    onRun: {
        
        var output={schemaVersion:1,coordinateUnits:"staff-space",rows:[],spanners:[],allTies:[],barlines:[],otherSpanners:[],summary:null,error:null};
        var tieList=[];
        try {
            if (!curScore) throw new Error("No open score");
            output.scoreName=curScore.scoreName;
            console.log("HARPSCORE_GEOM_BEGIN "+curScore.scoreName);
            var measureNo=0,systems=[],pages=[],count=0;
            for(var m=curScore.firstMeasure;m;m=m.nextMeasure){
                var system=m.parent,page=system?system.parent:null,si=-1,pi=-1;
                for(var k=0;k<systems.length;k++)if(system&&system.is(systems[k]))si=k;
                if(si<0){si=systems.length;systems.push(system);}
                for(var k=0;k<pages.length;k++)if(page&&page.is(pages[k]))pi=k;
                if(pi<0){pi=pages.length;pages.push(page);}
                for(var seg of m.segments){
                    var row={tick:seg.fraction.ticks,measure:measureNo,system:si,page:pi,measureBox:box(m),systemBox:box(system),events:[],annotations:[]};
                    for(var track=0;track<curScore.ntracks;track++){
                        var e=seg.elementAt(track);
                        if(e && e.type===Element.BAR_LINE) output.barlines.push({track:track,tick:seg.fraction.ticks,measure:measureNo,system:si,page:pi,visible:e.visible,box:box(e)});
                        if(e&&(e.type===Element.CHORD||e.type===Element.REST)){
                            var ev={track:track,box:box(e),notes:[],graces:[]};
                            if(e.type===Element.CHORD)for(var n of e.notes){
                                ev.notes.push({pitch:n.pitch,dead:n.dead,visible:n.visible,box:box(n)});
                                if(n.tieForward){
                                    var tf=n.tieForward,te=tf.endElement;
                                    output.allTies.push({track:track,startTick:n.fraction.ticks,endTick:te?te.fraction.ticks:null,startPitch:n.pitch,endPitch:te?te.pitch:null,visible:tf.visible});
                                }
                                if(n.tieForward&&n.tieForward.visible){
                                    var known=false;for(var t of tieList)if(t.is(n.tieForward))known=true;
                                    if(!known)tieList.push(n.tieForward);
                                }
                            }
                            if(e.type===Element.CHORD)for(var g of e.graceNotes){
                                var gr={box:box(g),notes:[]};
                                for(var gn of g.notes)gr.notes.push({pitch:gn.pitch,dead:gn.dead,visible:gn.visible,box:box(gn)});
                                ev.graces.push(gr);
                            }
                            ev.articulations=[];
                            if(e.articulations)for(var ar of e.articulations)ev.articulations.push({box:box(ar),visible:ar.visible,ox:ar.offsetX,oy:ar.offsetY});
                            row.events.push(ev);
                        }
                    }
                    for(var a of seg.annotations)if(a.type===Element.STAFF_TEXT||a.type===Element.DYNAMIC)row.annotations.push({track:a.track,type:a.type,text:a.text,size:a.fontSize,visible:a.visible,box:box(a),ox:a.offsetX,oy:a.offsetY});
                    if(row.events.length||row.annotations.length){output.rows.push(row);count++;}
                }
                measureNo++;
                if(measureNo>1000)throw new Error("measure overflow");
            }
            for(var ls of curScore.spanners)if(ls.visible && ls.type!==Element.SLUR && ls.type!==Element.TIE){
                var lr={type:ls.type,track:ls.track,visible:ls.visible,segments:[]};
                try {lr.startTick=ls.fraction.ticks;} catch(ignore){}
                try {lr.startText=ls.beginText;} catch(ignore){}
                for(var lg of ls.spannerSegments){
                    var li=-1;for(var j=0;j<systems.length;j++)if(lg.parent&&lg.parent.is(systems[j]))li=j;
                    lr.segments.push({box:box(lg),system:li,offsetX:lg.offsetX,offsetY:lg.offsetY});
                }
                output.otherSpanners.push(lr);
            }
            var allSpanners=[];
            for(var sp of curScore.spanners)if(sp.type===Element.SLUR && sp.visible)allSpanners.push(sp);
            for(var tie of tieList)allSpanners.push(tie);
            for(var sp of allSpanners){
                var sr={type:sp.type,kind:sp.type===Element.SLUR?"Slur":"Tie",track:sp.track,up:sp.up,visible:sp.visible,autoplace:sp.autoplace,startTick:sp.startElement.fraction.ticks,endTick:sp.endElement.fraction.ticks,startBox:box(sp.startElement),endBox:box(sp.endElement),startPitch:sp.startElement.type===Element.NOTE?sp.startElement.pitch:null,segments:[]};
                for(var sg of sp.spannerSegments){
                    var sy=-1;
                    for(var j=0;j<systems.length;j++)if(sg.parent && sg.parent.is(systems[j]))sy=j;
                    sr.segments.push({box:box(sg),system:sy,autoplace:sg.autoplace,up:sg.up,offsetX:sg.offsetX,offsetY:sg.offsetY,pos2:{x:sg.pos2.x,y:sg.pos2.y},o1:{x:sg.slurUoff1.x,y:sg.slurUoff1.y},o2:{x:sg.slurUoff2.x,y:sg.slurUoff2.y},o3:{x:sg.slurUoff3.x,y:sg.slurUoff3.y},o4:{x:sg.slurUoff4.x,y:sg.slurUoff4.y}});
                }
                output.spanners.push(sr);
            }
            output.summary={rows:count,measures:measureNo,systems:systems.length,pages:pages.length,spanners:output.spanners.length};
        } catch(e) {output.error=String(e);console.log("HARPSCORE_GEOM_ERROR "+e);}
        if (!resultFile.write(JSON.stringify(output))) console.log("HARPSCORE_GEOM_ERROR could not write output beside plugin");
        quit();
    }
}
