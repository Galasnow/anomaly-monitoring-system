import os

#ML Parameters
BATCH_SIZE_TRAIN = 16
BATCH_SIZE_VAL = 1
early_stop = 6
NUMBER_OF_WORKERS = 0
RESIZE_TO = 1024 #1024
EPOCHS = 32
LR = 1.8e-4
MOMENTUM = 0.8
# DETECTION_THRESHOLD = 0.7
DETECTION_THRESHOLD = 0.3
NUM_CLASSES = 2#3

CLASSES = ['background', 'ship']

#Save frequencies
SAVE_PLOTS_EPOCH = 1

NMS_THRESHOLD = 0.01

support_file_list = ['jpg', 'png', 'jp2', 'tif', 'tiff']
# 定义扩大倍数
EXPANSION_FACTOR = 1.5  # 1.0表示不扩大，大于1.0表示扩大

root_path = os.getcwd()
train_image_dir = r'./datasets/images/train'
train_label_dir = r'./datasets/labels/train'
val_image_dir = r'./datasets/images/val'
val_label_dir = r'./datasets/labels/val'
train_anno_path = r'./datasets/train.json'
val_anno_path = r'./datasets/val.json'

test_image_dir = r'./datasets/images/test'
test_anno_path = r'./datasets/test.json'

save_dir = r'./run'

# modify_type = 'GEE_global_2%_nlm'
place = 'malaysia_wenlai'
# place = 'functionality_test'
# stem_path = f'F:/zhongyan/ship_drilling_platform/{place}/test_compare/{modify_type}'
# stem_path = f'H:/zhongyan/ship_drilling_platform/predict_platform/datasets/test_set/{place}'
# stem_path = 'D:/zhongyan/functionality_test/'
stem_path = f'{root_path}/process'
# stem_path = 'H:/zhongyan/gee_download_wushi/Sentinel-1'
# stem_path = 'H:/zhongyan/gee_download_wenlai/test'
output_stem_path = f'{stem_path}/output'
# input_path = f'{stem_path}/grid_images'
ground_truth_path = f'{stem_path}/labels_t'
output_path = f'{output_stem_path}/predict'
output_preview_path = f'{output_stem_path}/preview'
output_grid_label_path = f'{output_stem_path}/labels/grid'
output_combine_label_path = f'{output_stem_path}/labels/combine'
original_image_path = f'{stem_path}/original_images'
modified_label_path = f'{output_stem_path}/labels/modified'
# input_shp_path = 'F:/zhongyan/gee_download_weizhou/weizhou_oil_field_range/weizhou_oil_field.shp'
# input_shp_path = 'H:/zhongyan/gee_download_wenlai/malaysia_range_for_test/malaysia_range_for_test.shp'
# input_shp_path = 'H:/zhongyan/gee_download_wenlai/test/malaysia_brunei_range_final/malaysia_brunei_range_final.shp'
input_shp_path = os.path.abspath('./process/greater_zhanghua_windfarm/greater_zhanghua_windfarm.shp')

output_shp_path_stable = f'{output_stem_path}/shapefile_stable'
output_shp_path_occur = f'{output_stem_path}/shapefile_occur'
output_shp_path_disappear = f'{output_stem_path}/shapefile_disappear'
output_shp_path_occur_and_disappear = f'{output_stem_path}/shapefile_occur_and_disappear'
output_shp_path_by_day = f'{output_stem_path}/by_day'

temp_result_path = ''

import torch
#Device configuration
DEVICE = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')