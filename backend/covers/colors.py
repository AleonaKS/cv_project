import numpy as np

def color_contrast(colors):
    return float(np.std(colors))

def warm_cold_ratio(colors):
    reds = colors[:, 0]
    blues = colors[:, 2]
    return float(np.mean(reds - blues))
