import unittest
import numpy as np
from util.labels import yolo2number

class TestMoransI(unittest.TestCase):
    CASES = {
        'test_1': {'box': np.array(
                       [0.1, 0,1, 0.9, 0.9], dtype=np.float32),
                   'image_shape': [200, 200],
        'result': [20, 20, 180, 180]},
        'test_2': {'box': np.array(
                       [0.2, 0,1, 0.9, 0.9], dtype=np.float32),
                   'image_shape': [200, 200],
        'result': [40, 20, 180, 180]},

    }

    def test_case(self):
        for case in self.CASES.values():
            # global Moran's I
            np.array_equal(
                yolo2number(case['image_shape'], case['box']),
                case['result'])


if __name__ == '__main__':
    unittest.main()

