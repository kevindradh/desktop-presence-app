# MiniFASNet upstream source

Source: https://github.com/minivision-ai/Silent-Face-Anti-Spoofing
Commit: `b6d5f04ad78778917853b25c778acef6d5626d15`. `MiniFASNet.py` is copied unchanged.
License: Apache-2.0; see LICENSE. Upstream copyright headers are retained.
Only the network definition is vendored; upstream training scripts are not executed.
Checkpoint loads use `torch.load(..., weights_only=True, map_location="cpu")`.
The companion RetinaFace Caffe detector is kept separate from ArcFace recognition.
