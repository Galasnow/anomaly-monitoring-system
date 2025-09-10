from config import input_path, output_path, output_grid_label_path, output_combine_label_path, modified_label_path, \
    output_shp_path_stable, output_shp_path_occur, output_shp_path_disappear, output_shp_path_occur_and_disappear, \
    output_shp_path_by_day
from utils import create_folder

if __name__ == "__main__":
    create_folder(input_path)
    create_folder(output_path)
    create_folder(output_grid_label_path)
    create_folder(output_combine_label_path)
    create_folder(modified_label_path)
    create_folder(output_shp_path_stable)
    create_folder(output_shp_path_occur)
    create_folder(output_shp_path_disappear)
    create_folder(output_shp_path_occur_and_disappear)
    create_folder(output_shp_path_by_day)