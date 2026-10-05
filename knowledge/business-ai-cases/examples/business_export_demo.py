"""Independent in-memory CSV export fixture; not Django or a durable worker."""
import csv
import hashlib
import io
import json
from dataclasses import dataclass
from threading import RLock
from uuid import uuid4


@dataclass(frozen=True)
class Principal:
    tenant: str
    user: str
    can_export: bool
    objects: frozenset


def identifier(value):
    if not isinstance(value, str) or not value or len(value) > 100:
        raise ValueError('invalid identifier')
    return value


def text_cell(value):
    """Limited spreadsheet formula mitigation; CSV quoting alone is insufficient."""
    if not isinstance(value, str):
        raise ValueError('text expected')
    probe = value.lstrip(' \t\r\n')
    if probe.startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')):
        return "'" + value
    return value


class Exports:
    def __init__(self):
        self._jobs = {}
        self._requests = {}
        self._lock = RLock()

    @staticmethod
    def _principal(p):
        if not isinstance(p, Principal) or type(p.can_export) is not bool or not isinstance(p.objects, frozenset):
            raise ValueError('trusted principal fixture required')
        identifier(p.tenant); identifier(p.user)
        for obj in p.objects: identifier(obj)
        if not p.can_export: raise PermissionError('export permission required')

    @staticmethod
    def _clock(now):
        if type(now) is not int or now < 0: raise ValueError('nonnegative integer clock required')

    def create(self, p, request, version, object_ids, source_rows, now, ttl=60):
        self._principal(p); self._clock(now)
        identifier(request); identifier(version)
        if type(ttl) is not int or not 1 <= ttl <= 3600: raise ValueError('invalid ttl')
        if not isinstance(object_ids, (list, tuple)) or not 1 <= len(object_ids) <= 100:
            raise ValueError('one to 100 requested objects')
        wanted = frozenset(identifier(x) for x in object_ids)
        if len(wanted) != len(object_ids): raise ValueError('duplicate requested objects')
        if not wanted <= p.objects: raise PermissionError('object scope denied')
        # Scope filtering happens before projecting public columns.
        selected = []
        for row in source_rows:
            if row['tenant'] != p.tenant or row['object_id'] not in wanted: continue
            obj = identifier(row['object_id'])
            name, count = row['name'], row['count']
            if not isinstance(name, str) or len(name) > 1000 or type(count) is not int or not 0 <= count <= 10**9:
                raise ValueError('invalid visible row')
            selected.append((obj, name, count))
        selected.sort()
        if len(selected) != len(wanted) or frozenset(r[0] for r in selected) != wanted:
            raise ValueError('missing or duplicate source rows')
        snapshot = tuple(selected)  # strings and integers; no retained mutable row reference
        fingerprint = hashlib.sha256(json.dumps([version, snapshot, ttl], ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        identity = (p.tenant, p.user, request)
        with self._lock:
            if identity in self._requests:
                job_id = self._requests[identity]
                if self._jobs[job_id]['fingerprint'] != fingerprint: raise ValueError('request conflict')
                return job_id
            job_id = str(uuid4())
            self._jobs[job_id] = dict(tenant=p.tenant, user=p.user, objects=wanted,
                snapshot=snapshot, version=version, fingerprint=fingerprint,
                created_at=now, expires_at=now+ttl, ready_at=None,
                state='queued', content=None, sha256=None)
            self._requests[identity] = job_id
            return job_id

    def _authorized(self, p, job_id, now):
        self._principal(p); self._clock(now); identifier(job_id)
        job = self._jobs.get(job_id)
        if not job or (job['tenant'], job['user']) != (p.tenant, p.user) or not job['objects'] <= p.objects:
            raise PermissionError('job unavailable')
        if now < job['created_at'] or (job['ready_at'] is not None and now < job['ready_at']):
            raise ValueError('clock precedes job state')
        return job

    def status(self, p, job_id, now):
        with self._lock:
            job = self._authorized(p, job_id, now)
            state = 'expired' if now >= job['expires_at'] else job['state']
            return {'state':state,'data_version':job['version'],'row_count':len(job['snapshot']),
                    'expires_at':job['expires_at'],'sha256':job['sha256'] if state=='ready' else None}

    def run(self, p, job_id, now):
        with self._lock:
            job = self._authorized(p, job_id, now)
            if now >= job['expires_at']: raise ValueError('expired')
            if job['state']=='ready': return self.status(p, job_id, now)
            stream = io.StringIO(newline='')
            writer = csv.writer(stream)
            writer.writerow(['object_id','name','count'])
            for obj, name, count in job['snapshot']:
                writer.writerow([text_cell(obj),text_cell(name),count])
            content = stream.getvalue().encode('utf-8')
            # Publish complete bytes and metadata together under one local lock.
            job.update(content=content,sha256=hashlib.sha256(content).hexdigest(),ready_at=now,state='ready')
            return self.status(p, job_id, now)

    def download(self, p, job_id, now):
        with self._lock:
            job = self._authorized(p, job_id, now)
            if now >= job['expires_at']: raise ValueError('expired')
            if job['state']!='ready': raise ValueError('not ready')
            return job['content']


def demo():
    p=Principal('tenant-demo','user-demo',True,frozenset({'poi-demo'}))
    exports=Exports()
    rows=[dict(tenant=p.tenant,object_id='poi-demo',name='=SUM(1,2)',count=25,private_note='excluded')]
    job=exports.create(p,'request-demo','snapshot-v1',['poi-demo'],rows,100,60)
    queued=exports.status(p,job,100)
    ready=exports.run(p,job,101)
    return {'fictional':True,'queued':queued,'ready':ready,'csv_utf8':exports.download(p,job,102).decode(),'expired':exports.status(p,job,160)}
