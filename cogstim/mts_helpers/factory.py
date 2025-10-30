from PIL import Image

from cogstim.helpers import COLOUR_MAP, SIZES
from cogstim.dots_core import NumberPoints


def create_numberpoints_image(bg_colour: str, dot_colour: str, min_radius: int, max_radius: int, attempts_limit: int):
    img = Image.new("RGB", (SIZES["init_size"], SIZES["init_size"]), color=bg_colour)
    np_obj = NumberPoints(
        img,
        SIZES["init_size"],
        colour_1=COLOUR_MAP[dot_colour],
        colour_2=None,
        min_point_radius=min_radius,
        max_point_radius=max_radius,
        attempts_limit=attempts_limit,
    )
    return img, np_obj


def generate_random_points(np_obj: NumberPoints, n_points: int):
    return np_obj.design_n_points(n_points, "colour_1")
