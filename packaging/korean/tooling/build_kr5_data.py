"""Apply the KR5 data correction using the unmodified YAMPT topic tagger.

Requires the KR4 mod directory, a legally installed Morrowind.esm and the
yampt-journal-tagger adapter. Never writes to the source directories.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import tempfile

NAMES = {
    'p_restore_health_b': '싸구려 체력 회복',
    'p_restore_health_c': '저가 체력 회복',
    'p_restore_health_s': '일반 체력 회복 물약',
}
TAG = re.compile(r'@[^@#]*#')
EXTRA_FORMS = {'칼데라의 에보니 광산': '칼데라 에보니 광산', '에보니 광산': '칼데라 에보니 광산'}

def records(data):
    p = 0
    while p < len(data):
        tag, size, unknown, flags = struct.unpack_from('<4sIII', data, p)
        end = p + 16 + size
        if end > len(data): raise ValueError('Truncated TES3 record')
        yield tag, data[p+16:end], unknown, flags
        p = end
    if p != len(data): raise ValueError('Trailing TES3 bytes')

def fields(body):
    p = 0
    while p < len(body):
        tag, size = struct.unpack_from('<4sI', body, p)
        end = p + 8 + size
        if end > len(body): raise ValueError('Truncated TES3 subrecord')
        yield tag, body[p+8:end]
        p = end

def pack_fields(fs):
    return b''.join(struct.pack('<4sI', t, len(v)) + v for t, v in fs)

def pack_record(t, body, unknown, flags):
    return struct.pack('<4sIII', t, len(body), unknown, flags) + body

def visible(s):
    return TAG.sub(lambda m: m[0][1:-1].rstrip('\x7f'), s)

def run_tagger(exe, topics, segments):
    with tempfile.TemporaryDirectory(prefix='kr5-yampt-') as tmp:
        src, dst = Path(tmp)/'input.bin', Path(tmp)/'output.bin'
        with src.open('wb') as f:
            for values in [topics]:
                f.write(struct.pack('<I', len(values)))
                for s in values:
                    raw=s.encode('utf-8')
                    f.write(struct.pack('<I', len(raw))); f.write(raw)
            f.write(struct.pack('<I',len(EXTRA_FORMS)))
            for phrase,topic in EXTRA_FORMS.items():
                for s in [phrase,topic]:
                    raw=s.encode('utf-8');f.write(struct.pack('<I',len(raw)));f.write(raw)
            f.write(struct.pack('<I',len(segments)))
            for s in segments:
                raw=s.encode('utf-8');f.write(struct.pack('<I',len(raw)));f.write(raw)
        subprocess.run([str(exe), str(src), str(dst)], check=True)
        data=dst.read_bytes()
        count=struct.unpack_from('<I', data)[0]
        if count != len(segments): raise ValueError('YAMPT result count mismatch')
        p=4; out=[]
        for _ in range(count):
            n=struct.unpack_from('<I',data,p)[0]; p+=4
            out.append(data[p:p+n].decode('utf-8')); p+=n
        if p != len(data): raise ValueError('YAMPT trailing output')
        return out

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-mod',type=Path,required=True)
    ap.add_argument('--master',type=Path,required=True)
    ap.add_argument('--tagger',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--reviewed-info-ids',type=Path,required=True,help='JSON list of INFO IDs approved after actual-engine parser verification')
    a=ap.parse_args()
    approved=set(json.loads(a.reviewed_info_ids.read_text('utf-8')))
    approved.update(['10356287601274130444','2531617332095525831','610522350507519773'])
    if a.output.exists(): raise ValueError('Output must be a new directory')
    source=a.source_mod/'Morrowind_Korean_ReTranslation.esp'
    original=source.read_bytes()
    rs=list(records(original))
    forms=dict(line.split('\t',1) for line in (a.source_mod/'Morrowind_Korean_ReTranslation.top').read_text('utf-8-sig').splitlines() if '\t' in line)
    for phrase,topic in EXTRA_FORMS.items():
        if phrase in forms and forms[phrase]!=topic: raise ValueError('Conflicting phrase alias')
        forms[phrase]=topic
    keywords=dict(line.split('\t',1) for line in (a.source_mod/'Morrowind_Korean_ReTranslation.mrk').read_text('utf-8-sig').splitlines() if '\t' in line)
    topics=[]
    for tag,body,_,_ in rs:
        if tag != b'DIAL': continue
        fs=dict(fields(body))
        if fs.get(b'DATA') != b'\0': continue
        name=fs[b'NAME'].rstrip(b'\0').decode('utf-8')
        # Avoid ambiguous one-character matches and aliases that redirect a canonical name.
        if len(name)<2 or forms.get(name,name).lower()!=name.lower(): continue
        # Native implicit linking already covers canonical names unless .mrk replaces
        # the search phrase. Tag only that demonstrable gap instead of retagging everything.
        if keywords.get(name,name)==name: continue
        topics.append(name)
    topics=sorted(set(topics))
    entries=[]; segments=[]; kind=None
    for i,(tag,body,_,_) in enumerate(rs):
        fs=dict(fields(body))
        if tag==b'DIAL': kind=fs.get(b'DATA',b'\xff')[0]
        if tag!=b'INFO' or kind!=4 or b'NAME' not in fs: continue
        old=fs[b'NAME'].rstrip(b'\0').decode('utf-8')
        chunks=[]; pos=0
        for match in TAG.finditer(old):
            if pos<match.start():
                chunks.append(('text',len(segments),pos>0)); segments.append(('x' if pos>0 else '')+old[pos:match.start()])
            chunks.append(('tag',match[0],False)); pos=match.end()
        if pos<len(old):
            chunks.append(('text',len(segments),pos>0)); segments.append(('x' if pos>0 else '')+old[pos:])
        entries.append((i,old,chunks,fs.get(b'INAM',b'').rstrip(b'\0').decode('ascii')))
    results=run_tagger(a.tagger.resolve(),topics,segments)
    changes=[]; inserted=0
    for i,old,chunks,info in entries:
        if info not in approved: continue
        new=''.join(val if typ=='tag' else results[val][1 if prefix else 0:] for typ,val,prefix in chunks)
        if visible(old)!=visible(new): raise ValueError('Displayed journal text changed')
        if old==new: continue
        old_tags=TAG.findall(old); new_tags=TAG.findall(new)
        it=iter(new_tags)
        if not all(any(x==t for x in it) for t in old_tags): raise ValueError('Existing tag changed')
        for match in TAG.finditer(new):
            raw=match[0][1:-1]; shown=raw.rstrip('\x7f')
            key=shown+'*'*(len(raw)-len(shown))
            # Existing links may legitimately refer to topics provided by other plugins.
            if match[0] not in old_tags and forms.get(key,key).lower()!=shown.lower() and EXTRA_FORMS.get(key)!=forms.get(key):
                raise ValueError('New tag redirects to another topic')
        tag,body,unknown,flags=rs[i]
        rs[i]=(tag,pack_fields([(t,new.encode('utf-8')+b'\0' if t==b'NAME' else v) for t,v in fields(body)]),unknown,flags)
        added=len(new_tags)-len(old_tags); inserted+=added
        changes.append({'info':info,'added_links':added,'before':old,'after':new})
    master={}
    for rec in records(a.master.read_bytes()):
        if rec[0]!=b'ALCH': continue
        fs=dict(fields(rec[1])); key=fs[b'NAME'].rstrip(b'\0').decode('ascii').lower()
        if key in NAMES: master[key]=rec
    if set(master)!=set(NAMES): raise ValueError('Master is missing reported potions')
    existing={dict(fields(b))[b'NAME'].rstrip(b'\0').decode('ascii').lower() for t,b,_,_ in rs if t==b'ALCH'}
    if existing.intersection(NAMES): raise ValueError('Source already overrides a potion; review before replacing')
    added_records=[]
    for key,name in NAMES.items():
        tag,body,unknown,flags=master[key]
        changed=pack_fields([(t,name.encode('utf-8')+b'\0' if t==b'FNAM' else v) for t,v in fields(body)])
        # Every gameplay field remains byte-identical to the original master.
        assert [(t,v) for t,v in fields(changed) if t!=b'FNAM']==[(t,v) for t,v in fields(body) if t!=b'FNAM']
        added_records.append((tag,changed,unknown,flags))
    index=next(i for i,r in enumerate(rs) if r[0]==b'DIAL')
    rs[index:index]=added_records
    tag,body,unknown,flags=rs[0]
    if tag!=b'TES3': raise ValueError('Missing TES3 header')
    fs=[]
    for t,v in fields(body):
        if t==b'HEDR':
            v=bytearray(v); struct.pack_into('<I',v,296,len(rs)-1); v=bytes(v)
        fs.append((t,v))
    rs[0]=(tag,pack_fields(fs),unknown,flags)
    output=b''.join(pack_record(*r) for r in rs)
    list(records(output))
    shutil.copytree(a.source_mod,a.output)
    (a.output/source.name).write_bytes(output)
    top_path=a.output/'Morrowind_Korean_ReTranslation.top'
    top=top_path.read_bytes()
    if not top.endswith(b'\n'): top+=b'\r\n'
    top+=''.join(f'{phrase}\t{topic}\r\n' for phrase,topic in EXTRA_FORMS.items()).encode('utf-8')
    top_path.write_bytes(top)
    (a.output/'Morrowind_Korean_ReTranslation.jrn').write_text(''.join(f'{phrase}\t{topic}\r\n' for phrase,topic in EXTRA_FORMS.items()),'utf-8-sig')
    report={'source_sha256':hashlib.sha256(original).hexdigest(),'output_sha256':hashlib.sha256(output).hexdigest(),'journal_entries_scanned':len(entries),'journal_entries_changed':len(changes),'new_explicit_links':inserted,'potions':NAMES,'added_topic_forms':EXTRA_FORMS,'visible_text_unchanged':True,'existing_tags_preserved':True,'potion_gameplay_fields_unchanged':True,'journal_changes':changes}
    (a.output.parent/'kr5-data-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='journal_changes'},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
