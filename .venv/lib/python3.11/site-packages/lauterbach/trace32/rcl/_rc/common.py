def align_eight(n):
    """Calculate the remaining count from n to the next larger number divisible by eight."""

    return align_up(n, 8)


def align_up(n, m):
    """Calculate the remaining count from n to the next larger number divisible by m."""

    if n % m:
        return m - (n % m)
    else:
        return 0


def int2bytearray(n, length):
    """Encodes Integer to bytes array of defined length"""
    assert isinstance(n, int), ">{}< is not of type integer, but {}".format(n, type(n))
    if n < 0:
        return n.to_bytes(length, "little", signed=True)
    else:
        return n.to_bytes(length, "little", signed=False)


def up_align(size, align_to):
    """Calculate the next larger number divisble by a given integer.

    Args:
        size (int): nonzero integer to which the next larger number divisible by align_to is searched for.
        align_to (int): nonzero positive integer which is the divisor

    Return:
        size: smallest integer divisible by align_to that is larger than passed in size value

    """

    while size % align_to:
        size += 1
    return size


def down_align(size, align_to):
    """Calculate the next smaller number divisble by a given integer.

    Args:
        size (int): nonzero integer to which the next smaller number divisible by align_to is searched for.
        align_to (int): nonzero positive integer which is the divisor

    Return:
        size: largest integer divisible by align_to that is smamller than passed in size value

    """

    while size % align_to:
        size -= 1
    return size
