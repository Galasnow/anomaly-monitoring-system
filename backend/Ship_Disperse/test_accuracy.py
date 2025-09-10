import csv
import datetime
import logging
import math

import numpy as np

from config import stem_path
from utils import initial_logging_formatter


class AbnormalEvent:
    def __init__(self, date, event_type, latitude, longitude):
        super(AbnormalEvent, self).__init__()
        self.date: datetime.date = date
        self.event_type: np.intp = event_type
        self.latitude: np.float32 = latitude
        self.longitude: np.float32 = longitude


def read_events_csv_file(events_csv_file):
    csv_reader = csv.reader(open(events_csv_file))
    content = []
    for i, row in enumerate(csv_reader):
        if i == 0:
            continue
        event_type = 1 if row[0] == 'occur' else 0
        event_time = datetime.datetime.strptime(row[1], '%Y-%m-%d')
        latitude = float(row[2])
        longitude = float(row[3])
        event = AbnormalEvent(event_time, event_type, latitude, longitude)
        content.append(event)
    return content


def calculate_distance(event_1: AbnormalEvent, event_2: AbnormalEvent):
    degree_long = 6378137 * 2 * math.pi / 360
    latitude_1 = event_1.latitude
    longitude_1 = event_1.longitude
    latitude_2 = event_2.latitude
    longitude_2 = event_2.longitude
    distance = np.sqrt(np.square(latitude_1 - latitude_2) + np.square(longitude_1 - longitude_2)) * degree_long
    return distance


def judge_event(event_1: AbnormalEvent, event_2: AbnormalEvent):
    if event_1.date == event_2.date and event_1.event_type == event_2.event_type and calculate_distance(event_1, event_2) <= 100:
        return True
    else:
        return False


def calculate_accuracy(events_list_truth: list[AbnormalEvent], events_list_detect: list[AbnormalEvent]):
    sum_truth = len(events_list_truth)
    sum_detect = len(events_list_detect)
    correct_events_detect_number = 0
    for event_truth in events_list_truth:
        match = False
        for event_detect in events_list_detect:
            if judge_event(event_truth, event_detect):
                correct_events_detect_number += 1
                match = True
                break
        if not match:
            print(event_truth.date, event_truth.event_type, event_truth.latitude, event_truth.longitude)
    tp = correct_events_detect_number
    fp = sum_truth - tp
    tn = sum_detect - tp
    return [tp, fp, tn]


if __name__ == "__main__":
    initial_logging_formatter()
    events_detect_csv_file = f'{stem_path}/events_detect.csv'
    events_detect = read_events_csv_file(events_detect_csv_file)
    events_truth_csv_file = f'{stem_path}/events_truth.csv'
    events_truth = read_events_csv_file(events_truth_csv_file)
    # events_detect = [AbnormalEvent(datetime.date(2017, 1, 1), 1, 113.01, 4.01),
    #                  AbnormalEvent(datetime.date(2018, 1, 1), 0, 113.0202, 4.0102),
    #                  AbnormalEvent(datetime.date(2019, 1, 1), 1, 113.0102, 4.0102),
    #                  ]
    # events_truth = [AbnormalEvent(datetime.date(2017, 1, 1), 1, 113.0102, 4.0102),
    #                 AbnormalEvent(datetime.date(2018, 1, 1), 1, 113.0202, 4.0102),
    #                 AbnormalEvent(datetime.date(2019, 1, 2), 1, 113.0102, 4.0102),
    #                 ]
    # logging.info(calculate_distance(events_detect[0], events_truth[0]))
    # logging.info(judge_event(events_detect[0], events_truth[0]))
    logging.info(calculate_accuracy(events_truth, events_detect))
