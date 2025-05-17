"""
使用这个
"""
"""单个"""
# import os
# import csv
# from osgeo import ogr, osr
#
# # 从CSV文件中读取点数据
# def read_points_from_csv(csv_path):
#     points = []
#     with open(csv_path, mode='r') as file:
#         reader = csv.reader(file)
#         next(reader)  # 跳过标题行
#         for row in reader:
#             lon, lat = float(row[1]), float(row[2])  # 假设CSV文件的列顺序是经度和纬度
#             points.append((lon, lat))
#     return points
#
# # 将点转换为矢量文件
# def points_to_shapefile(points, output_shapefile):
#     # 创建新的矢量文件
#     driver = ogr.GetDriverByName('ESRI Shapefile')
#     if os.path.exists(output_shapefile):
#         driver.DeleteDataSource(output_shapefile)
#     data_source = driver.CreateDataSource(output_shapefile)
#     spatial_ref = osr.SpatialReference()
#     spatial_ref.ImportFromEPSG(32649)  # 使用WGS84坐标系（EPSG:4326）#renaijiao 50N xijiao 49N
#
#     # 创建图层
#     layer = data_source.CreateLayer('points', spatial_ref, ogr.wkbPoint)
#     layer_defn = layer.GetLayerDefn()
#
#     # 添加点要素
#     for lon, lat in points:
#         point = ogr.Geometry(ogr.wkbPoint)
#         point.AddPoint(lon, lat)
#         feature = ogr.Feature(layer_defn)
#         feature.SetGeometry(point)
#         layer.CreateFeature(feature)
#         feature = None
#
#     # 释放资源
#     data_source = None
#
# # 输入CSV文件路径和输出矢量文件路径
# csv_path = r'E:\personal file\task\05zhongyan\code\aircraft\pytorch-remote-sensing-master1\pytorch-remote-sensing-master\output\sige_RGB_tiliang\inference\renaijiao\csv\circle/20230831T023529_20230831T025334_T50PLR.csv'
# output_shapefile = r'E:\personal file\task\05zhongyan\code\aircraft\pytorch-remote-sensing-master1\pytorch-remote-sensing-master\output\sige_RGB_tiliang\inference\renaijiao\csv\circle_shp/20230831T023529point.shp'
#
# # 读取CSV文件中的点数据
# points = read_points_from_csv(csv_path)
#
# # 将点数据转换为矢量文件
# points_to_shapefile(points, output_shapefile)
#
# logging.info('Conversion complete.')

"""批量加载csv文件"""
import os
import csv
from osgeo import ogr, osr

# 从CSV文件中读取点数据
def read_points_from_csv(csv_folder):
    all_points = []
    for filename in os.listdir(csv_folder):
        if filename.endswith('.csv'):
            csv_path = os.path.join(csv_folder, filename)
            points = []
            with open(csv_path, mode='r') as file:
                reader = csv.reader(file)
                next(reader)  # 跳过标题行
                for row in reader:
                    name, lon, lat = row[:3]  # 假设CSV文件的列顺序是name, lon, lat
                    lon, lat = float(lon), float(lat)
                    points.append((name, lon, lat))
            all_points.append((filename, points))
    return all_points


def points_to_shapefile(layer_name, points, output_shapefile, target_epsg):

    # 创建新的矢量文件
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(int(target_epsg))  # 使用WGS84坐标系（EPSG:4326）#renaijiao 50N xijiao 49N

    # 创建图层
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    logging.info(layer_defn)
    # 添加点要素
    for id, lon, lat in points:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)
        feature.SetField('ID', id)  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)
        feature = None

    # 释放资源
    data_source = None


# 将点转换为矢量文件
# def points_to_shapefile(csv_filename, points, output_shapefile,target_epsg):
#
#     # 创建新的矢量文件
#     driver = ogr.GetDriverByName('ESRI Shapefile')
#     if os.path.exists(output_shapefile):
#         driver.DeleteDataSource(output_shapefile)
#     data_source = driver.CreateDataSource(output_shapefile)
#     spatial_ref = osr.SpatialReference()
#     spatial_ref.ImportFromEPSG(int(target_epsg))  # 使用WGS84坐标系（EPSG:4326）#renaijiao 50N xijiao 49N
#
#     # 创建图层
#     layer = data_source.CreateLayer(csv_filename, spatial_ref, ogr.wkbPoint)
#     layer_defn = layer.GetLayerDefn()
#
#     # 添加点要素
#     for name, lon, lat in points:
#         point = ogr.Geometry(ogr.wkbPoint)
#         point.AddPoint(lon, lat)
#         feature = ogr.Feature(layer_defn)
#         feature.SetField('Name', name)  # 设置属性字段
#         feature.SetGeometry(point)
#         layer.CreateFeature(feature)
#         feature = None
#
#     # 释放资源
#     data_source = None

