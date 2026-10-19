const test=require('node:test'),assert=require('node:assert/strict');
const {makeBrief,prompt}=require('../web/brief.js');
const base={title:'原創練習',source:'原創素材',ensemble:'duet',level:'beginner-2-months',notation:['jianpu'],pdf:false,piano:true};
test('duet has combined harp edition and optional piano master, no individual parts',()=>{const b=makeBrief(base);assert.deepEqual(b.editions,['combined-harmonicas','with-piano-master']);assert.equal(b.pdf,false);assert.match(prompt(b),/不另拆個別口琴分部/)});
test('quintet ignores piano option',()=>assert.deepEqual(makeBrief({...base,ensemble:'quintet'}).editions,['combined-harmonicas']));
test('quartet uses two chromatics, bass and chord without extra piano',()=>{const b=makeBrief({...base,ensemble:'quartet'});assert.deepEqual(b.editions,['combined-harmonicas']);assert.match(prompt(b),/兩部半音階、DB H.、Chord/)});
test('reject incomplete and unsupported requests',()=>{assert.throws(()=>makeBrief({...base,source:''}));assert.throws(()=>makeBrief({...base,notation:[]}));assert.throws(()=>makeBrief({...base,ensemble:'trio'}))});
test('user contents preserved without execution',()=>{const b=makeBrief({...base,title:'<script>test</script>',notes:'保留 332'});assert.equal(b.title,'<script>test</script>');assert.match(prompt(b),/保留 332/)});
