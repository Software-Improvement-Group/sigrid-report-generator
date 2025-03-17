import math

_USE_SIG_STERREN = False


def use_sig_sterren(enabled: bool = True) -> None:
    """
    Enable the use of SIG sterren notation for star ratings.

    This function sets the global flag _USE_SIG_STERREN to True, which causes
    the calculate_stars function to return star ratings using the H/I notation
    (HIIII, HHIII, etc.) instead of the default ★/☆ notation.

    For internal SIG use only.
    """
    global _USE_SIG_STERREN
    _USE_SIG_STERREN = enabled


def calculate_stars(maintainability_rating: float) -> str:
    sig_sterren_ratings = ("HIIII", "HHIII", "HHHII", "HHHHI", "HHHHH")
    star_ratings = ("★☆☆☆☆", "★★☆☆☆", "★★★☆☆", "★★★★☆", "★★★★★")

    ratings = sig_sterren_ratings if _USE_SIG_STERREN else star_ratings

    if maintainability_rating < 0.1:
        return ""
    elif maintainability_rating < 1.5:
        return ratings[0]
    elif maintainability_rating < 2.5:
        return ratings[1]
    elif maintainability_rating < 3.5:
        return ratings[2]
    elif maintainability_rating < 4.5:
        return ratings[3]
    else:
        return ratings[4]


def maintainability_round(rating) -> str:
    if isinstance(rating, str):
        rating = float(rating)

    return "N/A" if rating < 0.1 else str(math.floor(rating * 10) / 10)
