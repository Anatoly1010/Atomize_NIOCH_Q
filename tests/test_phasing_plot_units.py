"""Preview plot coordinates and integration markers share seconds."""

import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest


@pytest.mark.parametrize('name', ['phasing', 'awg_phasing'])
@pytest.mark.parametrize('sample_us', [0.0004, 0.002, 0.01])
def test_preview_plot_and_markers_are_seconds(name, sample_us):
    path = Path(__file__).parents[1] / 'atomize/control_center' / (name + '.py')
    tree = ast.parse(path.read_text())
    worker = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Worker')
    preview = next(node for node in worker.body if isinstance(node, ast.FunctionDef) and node.name == 'dig_on')
    calls = [node for node in ast.walk(preview) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == 'plot_1d'
             and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == 'Dig']
    assert len(calls) == 2
    x = np.arange(8) * sample_us
    i, q = np.arange(8), -np.arange(8)
    for call in calls:
        plot = Mock()
        namespace = dict(general=SimpleNamespace(plot_1d=plot), x_axis=x,
                         data_x=i, data_y=q, t_res=sample_us,
                         win_left=2, win_right=6, int_x=1.0, int_y=-1.0)
        eval(compile(ast.Expression(call), str(path), 'eval'), namespace)
        args, kwargs = plot.call_args
        np.testing.assert_allclose(args[1], x * 1e-6, rtol=1e-12, atol=0)
        assert args[2][0] is i and args[2][1] is q
        assert kwargs['xscale'] == 's'
        np.testing.assert_allclose(kwargs['vline'], x[[2, 6]] * 1e-6, rtol=1e-12, atol=0)
