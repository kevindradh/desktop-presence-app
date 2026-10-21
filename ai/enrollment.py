"""Five-angle capture in memory, signed handoff; no persistence or Qt dependencies."""
from dataclasses import dataclass,field
import hashlib
import hmac
import json
import math
import secrets
import time
import cv2
import numpy as np
from ai.embedding.search import cosine_similarity

ANGLES=('FRONT','LEFT','RIGHT','UP','DOWN')
GUIDES={'FRONT':'Hadapkan wajah lurus ke kamera','LEFT':'Putar perlahan hingga hidung ke kanan gambar',
 'RIGHT':'Putar perlahan hingga hidung ke kiri gambar','UP':'Angkat wajah perlahan','DOWN':'Tundukkan wajah perlahan'}


class CaptureError(ValueError):
    pass


@dataclass(frozen=True,repr=False)
class CapturePacket:
    body: bytes=field(repr=False)
    signature: str=field(repr=False)


def pose_ratios(points):
    points=np.asarray(points,dtype=np.float64)
    if points.shape!=(5,2) or not np.isfinite(points).all():
        raise CaptureError('Titik wajah belum valid.')
    eye=points[1]-points[0]
    distance=float(np.linalg.norm(eye))
    if distance<8:
        raise CaptureError('Wajah terlalu kecil untuk panduan sudut.')
    axis=eye/distance
    vertical=np.array([-axis[1],axis[0]])
    center=(points[0]+points[1])/2
    nose=points[2]-center
    mouth=(points[3]+points[4])/2-center
    gap=float(np.dot(mouth,vertical))
    if gap<=distance*.25:
        raise CaptureError('Posisi wajah belum sesuai.')
    yaw=float(np.dot(nose,axis)/distance)
    pitch=float(np.dot(nose,vertical)/gap)
    roll=math.degrees(math.atan2(axis[1],axis[0]))
    return yaw,pitch,roll


def angle_matches(angle,pose,front):
    yaw,pitch,roll=pose
    if abs(roll)>20:
        return False
    if angle=='FRONT':
        return abs(yaw)<=.15 and .25<=pitch<=.75
    if front is None:
        return False
    dy,dp=yaw-front[0],pitch-front[1]
    return {'LEFT':dy>=.12 and abs(dp)<.15,'RIGHT':dy<=-.12 and abs(dp)<.15,
        'UP':dp<=-.10 and abs(dy)<.12,'DOWN':dp>=.10 and abs(dy)<.12}.get(angle,False)


class CaptureDraft:
    def __init__(self,*,binding,key,model_version,clock=time.monotonic,identity_threshold=.60):
        self.binding=dict(binding)
        self.key=key
        self.version=model_version
        self.clock=clock
        self.identity_threshold=identity_threshold
        self.created=clock()
        self.front_pose=None
        self.samples=[]
        self.photo=None
        self.packet_id=secrets.token_hex(24)

    @property
    def expected(self):
        return ANGLES[len(self.samples)] if len(self.samples)<5 else None

    def status(self,analysis):
        if analysis.status!='ready' or analysis.face_count!=1 or analysis.embedding is None:
            raise CaptureError('Wajah harus tunggal dan lolos kualitas serta pemeriksaan keaslian.')
        if analysis.live_class!=1 or analysis.live_score is None or not .85<=analysis.live_score<=1:
            raise CaptureError('Sampel harus lolos pemeriksaan keaslian pada ambang registrasi 0,85.')
        pose=pose_ratios(analysis.points)
        if not angle_matches(self.expected,pose,self.front_pose):
            raise CaptureError('Sudut belum sesuai panduan. Gerakkan kepala perlahan, lalu coba lagi.')
        if self.samples and cosine_similarity(self.samples[0][1],analysis.embedding)<self.identity_threshold:
            raise CaptureError('Wajah berbeda dari referensi depan. Ulangi dengan orang yang sama.')
        return pose

    def add(self,analysis,frame):
        if self.clock()-self.created>900:
            raise CaptureError('Sesi capture kedaluwarsa. Mulai ulang.')
        if self.expected is None:
            raise CaptureError('Lima sudut sudah lengkap.')
        pose=self.status(analysis)
        if not self.samples:
            self.front_pose=pose
            x1,y1,x2,y2=analysis.box
            success,png=cv2.imencode('.png',frame[y1:y2,x1:x2])
            if not success or len(png)>2*1024*1024:
                raise CaptureError('Foto depan tidak dapat disiapkan.')
            self.photo=png.tobytes()
        self.samples.append((self.expected,analysis.embedding.copy()))

    def seal(self):
        if self.expected is not None:
            raise CaptureError('Capture lima sudut belum lengkap.')
        import base64
        content=dict(binding=self.binding,created=self.created,packet_id=self.packet_id,
            model_version=self.version,samples=[dict(angle=a,vector=v.tolist()) for a,v in self.samples],
            photo=base64.b64encode(self.photo).decode('ascii'))
        body=json.dumps(content,separators=(',',':'),allow_nan=False).encode()
        return CapturePacket(body,hmac.new(self.key,body,hashlib.sha256).hexdigest())

    def clear(self):
        for _,vector in self.samples:
            vector.fill(0)
        self.samples.clear()
        self.photo=None
        self.front_pose=None


class AutoCapture:
    """Require consecutive valid, consistent observations before accepting a pose."""
    def __init__(self,draft,*,clock=time.monotonic,hold_seconds=.6,min_observations=3,max_gap=2.):
        self.draft=draft
        self.clock=clock
        self.hold_seconds=hold_seconds
        self.min_observations=min_observations
        self.max_gap=max_gap
        self.reset()

    def reset(self):
        if getattr(self,'embedding',None) is not None:
            self.embedding.fill(0)
        self.embedding=None
        self.pose=None
        self.box=None
        self.angle=None
        self.began=self.last=None
        self.observations=0

    def consider(self,analysis,frame):
        now=self.clock()
        try:
            pose=self.draft.status(analysis)
        except CaptureError:
            self.reset()
            return False
        box=analysis.box
        if box is None or len(box)!=4 or not all(math.isfinite(v) for v in box) or box[2]<=box[0] or box[3]<=box[1]:
            self.reset()
            return False
        same=(self.angle==self.draft.expected and self.pose is not None and self.last is not None
              and 0<=now-self.last<=self.max_gap
              and abs(pose[0]-self.pose[0])<=.04 and abs(pose[1]-self.pose[1])<=.05
              and abs(pose[2]-self.pose[2])<=5
              and all(abs(box[i]-self.box[i])<=.1*(self.box[2+i%2]-self.box[i%2]) for i in range(4))
              and cosine_similarity(self.embedding,analysis.embedding)>=self.draft.identity_threshold)
        if not same:
            self.reset()
            self.pose=pose
            self.box=tuple(box)
            self.angle=self.draft.expected
            self.embedding=analysis.embedding.copy()
            self.began=now
        self.last=now
        self.observations+=1
        if self.observations<self.min_observations or now-self.began<self.hold_seconds:
            return False
        try:
            self.draft.add(analysis,frame)
            return True
        finally:
            self.reset()
