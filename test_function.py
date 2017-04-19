import math

def quantize(e=[0.24,3.98], stepSize=0.25, quantizeStartTime=True, quantizeDuration=True):
    beat_grid = 2 * (1.0 / stepSize)
    if quantizeStartTime:
        starts = (e[0] * beat_grid) % 2
        if starts < 1.0:
            e[0] = math.floor(e[0] * beat_grid) / beat_grid
        elif starts == 1.0:
            e[0] = ((e[0] - (stepSize * 0.5)) * beat_grid) / beat_grid
        else:
            e[0] = math.ceil(e[0] * beat_grid) / beat_grid
    if quantizeDuration:
        if e[1] < (stepSize * 0.5):
            e[1] = stepSize
        else:
            durs = (e[1] * beat_grid) % 2
            if durs < 1.0:
                e[1] = math.floor(e[1] * beat_grid) / beat_grid
            elif durs == 1.0:
                e[1] = ((e[1] + (stepSize * 0.5)) * beat_grid) / beat_grid
            else:
                e[1] = math.ceil(e[1] * beat_grid) / beat_grid
    return e


quantize([0.125, 0.5])
