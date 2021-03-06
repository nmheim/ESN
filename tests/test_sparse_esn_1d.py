import joblib
import numpy as np
import jax.numpy as jnp
from jax.config import config
config.update("jax_enable_x64", True)

from esn.input_map import InputMap
from esn.utils import split_train_label_pred
from esn.toydata import mackey_sequence
import esn.sparse_esn as se


def sparse_esn_1d_train_pred(tmpdir, data,
                             Ntrans=500,        # Number of transient initial steps before training
                             Ntrain=2500,       # Number of steps to train on
                             Npred=500,         # Number of steps for free-running prediction
                             hidden_size=1500,  # size of reservoir
                             mse_threshold=1e-10,
                             plot_states=False,
                             plot_trained_outputs=False,
                             plot_prediction=False):
    np.random.seed(0)

    N = Ntrain + Npred + 1
    assert data.ndim == 1
    assert data.shape[0] >= N

    input_size  = 1

    specs = [{"type":"random_weights",
              "input_size":input_size,
              "hidden_size":hidden_size,
              "factor": 1.0}]
    map_ih = InputMap(specs)
    hidden_size = map_ih.output_size((input_size,))
    esn = se.esncell(map_ih, hidden_size, spectral_radius=1.5, density=0.05)

    data = data.reshape(-1, 1)
    inputs, labels, pred_labels = split_train_label_pred(data,Ntrain,Npred)

    H = se.augmented_state_matrix(esn, inputs, Ntrans)
    assert H.shape == (Ntrain-Ntrans, hidden_size+input_size+1)
    if plot_states:
        import matplotlib.pyplot as plt
        plt.plot(H)
        plt.show()

    model = se.train(esn, H, labels[Ntrans:])
    if plot_trained_outputs:
        import matplotlib.pyplot as plt
        plt.plot(labels[Ntrans:])
        ts = Who.dot(H.T).reshape(-1)
        plt.plot(ts)
        plt.show()

    y0 = labels[-1]
    h0 = H[-1]
    (y,h), (ys,hs) = se.predict(model, y0, h0, Npred)
    assert y.shape == (1,)
    assert ys.shape == (Npred, 1)
    assert h.shape == (hidden_size+input_size+1,)
    assert hs.shape == (Npred, hidden_size+input_size+1)

    _, (wys,_) = se.warmup_predict(model, labels[-Ntrans:], Npred)

    mse = jnp.mean((ys - pred_labels)**2)
    w_mse = jnp.mean((wys - pred_labels)**2)
    if plot_prediction:
        import matplotlib
        matplotlib.use('TkAgg')
        import matplotlib.pyplot as plt
        plt.plot(ys, label="Prediction")
        plt.plot(pred_labels.reshape(-1), label="Truth")
        plt.plot(wys, label="Warmup Prediction")
        plt.title(f"500 step prediction vs. truth | MSE={mse}")
        plt.legend()
        plt.show()
    print(f"MSE: {mse}")
    assert mse < mse_threshold
    assert w_mse < mse_threshold
    assert jnp.isclose(mse, w_mse)

    with open(tmpdir / "esn.pkl", "wb") as fi:
        joblib.dump(model, fi)
    pkl_model = se.load_model(tmpdir / "esn.pkl")
    _, (pkl_ys,_) = se.predict(pkl_model, y0, h0, Npred)
    assert jnp.all(jnp.isclose(pkl_ys, ys))



def test_sparse_esn_sines(tmpdir):
    Ntrain = 2500
    Npred  = 500
    xs   = jnp.linspace(0,30*2*jnp.pi,Ntrain+Npred+1)
    data = jnp.sin(xs)
    sparse_esn_1d_train_pred(tmpdir, data,
        Ntrain=Ntrain, Npred=Npred, plot_prediction=False)


def test_sparse_esn_mackey(tmpdir):
    data = mackey_sequence(N=3500)
    sparse_esn_1d_train_pred(tmpdir, data,
                             hidden_size=2000,
                             Npred=200,
                             plot_prediction=False,
                             mse_threshold=1e-4)

if __name__ == "__main__":
    test_sparse_esn_mackey()
    #test_sparse_esn_sines()
