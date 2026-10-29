"""
Centroid Tracker Module for PC Testing (Giai đoạn 1)
"""

from collections import OrderedDict
import numpy as np


class CentroidTracker:
    def __init__(self, max_disappeared=10, max_distance=60):
        self.next_object_id = 1
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.history = OrderedDict()
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid):
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.history[self.next_object_id] = [centroid]
        self.next_object_id += 1

    def deregister(self, object_id):
        if object_id in self.objects:
            del self.objects[object_id]
        if object_id in self.disappeared:
            del self.disappeared[object_id]
        if object_id in self.history:
            del self.history[object_id]

    def update(self, rects):
        if len(rects) == 0:
            for obj_id in list(self.disappeared.keys()):
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self.deregister(obj_id)
            return self.objects

        input_centroids = np.zeros((len(rects), 2), dtype="int")
        for i, box in enumerate(rects):
            x1, y1, x2, y2 = box[:4]
            cx = int((x1 + x2) / 2.0)
            cy = int((y1 + y2) / 2.0)
            input_centroids[i] = (cx, cy)

        if len(self.objects) == 0:
            for i in range(len(input_centroids)):
                self.register(input_centroids[i])
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            D = np.linalg.norm(np.array(object_centroids)[:, np.newaxis] - input_centroids, axis=2)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue

                if D[row, col] > self.max_distance:
                    continue

                obj_id = object_ids[row]
                new_centroid = input_centroids[col]
                self.objects[obj_id] = new_centroid
                self.disappeared[obj_id] = 0
                self.history[obj_id].append(new_centroid)
                if len(self.history[obj_id]) > 15:
                    self.history[obj_id].pop(0)

                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(0, D.shape[0])).difference(used_rows)
            unused_cols = set(range(0, D.shape[1])).difference(used_cols)

            for row in unused_rows:
                obj_id = object_ids[row]
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self.deregister(obj_id)

            for col in unused_cols:
                self.register(input_centroids[col])

        return self.objects

    def get_trajectory(self, object_id):
        return self.history.get(object_id, [])
