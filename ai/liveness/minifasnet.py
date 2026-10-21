"""One pinned MiniFASNetV2 checkpoint: class 1 live probability, not ensemble /2."""
import cv2
import numpy as np
from ai.contracts import ModelError


def context_crop(image,box):
    height,width=image.shape[:2]
    x1,y1,x2,y2=box
    bw,bh=x2-x1,y2-y1
    if bw<=0 or bh<=0 or height<2 or width<2:
        raise ModelError()
    scale=min(2.7,(width-1)/bw,(height-1)/bh)
    cw,ch=bw*scale,bh*scale
    left=min(max(0,(x1+x2-cw)/2),width-1-cw)
    top=min(max(0,(y1+y2-ch)/2),height-1-ch)
    patch=image[int(top):int(top+ch)+1,int(left):int(left+cw)+1]
    return cv2.resize(patch,(80,80),interpolation=cv2.INTER_LINEAR)


def tensor_bgr(patch):
    # Pinned upstream functional.to_tensor preserves BGR and float range 0..255.
    # Its docstring says 0..1, but the actual division is commented out.
    import torch
    return torch.from_numpy(np.ascontiguousarray(patch.transpose(2,0,1))).float().unsqueeze(0)


class MiniFASNet:
    def __init__(self,assets):
        try:
            import torch
            from third_party.minifasnet.MiniFASNet import MiniFASNetV2
            torch.set_num_threads(2)
            self.net=MiniFASNetV2(conv6_kernel=(5,5))
            state=torch.load(assets["minifasnet-weights"],map_location="cpu",weights_only=True)
            self.net.load_state_dict({key.removeprefix("module."):value for key,value in state.items()},strict=True)
            self.net.eval()
        except Exception:
            raise ModelError() from None

    def score(self,image,box):
        import torch
        tensor=tensor_bgr(context_crop(image,box))
        with torch.inference_mode():
            logits=self.net(tensor)
            if tuple(logits.shape)!=(1,3) or not bool(torch.isfinite(logits).all()):
                raise ModelError()
            probabilities=torch.softmax(logits,dim=1)[0]
        return float(probabilities[1]),int(torch.argmax(probabilities))
