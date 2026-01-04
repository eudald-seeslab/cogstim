import tempfile
from unittest.mock import MagicMock, patch
from cogstim.mts_helpers.planner import GenerationPlan
from cogstim.match_to_sample import ImagePrinter


def make_task_list():
    # Return a simple plan-like object with a single task to exercise ImagePrinter
    class SimplePlan:
        def __init__(self):
            self.tasks = [{"n1": 2, "n2": 3, "rep": 0, "equalize": True}]

    return SimplePlan()


def test_image_printer_run_calls_generate_and_recorder():
    plan = make_task_list()
    # Recorder: just record calls
    recorder = MagicMock()

    # Create an args-like object; ImagePrinter uses .output_dir and other attrs
    args = MagicMock()
    args.output_dir = "/tmp"
    args.background_colour = "white"
    args.dot_colour = "black"
    args.min_radius = 5
    args.max_radius = 15
    args.attempts_limit = 100
    args.tolerance = 0.01

    printer = ImagePrinter(args)

    # Patch generate_pair to always return a valid pair and success flag
    mock_pair = (MagicMock(), [], MagicMock(), [])
    with patch('cogstim.match_to_sample.generate_pair', return_value=(mock_pair, True)):
        printer.run(plan, recorder)

    # Recorder.add should be called for each task in the plan
    assert recorder.add.call_count >= 1
