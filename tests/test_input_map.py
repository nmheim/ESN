import joblib
import numpy as np
import jax
import jax.numpy as jnp
from jax.config import config
config.update("jax_enable_x64", True)

from esn.input_map import make_operation, rescale, InputMap, ScaleOp, PixelsOp


IMG_SHAPE = (6,6)

RAND_SPEC = {"type":"random_weights",
            "input_size":IMG_SHAPE[0]*IMG_SHAPE[1],
            "hidden_size":20,
            "factor":0.5}

PIXEL_SPEC = {"type":"pixels", "size":(3,3), "factor": 0.5}

CONV_SPEC = {"type":"conv", "size":(2,2), "kernel":"gauss", "factor": 0.5}

GRAD_SPEC = {"type":"gradient", "factor": 0.5}

DCT_SPEC  = {"type":"dct", "size":(3,3), "factor": 0.5}

SPECS = [RAND_SPEC, CONV_SPEC, PIXEL_SPEC, GRAD_SPEC, DCT_SPEC]

def _testop(spec, tmpdir):
    img = jax.device_put(np.random.uniform(size=IMG_SHAPE))
    op = make_operation(spec)
    assert op(img).shape == (op.output_size(IMG_SHAPE),)

    with open(tmpdir / "op.pkl", "wb") as fi:
        joblib.dump(op, fi) 
    pkl_op = type(op).fromfile(tmpdir / "op.pkl")
    assert type(pkl_op(img)) == type(img)
    return op

def test_rand_operation(tmpdir):
    op = _testop(RAND_SPEC, tmpdir)
    img = jax.device_put(np.random.uniform(size=IMG_SHAPE))
    vec = img.reshape(-1)
    assert op(vec).shape == (op.output_size(IMG_SHAPE),)

def test_pixel_operation(tmpdir):
    op = _testop(PIXEL_SPEC, tmpdir)

def test_conv_operation(tmpdir):
    op = _testop(CONV_SPEC, tmpdir)

def test_grad_operation(tmpdir):
    op = _testop(GRAD_SPEC, tmpdir)

def test_dct_operation(tmpdir):
    op = _testop(DCT_SPEC, tmpdir)

def test_scale_operation():
    img = jax.device_put(np.random.uniform(size=IMG_SHAPE))
    op = PixelsOp(PIXEL_SPEC["size"])
    sp = ScaleOp(2, op)

    o1 = np.array(op(img))
    o2 = np.array(sp(img))
    assert np.allclose(o1*2, o2)

    sp = ScaleOp(4, op)
    o2 = np.array(sp(img))
    assert np.allclose(o1*4, o2)

def test_input_map(tmpdir):
    img = jax.device_put(np.random.uniform(size=(IMG_SHAPE)))
    mapih = InputMap(SPECS)
    out = mapih(img)

    # test correct output size
    assert out.shape == (mapih.output_size(IMG_SHAPE),)

    # test factor rescale
    fs = np.array([op.factor for op in mapih.ops])
    fs = fs * 2
    mapih = rescale(mapih, fs)
    assert np.allclose(out * 2, mapih(img))

    # test save / load
    with open(tmpdir / "mapih.pkl", "wb") as fi:
        joblib.dump(mapih, fi) 
    pkl_mapih = InputMap.fromfile(tmpdir / "mapih.pkl")
    assert type(pkl_mapih(img)) == type(img)


if __name__ == "__main__":
    test_make_operation()
    test_input_map()
