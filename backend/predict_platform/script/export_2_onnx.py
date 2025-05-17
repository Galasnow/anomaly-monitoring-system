import onnx
# import onnxoptimizer
from onnxsim import simplify

from model import create_model
from config import NUM_CLASSES, DEVICE, save_dir

from util.labels import *

def export_onnx(prefix_path, input_size=(1024, 1024)):
    model = create_model(num_classes=NUM_CLASSES)
    model_path = f'{prefix_path}/best_model.pth'
    model.load_state_dict(torch.load(model_path, map_location=DEVICE, weights_only=True))
    model.eval()
    example_data = torch.randn(1, 3, input_size[0], input_size[1])
    torch.onnx.export(model, example_data, f'{prefix_path}/faster_rcnn.onnx', opset_version=17)


# def optimize_onnx(prefix_path):
#     model_path = f'{prefix_path}/faster_rcnn.onnx'
#     model = onnx.load(model_path)
#     new_model = onnxoptimizer.optimize(model)
#     onnx.save(new_model, f'{prefix_path}/faster_rcnn_optimize.onnx')


def simplify_onnx(prefix_path):
    model_path = f'{prefix_path}/faster_rcnn.onnx'
    model = onnx.load(model_path)
    model_simp, check = simplify(model)
    assert check, "Simplified ONNX model could not be validated"
    onnx.save(model_simp, f'{prefix_path}/faster_rcnn_simplify.onnx')


if __name__ == "__main__":
    prefix_path = f'.{save_dir}/2025-03-29_10-59-38'
    input_size = (1024, 1024)
    export_onnx(prefix_path, input_size)
    # optimize_onnx(prefix_path)
    simplify_onnx(prefix_path)
