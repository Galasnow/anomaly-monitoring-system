# https://github.com/Taeyoung96/Yolo-to-COCO-format-converter
import logging
from pathlib import Path
import json
from imagesize import imagesize

classes = [
    "background",
    "ship",
]

def create_image_annotation(file_path: Path, width: int, height: int, image_id: int):
    file_path = file_path.name
    image_annotation = {
        "file_name": file_path,
        "height": height,
        "width": width,
        "id": image_id,
    }
    return image_annotation


def create_annotation_from_yolo_format(
        min_x, min_y, width, height, image_id, category_id, annotation_id, segmentation=True
):
    bbox = (float(min_x), float(min_y), float(width), float(height))
    area = width * height
    max_x = min_x + width
    max_y = min_y + height
    if segmentation:
        seg = [[min_x, min_y, max_x, min_y, max_x, max_y, min_x, max_y]]
    else:
        seg = []

    annotation = {
        "id": annotation_id,
        "image_id": image_id,
        "bbox": bbox,
        "area": area,
        "iscrowd": 0,
        "category_id": category_id,
        "segmentation": seg,
    }

    return annotation


def create_annotation_from_yolo_results_format(
        min_x, min_y, width, height, image_id, category_id, conf
):
    bbox = (float(min_x), float(min_y), float(width), float(height))

    annotation = [{
        "image_id": image_id,
        "category_id": category_id,
        "bbox": bbox,
        "score": conf
    }]

    return annotation



def get_images_info_and_annotations(path, input_annotations_path, results=True, box2seg=False):
    path = Path(path)
    annotations = []
    images_annotations = []
    if path.is_dir():
        file_paths = sorted(path.rglob("*.jpg"))
        file_paths += sorted(path.rglob("*.jpeg"))
        file_paths += sorted(path.rglob("*.png"))
        file_paths += sorted(path.rglob("*.tif"))

    else:
        with open(path, "r") as fp:
            read_lines = fp.readlines()
        file_paths = [Path(line.replace("\n", "")) for line in read_lines]

    image_id = 0
    annotation_id = 1  # In COCO dataset format, you must start annotation id with '1'

    for file_path in file_paths:
        # Check how many items have progressed
        logging.info("\rProcessing " + str(image_id) + " ...", end='')

        # Build image annotation, known the image's width and height
        w, h = imagesize.get(str(file_path))
        image_annotation = create_image_annotation(
            file_path=file_path, width=w, height=h, image_id=image_id
        )
        images_annotations.append(image_annotation)

        # label_file_name = f"{file_path.stem}.txt"
        # annotations_path = file_path.parent / label_file_name
        print(f'{file_path}', f'{input_annotations_path}')
        label_file_path = f'{file_path}'.replace('images', 'labels')
        label_file_name = f"{label_file_path}".replace('jpg', 'txt')
        print(label_file_name)
        annotations_path = Path(label_file_name)
        if annotations_path.exists(): # The image may not have any applicable annotation txt file.
            with open(str(annotations_path), "r") as label_file:
                label_read_line = label_file.readlines()

            # yolo format - (class_id, x_center, y_center, width, height)
            # coco format - (annotation_id, x_upper_left, y_upper_left, width, height)
            for line1 in label_read_line:
                label_line = line1
                # category_id = (
                #     int(label_line.split()[0]) + 1
                # )  # you start with annotation id with '1'
                category_id = (
                    1
                )  # you start with annotation id with '1'
                x_center = float(label_line.split()[1])
                y_center = float(label_line.split()[2])
                width = float(label_line.split()[3])
                height = float(label_line.split()[4])

                float_x_center = w * x_center
                float_y_center = h * y_center
                float_width = w * width
                float_height = h * height

                min_x = int(float_x_center - float_width / 2)
                min_y = int(float_y_center - float_height / 2)
                width = int(float_width)
                height = int(float_height)

                if results: #yolo_result to Coco_result (saves confidence)
                    conf = float(label_line.split()[5])
                    annotation = create_annotation_from_yolo_results_format(
                        min_x,
                        min_y,
                        width,
                        height,
                        image_id,
                        category_id,
                        conf
                    )

                else:
                    annotation = create_annotation_from_yolo_format(
                        min_x,
                        min_y,
                        width,
                        height,
                        image_id,
                        category_id,
                        annotation_id,
                        segmentation=box2seg,
                    )
                annotations.append(annotation)
                annotation_id += 1

        image_id += 1  # if you finished annotation work, updates the image id.

    return images_annotations, annotations


