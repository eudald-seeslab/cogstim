import os
import math
import random
from PIL import Image, ImageDraw
import numpy as np
from tqdm import tqdm

from cogstim.helpers import COLOUR_MAP
from cogstim.base_generator import BaseGenerator
from cogstim.mts_helpers.planner import GenerationPlan

random.seed(1714)


class ShapesGenerator(BaseGenerator):
    """
    A class for generating images with geometric shapes for machine learning tasks.

    Attributes:
        shape (str): The shape of the geometric objects.
        colours (list): The colours of the shapes.
        task_type (str): The type of task to generate images for.
    """

    background_colour = COLOUR_MAP["black"]
    colour_task_base_shape = "circle"
    boundary_width = 5
    img_paths = {}

    def __init__(
        self,
        shapes,
        colours,
        task_type,
        output_dir,
        train_num,
        test_num,
        jitter,
        min_surface,
        max_surface,
        background_colour,
    ):
        # Set directory based on task if not provided explicitly
        if output_dir is not None:
            pass
        else:
            shapes_list = shapes if isinstance(shapes, list) else [shapes]
            if task_type == "two_shapes":
                output_dir = "images/two_shapes"
            elif task_type == "two_colors":
                output_dir = "images/two_colors"
            else:
                output_dir = f"images/{'_'.join(shapes_list)}_{'_'.join(colours)}"
        
        # Initialize parent with config
        config = {
            'output_dir': output_dir,
            'shapes': shapes,
            'colours': colours,
            'task_type': task_type,
            'train_num': train_num,
            'test_num': test_num,
            'jitter': jitter,
            'min_surface': min_surface,
            'max_surface': max_surface,
            'background_colour': background_colour,
        }
        super().__init__(config)
        
        self.shapes = shapes if isinstance(shapes, list) else [shapes]
        self.colors = {col: COLOUR_MAP[col] for col in colours}
        self.task_type = task_type
        self.background_colour = COLOUR_MAP.get(background_colour, background_colour)

        # Override default generation params
        self.train_num = train_num
        self.test_num = test_num
        self.min_surface = min_surface
        self.max_surface = max_surface
        self.jitter = jitter
        self.img_paths = {}

    def get_subdirectories(self):
        """Get list of subdirectories for train/test and classes."""
        subdirs = []
        
        for t in ["train", "test"]:
            if self.task_type == "two_shapes":
                classes = self.shapes
            elif self.task_type == "two_colors":
                classes = self.colors.keys()
            else:
                classes = [
                    f"{shape}_{color}" for shape in self.shapes for color in self.colors
                ]

            for class_name in classes:
                subdirs.append((t, class_name))
                
        return subdirs
    
    def setup_directories(self):
        """Creates class directories for train and test sets and populate img_paths."""
        super().setup_directories()
        
        for t in ["train", "test"]:
            if self.task_type == "two_shapes":
                classes = self.shapes
            elif self.task_type == "two_colors":
                classes = self.colors.keys()
            else:
                classes = [
                    f"{shape}_{color}" for shape in self.shapes for color in self.colors
                ]

            for class_name in classes:
                path_key = f"{t}_{class_name}"
                self.img_paths[path_key] = os.path.join(self.output_dir, t, class_name)

    @staticmethod
    def get_radius_from_surface(shape: str, surface: float) -> float:
        """
        Calculate the radius needed to achieve a specific surface area for different shapes.
        
        Args:
            shape (str): The shape type ('circle', 'triangle', 'square', or 'star')
            surface (float): The desired surface area
            
        Returns:
            float: The radius needed to achieve the specified surface area
        """
        if shape == "circle":
            # A = πr²
            return math.sqrt(surface / math.pi)

        elif shape == "square":
            # A = (2r)² = 4r²
            # where r is half the side length
            return math.sqrt(surface / 4)

        elif shape == "triangle":
            # For an equilateral triangle:
            # A = (√3/4) * (2r)² = √3 * r²
            # where r is the distance from center to any vertex
            return math.sqrt(surface / math.sqrt(3))

        elif shape == "star":
            return np.sqrt(2 / 5 * surface * 1 / np.sqrt((25 - 11 * np.sqrt(5)) / 2))

        else:
            raise ValueError(f"Shape {shape} not implemented.")

    @staticmethod
    def create_star_vertices(center, radius):
        inner_radius = 1 / 1.014 * radius * np.sin(np.pi / 10) / np.sin(7 * np.pi / 10)

        vertices = []
        for i in range(5):
            # Outer vertices (points of the star)
            angle_rad = -np.pi/2 + i * 2 * np.pi / 5  # Start from top (-pi/2) and go clockwise
            vertices.append(
                (
                    center[0] + radius * np.cos(angle_rad),
                    center[1] + radius * np.sin(angle_rad),
                )
            )

            # Inner vertices
            angle_rad += np.pi / 5  # Rotate by 36 degrees (π/5 radians)
            vertices.append(
                (
                    center[0] + inner_radius * np.cos(angle_rad),
                    center[1] + inner_radius * np.sin(angle_rad),
                )
            )

        return vertices

    def get_vertices(self, shape: str, center: tuple, radius: int) -> list:
        """Calculate vertices of the shapes based on the given parameters."""
        if shape == "circle":
            return [
                (center[0] - radius, center[1] - radius),
                (center[0] + radius, center[1] + radius),
            ]
        elif shape == "triangle":
            return [
                (center[0], center[1] - radius),
                (center[0] - radius, center[1] + radius),
                (center[0] + radius, center[1] + radius),
            ]
        elif shape == "square":
            return [
                (center[0] - radius, center[1] - radius),
                (center[0] + radius, center[1] - radius),
                (center[0] + radius, center[1] + radius),
                (center[0] - radius, center[1] + radius),
            ]
        elif shape == "star":
            return self.create_star_vertices(center, radius)
        else:
            raise ValueError(f"Shape {shape} not implemented.")

    def draw_shape(self, shape: str, surface: int, colour: str, jitter: bool = False):
        """Draws a single shape on an image and saves it to the appropriate directory."""
        pixels_x, pixels_y = 512, 512
        image = Image.new("RGB", (pixels_x, pixels_y), color=self.background_colour)
        draw = ImageDraw.Draw(image)

        radius = int(self.get_radius_from_surface(shape, surface))

        # More than that and it's easier to fit a circle than a star
        max_jitter = 124 if jitter else 0

        dist_x = random.randint(-max_jitter, max_jitter)
        dist_y = random.randint(-max_jitter, max_jitter)
        center = (int(pixels_x / 2) + dist_x, int(pixels_y / 2) + dist_y)

        # for bookkeeping
        distance = int(np.sqrt(dist_x**2 + dist_y**2))
        angle = int((np.arctan2(dist_y, dist_x) / np.pi + 1) * 180)

        vertices = self.get_vertices(shape, center, radius)
        if shape == "circle":
            draw.ellipse(vertices, fill=colour)
        else:
            draw.polygon(vertices, fill=colour)

        return image, distance, angle

    def save_image(self, image, shape, surface, dist_from_center, angle, it, path):
        file_path = os.path.join(
            path,
            f"{shape}_{surface}_{dist_from_center}_{angle}_{it}.png",
        )
        image.save(file_path)

    def generate_images(self):
        """Generate all images for training and testing using unified GenerationPlan."""
        import logging

        self.setup_directories()

        for phase, num_images in [("train", self.train_num), ("test", self.test_num)]:
            # Build generation plan for this phase
            plan = GenerationPlan(
                mode="shapes",
                num_repeats=num_images,
                min_surface=self.min_surface,
                max_surface=self.max_surface,
                surface_step=100,
                shapes=self.shapes,
                colours=list(self.colors.keys()),
                task_type=self.task_type,
            ).build()
            
            tasks = plan.get_tasks()
            total_images = len(tasks)
            
            self.log_generation_info(
                f"Generating {total_images} images for {phase} in '{self.output_dir}/{phase}'."
            )
            
            # Execute each task in the plan
            for task in tqdm(tasks):
                shape = task["shape"]
                colour_name = task["colour"]
                surface = task["surface"]
                rep = task["rep"]
                
                # Draw the shape
                colour_code = self.colors[colour_name]
                image, dist, angle = self.draw_shape(shape, surface, colour_code, self.jitter)
                
                # Determine the path based on task type
                if self.task_type == "two_shapes":
                    class_name = shape
                elif self.task_type == "two_colors":
                    class_name = colour_name
                else:  # custom
                    class_name = f"{shape}_{colour_name}"
                
                # Save the image
                self.save_image(
                    image, shape, surface, dist, angle, rep,
                    self.img_paths[f"{phase}_{class_name}"]
                )
