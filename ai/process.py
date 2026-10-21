"""Memory-only model worker: no Qt, database, enrollment files or face-bearing output."""
import os
import numpy as np
from ai.contracts import InferenceTimeout


def inference_process(root,model_dir,options,pixels,shape,lock,connection):
    null=os.open(os.devnull,os.O_WRONLY)
    os.dup2(null,1)
    os.dup2(null,2)
    os.close(null)
    reference=None
    try:
        from ai.engine import FaceEngine
        engine=FaceEngine(root,model_dir,options)
        connection.send({"event":"ready","version":engine.model_version})
        while True:
            command=connection.recv()
            if command=="stop":
                break
            if command=="clear":
                reference=None
                connection.send({"event":"cleared"})
                continue
            if command not in ("analyze","reference"):
                raise ValueError
            with lock:
                height,width=map(int,shape[:])
                if not 16<=height<=540 or not 16<=width<=960:
                    raise ValueError
                frame=np.frombuffer(pixels,dtype=np.uint8,count=height*width*3).copy().reshape(height,width,3)
                np.frombuffer(pixels,dtype=np.uint8).fill(0)
                shape[:]=(0,0)
            try:
                analysis=engine.analyze(frame,purpose="registration")
                from ai.embedding.search import cosine_similarity
                similarity=None
                if analysis.status=="ready":
                    if command=="reference":
                        if reference is not None:
                            reference.fill(0)
                        reference=analysis.embedding.copy()
                    elif reference is not None:
                        similarity=cosine_similarity(reference,analysis.embedding)
                connection.send({"event":"result","status":analysis.status,"face_count":analysis.face_count,
                    "box":analysis.box,"points":analysis.points,"live_score":analysis.live_score,
                    "live_class":analysis.live_class,"elapsed_ms":analysis.elapsed_ms,
                    "has_reference":reference is not None,"similarity":similarity,
                    "matched":similarity is not None and similarity>=options.similarity_threshold})
            finally:
                frame.fill(0)
                # Do not retain the last embedding/crop while idle between requests.
                if 'analysis' in locals():
                    del analysis
    except EOFError:
        pass
    except InferenceTimeout:
        try:
            connection.send({"event":"timeout"})
        except (OSError,BrokenPipeError):
            pass
    except Exception:
        try:
            connection.send({"event":"error"})
        except (OSError,BrokenPipeError):
            pass
    finally:
        if reference is not None:
            reference.fill(0)
        np.frombuffer(pixels,dtype=np.uint8).fill(0)
        shape[:]=(0,0)
        connection.close()
