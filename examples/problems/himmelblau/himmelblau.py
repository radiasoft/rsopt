def himmelblau(x, y):
    """Himmelblau's function.

    A standard multi-modal test problem. It has four global minima, all with f = 0, which is what
    makes it useful for demonstrating optimizers that run several independent searches at once:

        ( 3.000000,  2.000000)
        (-2.805118,  3.131312)
        (-3.779310, -3.283186)
        ( 3.584428, -1.848126)

    A local optimizer converges to whichever minimum lies in the basin of its starting point, so
    which minima are found is decided entirely by where the searches begin.
    """
    return (x ** 2 + y - 11) ** 2 + (x + y ** 2 - 7) ** 2
