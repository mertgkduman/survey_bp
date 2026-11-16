"""Slow, independently orchestrated min-sum/beam/relay algebra oracle."""
import numpy as np


def uniform(seed, shot, leg, variable):
    mask = (1 << 64)-1
    x = seed ^ (((shot+1)*0x9e3779b97f4a7c15) & mask) ^ (((leg+1)*0xd1b54a32d192ed03) & mask) ^ (((variable+1)*0x94d049bb133111eb) & mask)
    x = ((x ^ (x >> 30))*0xbf58476d1ce4e5b9) & mask
    x = ((x ^ (x >> 27))*0x94d049bb133111eb) & mask
    x ^= x >> 31
    return (x >> 11)/9007199254740992.


def decode(h, syndrome, initial, prior, controls, seed, shot):
    edges = list(zip(*np.nonzero(h)))
    c = controls

    def segment(fixed, inherited, posterior, gamma, cap):
        active = [e for e, (_, v) in enumerate(edges) if v not in fixed]
        rows = [[e for e in active if edges[e][0] == check] for check in range(len(h))]
        target = syndrome.copy()
        for v, bit in fixed.items():
            if bit:
                target ^= h[:, v]
        old = inherited.copy()
        posterior = posterior.copy()
        summed = np.zeros(len(prior))
        clips = 0
        for t in range(1, cap+1):
            effective = (1.-gamma)*prior+gamma*posterior
            clips += int(np.count_nonzero((effective < -1e6) | (effective > 1e6)))
            effective = np.clip(effective, -1e6, 1e6)
            scale = c.alpha*(1.-2.**(-min(t, 54))) if c.paper_scale else c.alpha
            checks = {}
            for check, row in enumerate(rows):
                for e in row:
                    values = [old[o] for o in row if o != e]
                    magnitude = min(abs(v) for v in values) if values else 23.7189981105
                    message = scale*max(0., magnitude-c.beta)
                    if (int(target[check])+sum(v < 0 for v in values)) % 2:
                        message = -message
                    checks[e] = message
            posterior = effective.copy()
            for e in active:
                posterior[edges[e][1]] += checks[e]
            candidate = (posterior < 0).astype(np.uint8)
            for v, bit in fixed.items():
                candidate[v] = bit
            for v in range(len(prior)):
                if v not in fixed:
                    summed[v] += posterior[v]
            new = old.copy()
            for e in active:
                fresh = posterior[edges[e][1]]-checks[e]
                new[e] = c.damping*old[e]+(1.-c.damping)*fresh
            old = new
            valid = np.array_equal((h @ candidate) % 2, syndrome)
            if valid:
                break
        return candidate, posterior, summed, old, bool(valid), t, len(active), clips

    root = segment({}, np.full(len(edges), initial), prior,
                   np.full(len(prior), c.first_gamma if c.method == 'relay' else 0.), c.initial)
    states = [root]
    masks = [{}]
    traces = [[-1, -1, -1, root[5], root[6], int(root[4]), 0, root[7]]]
    scores = [0.]
    valid = [0] if root[4] else []
    if root[4] and (c.method == 'beam' or c.solutions == 1):
        return root[0], root[1], True, 0, np.array(traces), np.array(scores), np.array([root[1]]), np.array([root[3]])
    frontier = [0]
    for _ in range(c.rounds if c.method == 'beam' else c.units):
        children = []
        for parent in (frontier if c.method == 'beam' else [len(states)-1]):
            free = [v for v in range(len(prior)) if v not in masks[parent]]
            variable = min(free, key=lambda v: (abs(states[parent][2][v]), v)) if c.method == 'beam' and free else -1
            if c.method == 'beam' and not free:
                continue
            for bit in ((0, 1) if c.method == 'beam' else (-1,)):
                if len(states)-1 == c.units:
                    break
                index = len(states)
                fixed = {**masks[parent], **({variable: bit} if c.method == 'beam' else {})}
                gamma = (np.zeros(len(prior)) if c.method == 'beam' else
                         np.array([c.gamma_low+(c.gamma_high-c.gamma_low)*uniform(seed, shot, index, v) for v in range(len(prior))]))
                inherited = states[parent][3] if c.method == 'beam' else np.full(len(edges), initial)
                value = segment(fixed, inherited, states[parent][1], gamma, c.per_unit)
                states.append(value); masks.append(fixed)
                traces.append([parent, variable, bit, value[5], value[6], int(value[4]), 0, value[7]])
                scores.append(sum(abs(value[2][v])/value[5] for v in range(len(prior)) if v not in fixed))
                if value[4]:
                    valid.append(index)
                    if len(valid) >= c.solutions:
                        break
                elif c.method == 'beam':
                    children.append(index)
            if len(states)-1 == c.units or len(valid) >= c.solutions:
                break
        if len(states)-1 == c.units or len(valid) >= c.solutions:
            break
        if c.method == 'beam':
            children.sort(key=lambda i: (-scores[i], i))
            for index in children[c.width:]:
                traces[index][6] = 1
            frontier = children[:c.width]
            if not frontier:
                break
    best = min(valid, key=lambda i: (float(np.dot(states[i][0].astype(float), prior)), i)) if valid else -1
    selected = states[best] if best >= 0 else states[-1]
    return selected[0], selected[1], best >= 0, best, np.array(traces), np.array(scores), np.array([s[1] for s in states]), np.array([s[3] for s in states])
