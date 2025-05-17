from archive.predict import *
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval


def summarize(self, catId=None):
    """
    Compute and display summary metrics for evaluation results.
    Note this functin can *only* be applied on the default parameter setting
    """

    def _summarize(ap=1, iouThr=None, areaRng='all', maxDets=100):
        p = self.params
        iStr = ' {:<18} {} @[ IoU={:<9} | area={:>6s} | maxDets={:>3d} ] = {:0.3f}'
        titleStr = 'Average Precision' if ap == 1 else 'Average Recall'
        typeStr = '(AP)' if ap == 1 else '(AR)'
        iouStr = '{:0.2f}:{:0.2f}'.format(p.iouThrs[0], p.iouThrs[-1]) \
            if iouThr is None else '{:0.2f}'.format(iouThr)

        aind = [i for i, aRng in enumerate(p.areaRngLbl) if aRng == areaRng]
        mind = [i for i, mDet in enumerate(p.maxDets) if mDet == maxDets]

        if ap == 1:
            # dimension of precision: [TxRxKxAxM]
            s = self.eval['precision']
            # IoU
            if iouThr is not None:
                t = np.where(iouThr == p.iouThrs)[0]
                s = s[t]

            # 判断是否传入catId，如果传入就计算指定类别的指标
            if isinstance(catId, int):
                s = s[:, :, catId, aind, mind]
            else:
                s = s[:, :, :, aind, mind]

        else:
            # dimension of recall: [TxKxAxM]
            s = self.eval['recall']
            if iouThr is not None:
                t = np.where(iouThr == p.iouThrs)[0]
                s = s[t]

            # 判断是否传入catId，如果传入就计算指定类别的指标
            if isinstance(catId, int):
                s = s[:, catId, aind, mind]
            else:
                s = s[:, :, aind, mind]

        if len(s[s > -1]) == 0:
            mean_s = -1
        else:
            mean_s = np.mean(s[s > -1])

        logging.info_string = iStr.format(titleStr, typeStr, iouStr, areaRng, maxDets, mean_s)
        return mean_s, logging.info_string

    stats, logging.info_list = [0] * 12, [""] * 12
    stats[0], logging.info_list[0] = _summarize(1)
    stats[1], logging.info_list[1] = _summarize(1, iouThr=.5, maxDets=self.params.maxDets[2])
    stats[2], logging.info_list[2] = _summarize(1, iouThr=.75, maxDets=self.params.maxDets[2])
    stats[3], logging.info_list[3] = _summarize(1, areaRng='small', maxDets=self.params.maxDets[2])
    stats[4], logging.info_list[4] = _summarize(1, areaRng='medium', maxDets=self.params.maxDets[2])
    stats[5], logging.info_list[5] = _summarize(1, areaRng='large', maxDets=self.params.maxDets[2])
    stats[6], logging.info_list[6] = _summarize(0, maxDets=self.params.maxDets[0])
    stats[7], logging.info_list[7] = _summarize(0, maxDets=self.params.maxDets[1])
    stats[8], logging.info_list[8] = _summarize(0, maxDets=self.params.maxDets[2])
    stats[9], logging.info_list[9] = _summarize(0, areaRng='small', maxDets=self.params.maxDets[2])
    stats[10], logging.info_list[10] = _summarize(0, areaRng='medium', maxDets=self.params.maxDets[2])
    stats[11], logging.info_list[11] = _summarize(0, areaRng='large', maxDets=self.params.maxDets[2])

    logging.info_info = "\n".join(logging.info_list)

    if not self.eval:
        raise Exception('Please run accumulate() first')

    return stats, logging.info_info


def write_predict_json():

    pass


def get_coco_map(predict_json_path, test_json_path):

    pass


if __name__ == "__main__":
    predict_json = f'F:/zhongyan/ship_drilling_platform/weizhou/test_compare/GEE_local_0.08%/predict.json'
    test_json = f'F:/zhongyan/ship_drilling_platform/weizhou/test_compare/GEE_local_0.08%/test.json'

    cocoGT = COCO(test_json)
    cocoDT = cocoGT.loadRes(predict_json)

    coco_evaluator = COCOeval(cocoGT, cocoDT, iouType='bbox')
    coco_evaluator.evaluate()
    # accumulate predictions from all images
    coco_evaluator.accumulate()
    coco_evaluator.summarize()

    # calculate COCO info for all classes
    coco_stats, logging.info_coco = summarize(coco_evaluator)
    category_index = [1, 2, 3]
    # calculate voc info for every classes(IoU=0.5)
    logging.info('AP50:')
    voc_map_info_list = []
    for i in range(len(category_index)):
        stats, _ = summarize(coco_evaluator, catId=i)
        voc_map_info_list.append(" {:15}: {}".format(category_index[i], stats[1]))

    logging.info_voc = "\n".join(voc_map_info_list)
    logging.info(logging.info_voc)

    logging.info('mAP:')
    voc_map_info_list = []
    for i in range(len(category_index)):
        stats, _ = summarize(coco_evaluator, catId=i)
        voc_map_info_list.append(" {:15}: {}".format(category_index[i], stats[0]))

    logging.info_voc = "\n".join(voc_map_info_list)
    logging.info(logging.info_voc)