import numpy as np
import torch


def remove_invalid_tensor_by_mask(tensors: torch.Tensor, mask: np.ndarray):
    invalid_tensor_args = []
    # image_range = np.zeros_like(mask, dtype=np.bool_)
    for i, tensor in enumerate(tensors):
        rectangle_range_detect = np.zeros_like(mask, dtype=np.bool)
        x1 = int(tensor[1])
        y1 = int(tensor[2])
        x2 = int(tensor[3])
        y2 = int(tensor[4])
        print(x1, y1, x2, y2)
        # rectangle_range_detect = image_range.copy()
        rectangle_range_detect[y1:y2, x1:x2] = True
        if np.any(np.logical_xor(np.logical_and(rectangle_range_detect, mask), rectangle_range_detect)):
            invalid_tensor_args.append(i)
    if invalid_tensor_args:
        index = torch.as_tensor(np.delete(np.arange(tensors.size(0)), invalid_tensor_args), dtype=torch.int,
                             device=tensors.device)
        tensors = tensors[index]
    # tensors = np.delete(tensors, invalid_tensor_args)
    return tensors

if __name__ == "__main__":
    mask = np.zeros((300, 300), dtype=np.bool)
    mask[100:200, 100:200] = True
    tensors = torch.tensor([[0,10,10,20,20],[0,150,160, 160, 170],[0,250,260, 260, 270]])
    new_tensors = remove_invalid_tensor_by_mask(tensors, mask)
    print(new_tensors)