def main_write_json(output_path, output_name, input_image_path, input_annotations_path, results=True, box2seg=False):
    output_path = f'{output_path}/{output_name}'

    logging.info("Start!")

    (
        coco_format["images"],
        coco_format["annotations"],
    ) = get_images_info_and_annotations(input_image_path, input_annotations_path, results=results, box2seg=box2seg)

    for index, label in enumerate(classes):
        categories = {
            "supercategory": "Defect",
            "id": index + 1,  # ID starts with '1' .
            "name": label,
        }
        coco_format["categories"].append(categories)

    if results:
        dict_list = []
        for l in coco_format["annotations"]:
            dict_list.append(l[0])
        with open(output_path, "w") as outfile:
            json.dump(dict_list, outfile, indent=4)

    else:
        with open(output_path, "w") as outfile:
            json.dump(coco_format, outfile, indent=4)

    logging.info("Finished!")
# Create the annotations of the ECP dataset (Coco format)
coco_format = {"images": [{}], "categories": [], "annotations": [{}]}

#
# python main.py --path F:\zhongyan\ship_drilling_platform\weizhou\test_compare\GEE_local_0.08%\test_convert --output predict.json --results
# python main.py --path F:\zhongyan\ship_drilling_platform\weizhou\test_compare\GEE_local_0.08%\test_convert --output test.json

if __name__ == "__main__":
    image_path = r'H:\zhongyan\ship_drilling_platform\predict_platform\datasets\images\train'
    label_path = r'H:\zhongyan\ship_drilling_platform\predict_platform\datasets\label\train'
    output_path = r'H:\zhongyan\ship_drilling_platform\predict_platform\datasets\train.json'
    result=False
    (
        coco_format["images"],
        coco_format["annotations"],
    ) = get_images_info_and_annotations(image_path, label_path, result)

    for index, label in enumerate(classes):
        categories = {
            "supercategory": "Defect",
            "id": index + 1,  # ID starts with '1' .
            "name": label,
        }
        coco_format["categories"].append(categories)

    if result:
        dict_list = []
        for l in coco_format["annotations"]:
            dict_list.append(l[0])
        with open(output_path, "w") as outfile:
            str = json.dump(dict_list, outfile, indent=4)

    else:
        with open(output_path, "w") as outfile:
            json.dump(coco_format, outfile, indent=4)

    print("Finished!")

    image_path = r'H:\zhongyan\ship_drilling_platform\predict_platform\datasets\images\val'
    label_path = r'H:\zhongyan\ship_drilling_platform\predict_platform\datasets\label\val'
    output_path = r'H:\zhongyan\ship_drilling_platform\predict_platform\datasets\val.json'
    result = False
    (
        coco_format["images"],
        coco_format["annotations"],
    ) = get_images_info_and_annotations(image_path, label_path, result)

    for index, label in enumerate(classes):
        categories = {
            "supercategory": "Defect",
            "id": index + 1,  # ID starts with '1' .
            "name": label,
        }
        coco_format["categories"].append(categories)

    if result:
        dict_list = []
        for l in coco_format["annotations"]:
            dict_list.append(l[0])
        with open(output_path, "w") as outfile:
            str = json.dump(dict_list, outfile, indent=4)

    else:
        with open(output_path, "w") as outfile:
            json.dump(coco_format, outfile, indent=4)

    print("Finished!")

    image_path = r'H:\zhongyan\ship_drilling_platform\predict_platform\datasets\images\test'
    label_path = r'H:\zhongyan\ship_drilling_platform\predict_platform\datasets\label\test'
    output_path = r'H:\zhongyan\ship_drilling_platform\predict_platform\datasets\test.json'
    result = False
    (
        coco_format["images"],
        coco_format["annotations"],
    ) = get_images_info_and_annotations(image_path, label_path, result)

    for index, label in enumerate(classes):
        categories = {
            "supercategory": "Defect",
            "id": index + 1,  # ID starts with '1' .
            "name": label,
        }
        coco_format["categories"].append(categories)

    if result:
        dict_list = []
        for l in coco_format["annotations"]:
            dict_list.append(l[0])
        with open(output_path, "w") as outfile:
            str = json.dump(dict_list, outfile, indent=4)

    else:
        with open(output_path, "w") as outfile:
            json.dump(coco_format, outfile, indent=4)

    print("Finished!")