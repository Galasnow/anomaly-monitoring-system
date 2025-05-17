from archive.predict import *
import matplotlib.pyplot as plt

def accumulate_size(modify_type):
    labels_path = f'F:/zhongyan/ship_drilling_platform/weizhou/test_compare/{modify_type}/predict_label'
    labels_names = natsorted(os.listdir(labels_path))
    gts_list = np.zeros([1, 5])
    for i, label_name in enumerate(labels_names):
        with open(f'{labels_path}/{label_name}', 'r') as label_file:
            # logging.info(np.array(label_file.read().split()))
            content = np.array(label_file.read().split()).reshape(-1, 6).astype(float)
            content[..., 0].astype(int)
            gts_r = content[..., 0: -1]
            # gts_r[..., 1:] = yolo2number(image_shape, content[..., 1:])
            gts_list = np.concatenate((gts_list, gts_r), axis=0)
    gts_list = np.delete(gts_list, [0, 0, 0, 0, 0], axis=0)
    # logging.info(f'gts_list = {gts_list}')
    # logging.info(f'gts_list.shape = {gts_list.shape}')
    gts_sort = divide_annotations(np.array(gts_list), category_list, sorted=True)
    # logging.info(f'gts_sort = {gts_sort}')
    # logging.info(f'gts_sort.shape = {gts_sort.shape}')
    platform_array = gts_sort[1]
    ship_array = gts_sort[0]
    platform_size = platform_array[:, -2] * platform_array[:, -1] * image_shape[0] * image_shape[
        1] * resolution_size * resolution_size
    ship_size = ship_array[:, -2] * ship_array[:, -1] * image_shape[0] * image_shape[
        1] * resolution_size * resolution_size

    logging.info(f'platform_size = {platform_size}')
    return platform_size, ship_size

if __name__ == "__main__":
    image_shape = (1080, 1080)
    category_list = [1, 2]
    resolution_size = 10

    platform_size_1, ship_size_1 = accumulate_size('GEE_global_2%')
    platform_size_2, ship_size_2 = accumulate_size('GEE_global_2%_lee')
    platform_size_3, ship_size_3 = accumulate_size('GEE_global_2%_nlm')
    fig, ax = plt.subplots()
    colors = ['lightgreen', 'lightblue', 'lightyellow'] * 2
    u = plt.boxplot([platform_size_1, platform_size_2, platform_size_3, ship_size_1, ship_size_2, ship_size_3], widths=0.25, patch_artist=True, showmeans=True, meanline=True)
    for patch, color in zip(u['boxes'], colors):
        patch.set_facecolor(color)

    ax.legend([u['boxes'][0], u['boxes'][1],u['boxes'][2], u['boxes'][3], u['boxes'][4],u['boxes'][5]], ['platform_2%', 'platform_2%_lee', 'platform_2%_nlm', 'ship_2%', 'ship_2%_lee', 'ship_2%_nlm'])
    ax.ticklabel_format(style='sci', scilimits=(-1, 2), axis='y')
    ax.set_ylabel('m\u00b2')
    plt.title('Size of BBox')
    plt.show()

    fig, ax = plt.subplots()
    colors = ['lightgreen', 'lightblue', 'lightyellow']
    u = plt.boxplot([ship_size_1, ship_size_2, ship_size_3],
                    widths=0.25, patch_artist=True, showmeans=True, meanline=True)
    for patch, color in zip(u['boxes'], colors):
        patch.set_facecolor(color)

    ax.legend([u['boxes'][0], u['boxes'][1], u['boxes'][2]], ['ship_2%', 'ship_2%_lee', 'ship_2%_nlm'])
    ax.ticklabel_format(style='sci', scilimits=(-1, 2), axis='y')
    ax.set_ylabel('m\u00b2')
    plt.title('Size of BBox')
    plt.show()