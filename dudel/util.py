def load_icons(filename):
    with open(filename) as f:
        lines = f.readlines()
        return [x.strip("\n").split(" ", 1) for x in lines if x]
    return []
