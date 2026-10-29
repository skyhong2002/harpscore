"""Physical double-stop candidates for a standard C 16-hole solo-tuned harp.

Derived from Suzuki's SCX-64 notation chart, not Richter tuning. This checks
reed selection, not a performer's tongue-blocking skill or preferred fingering.
"""
from itertools import product

SOURCE='https://csj-concierge.com/suzukimusic/uploads/products_pdf/13/5bee70fd289e213.pdf'
BLOW=[48+12*(i//4)+[0,4,7,12][i%4] for i in range(16)]
DRAW=[48+12*(i//4)+[2,5,9,11][i%4] for i in range(16)]

def double_stop_options(pitches):
    """Return actual two-hole pairs with one breath and one slide position.

    The opening spans at most five holes. Non-adjacent pairs require blocking
    every interior hole; merely covering the full span would add other notes.
    """
    if len(pitches)!=2 or pitches[0]==pitches[1]:return []
    options=[]
    for direction,chart in [('blow',BLOW),('draw',DRAW)]:
        for slide in [0,1]:
            values=[v+slide for v in chart]
            # Suzuki's highest draw with the lever pressed is D7, not C7.
            if direction=='draw' and slide:values[-1]=98
            holes=[[i+1 for i,v in enumerate(values)if v==p]for p in pitches]
            for pair in product(*holes):
                low,high=sorted(pair)
                if low==high or high-low>4:continue
                options.append({'direction':direction,'slide':'in'if slide else 'out',
                                'holes':list(pair),'blocked_holes':list(range(low+1,high))})
    return sorted(options,key=lambda o:(len(o['blocked_holes']),o['slide']=='in',o['holes']))