# # 输入CSV文件夹路径和输出矢量文件夹路径
# csv_folder = r'E:\personal file\task\05zhongyan\code\aircraft\pytorch-remote-sensing-master1\pytorch-remote-sensing-master\output\RGB_S2_noair_xj_txj_htj\inference\houtenjiao\csv\circle\label/'
# output_folder = r'E:\personal file\task\05zhongyan\code\aircraft\pytorch-remote-sensing-master1\pytorch-remote-sensing-master\output\RGB_S2_noair_xj_txj_htj\inference\houtenjiao\csv\circle_shp\label/'
#
# # 读取CSV文件夹中的所有点数据
# all_points = read_points_from_csv(csv_folder)

# # 将点数据转换为矢量文件并保存到输出文件夹中
# for csv_filename, points in all_points:
#     output_shapefile = os.path.join(output_folder, f'{os.path.splitext(csv_filename)[0]}.shp')
#     points_to_shapefile(csv_filename, points, output_shapefile,target_epsg)

# logging.info('Conversion complete.')



"""
将所有csv文件中的点集合到一个points.shp文件上
"""
# import os
# import csv
# from osgeo import ogr, osr
#
# # 从单个CSV文件中读取点数据
# def read_points_from_csv(csv_path):
#     points = []
#     with open(csv_path, mode='r') as file:
#         reader = csv.reader(file)
#         next(reader)  # 跳过标题行
#         for row in reader:
#             lon, lat = float(row[1]), float(row[2])  # 假设CSV文件的列顺序是经度和纬度
#             points.append((lon, lat))
#     return points
#
# # 从文件夹中加载多个CSV文件
# def load_points_from_folder(folder_path):
#     points = []
#     for filename in os.listdir(folder_path):
#         if filename.endswith('.csv'):
#             csv_path = os.path.join(folder_path, filename)
#             points.extend(read_points_from_csv(csv_path))
#     return points
#
# # 将点转换为矢量文件
# def points_to_shapefile(points, output_shapefile):
#     # 创建新的矢量文件
#     driver = ogr.GetDriverByName('ESRI Shapefile')
#     if os.path.exists(output_shapefile):
#         driver.DeleteDataSource(output_shapefile)
#     data_source = driver.CreateDataSource(output_shapefile)
#     spatial_ref = osr.SpatialReference()
#     spatial_ref.ImportFromEPSG(4326)  # 使用WGS84坐标系（EPSG:4326）
#
#     # 创建图层
#     layer = data_source.CreateLayer('points', spatial_ref, ogr.wkbPoint)
#     layer_defn = layer.GetLayerDefn()
#
#     # 添加点要素
#     for lon, lat in points:
#         point = ogr.Geometry(ogr.wkbPoint)
#         point.AddPoint(lon, lat)
#         feature = ogr.Feature(layer_defn)
#         feature.SetGeometry(point)
#         layer.CreateFeature(feature)
#         feature = None
#
#     # 释放资源
#     data_source = None
#
# # 文件夹路径和输出矢量文件路径
# folder_path = r'E:\personal file\task\05zhongyan\code\aircraft\pytorch-remote-sensing-master1\pytorch-remote-sensing-master\output\sige_RGB_tiliang\inference\xijiao\avg\csv\circle/'
# output_shapefile = r'E:\personal file\task\05zhongyan\code\aircraft\pytorch-remote-sensing-master1\pytorch-remote-sensing-master\output\sige_RGB_tiliang\inference\xijiao\avg\csv\circle_shp/'
#
# # 加载文件夹中所有CSV文件中的点数据
# points = load_points_from_folder(folder_path)
#
# # 将点数据转换为矢量文件
# points_to_shapefile(points, output_shapefile)
#
# logging.info('Conversion complete.')
