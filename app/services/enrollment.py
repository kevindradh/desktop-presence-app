"""Authorized atomic member/embedding enrollment from a fresh signed capture packet."""
import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import replace
from dataclasses import dataclass
from sqlalchemy import func,select
from ai.enrollment import ANGLES,CapturePacket
from app.models.entities import Member,MemberGroup,FaceEmbedding
from app.repositories.core import AuditRepository,EmbeddingRepository,normalized_vector
from app.services.administration import AdministrationService,validate_member,member_data,identifier
from app.services.database import DataValidationError
from app.services.member_photos import PhotoStore


@dataclass(frozen=True)
class VerificationResult:
    matched: bool
    similarity: float | None


class EnrollmentService:
    def __init__(self,auth,root,*,storage_enabled=False,clock=time.monotonic,similarity_threshold=.60):
        from ai.contracts import EngineOptions
        EngineOptions(similarity_threshold=similarity_threshold)
        self.auth=auth
        self.photos=PhotoStore(root)
        self.storage_enabled=storage_enabled
        self.clock=clock
        self.similarity_threshold=similarity_threshold
        self.key=secrets.token_bytes(32)
        self.flows={}

    def begin(self,token,*,member_id=None,revision=None,fields=None,purpose='enrollment'):
        def operation(session,actor):
            if purpose not in ('enrollment','verification') or (purpose=='verification' and member_id is None):
                raise DataValidationError('Tujuan capture tidak valid.')
            if fields is not None:
                checked=validate_member(fields['code'],fields['name'],fields['group_id'],
                    fields.get('email',''),fields.get('phone',''),fields.get('position',''))
                AdministrationService._row(session,MemberGroup,checked['group_id'])
                duplicate=session.scalar(select(Member.id).where(func.lower(Member.member_code)==checked['member_code'].lower(),
                    Member.id!=member_id if member_id is not None else True).limit(1))
                if duplicate is not None:
                    raise DataValidationError('ID anggota sudah digunakan.')
            if member_id is not None:
                member=AdministrationService._row(session,Member,member_id,identifier(revision))
                if not member.is_active:
                    raise DataValidationError('Anggota nonaktif tidak dapat diregistrasi ulang.')
                if purpose=='verification' and session.scalar(select(FaceEmbedding.id).where(
                    FaceEmbedding.member_id==member.id,FaceEmbedding.is_active.is_(True)).limit(1)) is None:
                    raise DataValidationError('Anggota belum memiliki sampel wajah tersimpan.')
            now=self.clock()
            self.flows={k:v for k,v in self.flows.items() if now-v['created']<=900}
            if len(self.flows)>=20:
                raise DataValidationError('Terlalu banyak sesi capture. Tutup capture lama dan coba lagi.')
            binding=dict(nonce=secrets.token_hex(24),token_hash=hashlib.sha256(token.encode()).hexdigest(),
                member_id=member_id,revision=revision,created=now,purpose=purpose)
            from app.services.settings import read_values
            binding['settings']=read_values(session)
            from copy import deepcopy
            self.flows[binding['nonce']]=deepcopy(binding)
            return dict(binding)
        return self.auth._protected(token,'members',operation)

    def cancel(self,binding):
        self.flows.pop(binding['nonce'],None)

    def _read(self,packet,token,member_id,revision):
        try:
            if not isinstance(packet,CapturePacket) or not isinstance(packet.body,bytes) or len(packet.body)>3*1024*1024:
                raise ValueError
            expected=hmac.new(self.key,packet.body,hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected,packet.signature):
                raise ValueError
            data=json.loads(packet.body)
            binding=data['binding']
            saved=self.flows.get(binding['nonce'])
            if saved is None or saved!=binding or binding['member_id']!=member_id or binding['revision']!=revision:
                raise ValueError
            if binding['purpose']!='enrollment':
                raise ValueError
            if binding['token_hash']!=hashlib.sha256(token.encode()).hexdigest() or not 0<=self.clock()-binding['created']<=900:
                raise ValueError
            if not binding['created']<=data['created']<=self.clock():
                raise ValueError
            samples=data['samples']
            if len(samples)!=5 or tuple(s['angle'] for s in samples)!=ANGLES:
                raise ValueError
            vectors=[normalized_vector(s['vector']) for s in samples]
            version=data['model_version']
            if not isinstance(version,str) or not version or len(version)>120:
                raise ValueError
            photo=base64.b64decode(data['photo'],validate=True)
            if not photo:
                raise ValueError
            return binding,vectors,version,photo
        except (ValueError,TypeError,KeyError,AttributeError,OverflowError):
            raise DataValidationError('Hasil capture tidak valid, belum lengkap, sudah dipakai atau kedaluwarsa. Ambil ulang lima sudut.') from None

    def save(self,token,packet,*,code,name,group_id,email='',phone='',position='',member_id=None,revision=None):
        imported=[]
        obsolete=[]
        used=[]
        def operation(session,actor):
            if not self.storage_enabled:
                raise DataValidationError('Penyimpanan biometrik belum diaktifkan sampai aturan retensi ditetapkan.')
            binding,vectors,version,photo=self._read(packet,token,member_id,revision)
            fields=validate_member(code,name,group_id,email,phone,position)
            AdministrationService._row(session,MemberGroup,fields['group_id'])
            if session.scalar(select(Member.id).where(func.lower(Member.member_code)==fields['member_code'].lower(),
                Member.id!=member_id if member_id is not None else True).limit(1)) is not None:
                raise DataValidationError('ID anggota sudah digunakan.')
            row=None if member_id is None else AdministrationService._row(session,Member,member_id,identifier(revision))
            if row is not None and not row.is_active:
                raise DataValidationError('Anggota nonaktif tidak dapat diregistrasi ulang.')
            path=self.photos.import_bytes(photo)
            imported.append(path)
            if row is None:
                row=Member(**{k:(v or None if k in {'email','phone','position'} else v) for k,v in fields.items()},photo_path=path)
                session.add(row)
            else:
                obsolete.append(row.photo_path)
                for key,value in fields.items():
                    setattr(row,key,value or None if key in {'email','phone','position'} else value)
                row.photo_path=path
                row.revision+=1
                for old in session.scalars(select(FaceEmbedding).where(FaceEmbedding.member_id==row.id)):
                    session.delete(old)
            session.flush()
            repository=EmbeddingRepository(session)
            for angle,vector in zip(ANGLES,vectors):
                repository.create(row.id,vector,angle,version)
            AuditRepository(session).append('member.enrolled' if member_id is None else 'member.reregistered',
                'member',row.id,actor_id=actor.id,details={'record_count':5,'changed_fields':['photo_path','embedding']})
            used.append(binding['nonce'])
            return member_data(session,row)
        try:
            result=self.auth._protected(token,'members',operation)
        except Exception:
            for path in imported:
                self.photos.discard_uncommitted(path)
            raise
        for nonce in used:
            self.flows.pop(nonce,None)
        try:
            pending=self.auth._protected(token,'members',lambda session,actor:self.photos.cleanup_orphans(session))>0
        except Exception:
            pending=bool(obsolete)
        return replace(result,cleanup_pending=pending)

    def verify(self,token,packet):
        consumed=[]
        def operation(session,actor):
            try:
                if not isinstance(packet,CapturePacket) or not isinstance(packet.body,bytes) or len(packet.body)>100_000:
                    raise ValueError
                if not hmac.compare_digest(hmac.new(self.key,packet.body,hashlib.sha256).hexdigest(),packet.signature):
                    raise ValueError
                data=json.loads(packet.body)
                binding=data['binding']
                if data['kind']!='probe' or binding.get('purpose')!='verification' or self.flows.get(binding['nonce'])!=binding:
                    raise ValueError
                now=self.clock()
                if binding['token_hash']!=hashlib.sha256(token.encode()).hexdigest() or not 0<=now-binding['created']<=900:
                    raise ValueError
                if not binding['created']<=data['created']<=now:
                    raise ValueError
                vector=normalized_vector(data['vector'])
                version=data['model_version']
                if not isinstance(version,str) or not version or len(version)>120:
                    raise ValueError
            except (ValueError,TypeError,KeyError,AttributeError,OverflowError):
                raise DataValidationError('Probe wajah tidak valid, kedaluwarsa atau sudah digunakan. Ulangi pemeriksaan.') from None
            member=AdministrationService._row(session,Member,binding['member_id'],binding['revision'])
            if not member.is_active:
                raise DataValidationError('Anggota sudah nonaktif.')
            from ai.embedding.search import identify
            result=identify(session,vector,model_version=version,threshold=binding['settings']['similarity_threshold'])
            consumed.append(binding['nonce'])
            return VerificationResult(result.member_id==member.id,result.similarity)
        result=self.auth._protected(token,'members',operation)
        for nonce in consumed:self.flows.pop(nonce,None)
        return result
