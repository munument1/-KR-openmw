"""Portable regression fixtures for the actual OpenMW parser and sidecar loader."""
from pathlib import Path
import sys,tempfile
from verify_kr5_links import inspect

runner=Path(sys.argv[1]).resolve()
mine='칼데라 에보니 광산'
guild='마법사 길드'
ore='에보니'
with tempfile.TemporaryDirectory(prefix='openmw-journal-test-') as tmp:
    mod=Path(tmp)
    for newline in ['\n','\r\n']:
        for extension,text in {
            'cel':'',
            'top':f'칼데라의 에보니 광산\t{mine}{newline}',
            'mrk':f'{guild}\t마법사 길드에서{newline}',
            'jrn':f'칼데라의 에보니 광산\t{mine}{newline}에보니 광산\t{mine}{newline}',
        }.items():
            (mod/f'Morrowind_Korean_ReTranslation.{extension}').write_bytes(b'\xef\xbb\xbf'+text.encode('utf-8'))
        entries=[('mine','칼데라의 에보니 광산을 방문했다.'),('guild','마법사 길드에 들렀다.'),('explicit','@칼데라의 에보니 광산#을 방문했다.')]
        before=inspect(runner,mod,entries,[mine,guild],False)
        after=inspect(runner,mod,entries,[mine,guild],True)
        assert before['mine']['targets']==[]
        assert before['guild']['targets']==[]
        assert after['mine']['targets']==[mine]
        assert after['guild']['targets']==[guild]
        assert after['explicit']['targets']==[mine]
        assert before['explicit']['text']==after['explicit']['text']=='칼데라의 에보니 광산을 방문했다.'
        unknown=inspect(runner,mod,entries,[],True)
        assert all(not x['targets'] for x in unknown.values())
        overlapping=inspect(runner,mod,entries,[mine,ore,guild],True)
        assert overlapping['mine']['targets']==[mine]
        only_ore=inspect(runner,mod,entries,[ore],True)
        assert mine not in only_ore['mine']['targets']
        assert only_ore['explicit']['targets']==[]
print('PASS: canonical names, legacy saved text, reviewed aliases, overlap resolution, unknown-topic gating, UTF-8 BOM, LF and CRLF')
