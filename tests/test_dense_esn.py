"""
# dense esncell still has to be implemented...
def tst_esn():
    # Set up data for training and prediction
    Ntrans     = 500   # Number of transient initial steps before training
    Ntrain     = 2500  # Number of steps to train on
    Npred      = 500   # Number of steps for free-running prediction
    hidden_size = 1500  # size of reservoir

    esn = dense_esncell(1,hidden_size, spectral_radius=1.5, density=0.05)

    xs   = jnp.linspace(0,30*2*jnp.pi,Ntrain+Npred)
    data = jnp.sin(xs).reshape(-1, 1)

    inputs, labels, pred_labels = split_train_label_pred(data,Ntrain,Npred)

    H = dense_generate_state_matrix(esn, inputs, Ntrans)
    assert H.shape == (Ntrain-Ntrans, hidden_size+2)
    # plt.plot(H)
    # plt.show()

    Who = lstsq_stable(H, labels[Ntrans:])
    Wih, Whh, bh = esn
    model = (Wih,Whh,bh,Who)
    # plt.plot(labels[Ntrans:])
    # ts = Who.dot(H.T).reshape(-1)
    # plt.plot(ts)
    # plt.show()

    y0 = labels[-1]
    h0 = H[-1]
    (y,h), (ys,hs) = dense_predict_esn(model, y0, h0, Npred)
    assert y.shape == (1,)
    assert ys.shape == (Npred, 1)
    assert h.shape == (hidden_size+2,)
    assert hs.shape == (Npred, hidden_size+2)

    pred_labels = pred_labels.reshape(-1)
    print(jnp.mean(jnp.abs(ys - pred_labels)))

    plt.plot(ys, label="Truth")
    plt.plot(pred_labels.reshape(-1), label="Prediction")
    plt.title("500 step prediction vs. truth")
    plt.legend()
    plt.show()
"""
