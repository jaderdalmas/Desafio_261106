import matplotlib.pyplot as plt


def save_profit(value):

    fig, ax = plt.subplots()

    ax.bar(["profit"], [value])

    fig.savefig(
        "outputs/profit.png"
    )