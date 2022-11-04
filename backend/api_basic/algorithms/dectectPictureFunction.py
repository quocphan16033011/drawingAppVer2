import os
from django.conf import settings
import cv2
import numpy as np
import math
import itertools
import time
from scipy.spatial import cKDTree

# from .detectAreaFunction import detectArea


def region_of_interest(img):
    canny_img = cv2.Canny(img, 127, 255)
    contours, hierarchy = cv2.findContours(canny_img,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    height, width = canny_img.shape
    min_x, min_y = width, height
    max_x = max_y = 0
    for contour in contours:
        (x,y,w,h) = cv2.boundingRect(contour)
        min_x, max_x = min(x, min_x), max(x+w, max_x)
        min_y, max_y = min(y, min_y), max(y+h, max_y)
    if max_x - min_x > 0 and max_y - min_y > 0:
        min_x, min_y = min_x - 3, min_y - 3
        max_x, max_y = max_x + 3, max_y + 3
        img = img[min_y:max_y, min_x:max_x]
    return img

def get_end_points(points, img):
    node_coords = []    
    for point in points:
        x = point[0]
        y = point[1]
        n = 0        
        n += img[y - 1,x]
        n += img[y - 1,x - 1]
        n += img[y - 1,x + 1]
        n += img[y,x - 1]    
        n += img[y,x + 1]    
        n += img[y + 1,x]    
        n += img[y + 1,x - 1]
        n += img[y + 1,x + 1]
        n /= 255        
        if n == 1:
            node_coords.append(point.tolist())
    return node_coords

def flat_segment_list(segment):
    segment = [segment[0][0],segment[0][1], segment[1][0], segment[1][1]]
    return segment

def dot_product(v1, v2):
    return sum((a*b) for a, b in zip(v1, v2))

def get_length(v):
    return math.sqrt(dot_product(v, v))

def get_angle(segment1, segment2):
    v1 = flat_segment_list(segment1)
    v2 = flat_segment_list(segment2)
    return math.degrees(math.acos(dot_product(v1, v2) / (get_length(v1) * get_length(v2))))

def get_precision(bin_inv, bin_line):
    conjs = (bin_inv + bin_line)
    n_agree = np.sum(conjs == 2)
    n_line = np.sum(bin_line == 1)
    precision = n_agree / n_line
    return precision

def filter_overlap(segment_dict):
    segment_combinations = itertools.combinations(segment_dict,2)
    for couple_segment in segment_combinations:
        segment1, segment2 = couple_segment
        try:
            segment1_start_node, segment1_end_node = segment_dict[segment1]['line']
            if segment1_start_node in segment_dict[segment2]['line'] or segment1_end_node in segment_dict[segment2]['line']:
                    angle = get_angle(segment_dict[segment1]['line'], segment_dict[segment2]['line'])
                    if angle < 10:
                        if segment_dict[segment1]['precision'] > segment_dict[segment2]['precision']:
                            del segment_dict[segment2]
                        else:
                            del segment_dict[segment1]
        except:
            pass
    return segment_dict

def get_distance(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def det(a, b):
    return a[0] * b[1] - a[1] * b[0]

def find_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])
    div = det(xdiff, ydiff)
    if div != 0:
        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        length1 = get_distance(line1[0], line1[1])
        length2 = get_distance(line2[0], line2[1])
        if get_distance([x,y],line1[0]) < length1 and get_distance([x,y],line1[1]) < length1 and get_distance([x,y],line2[0]) < length2 and get_distance([x,y],line2[1]) < length2:
            return [round(x), round(y)]

def detectLine(line, intersections):
    intersections.sort()
    listLine = []
    if(len(intersections) !=0):
        listLine.append([line[0], intersections[0]])
        if len(intersections) >2:
            for i in range(0, len(intersections)-2):
                listLine.append([intersections[i], intersections[i]+1])
            listLine.append([line[1], intersections[len(intersections)-1]])
        elif(len(intersections) == 2):
            listLine.append([intersections[0], intersections[1]])
            listLine.append([line[1], intersections[len(intersections)-1]])
        elif (len(intersections) == 1):
            listLine.append([line[1], intersections[len(intersections)-1]])
    return listLine

def detectPicture(file_name):
    data = {
        "num_nodes": 0,
        "num_segments": 0,
        "node_coords": [],
        "node_names": [],
        "segments": [],
        "segment_names": [],
        "surfaces": [],
        "surface_names": [],
        "nodal_loads": [],
        "segment_loads": []
    }
    read_path = os.path.join(settings.MEDIA_ROOT,file_name)
    img = cv2.imread(read_path, cv2.IMREAD_GRAYSCALE)
    img = region_of_interest(img)
    bin_inv = cv2.bitwise_not(img) # flip image colors
    bin_inv = cv2.dilate(bin_inv, np.ones((1, 1)))

    # ========================== FIND END POINTS =====================================
    th, img = cv2.threshold(img, 127, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY_INV)
    img = cv2.ximgproc.thinning(img)
    points = cv2.findNonZero(img)
    points = np.squeeze(points)
    node_coords = get_end_points(points, img)

    # =========================== FIND SEGMENTS ========================================
    time_start = time.time()

    segment_dict = {}
    count = 0
    lines = itertools.combinations(node_coords,2) # create all possible lines
    bin_inv = bin_inv / 255
    for line in lines: # loop through each line
        bin_line = np.zeros_like(bin_inv) # create a matrix to draw the line in
        start, end = line # grab endpoints
        cv2.line(bin_line, start, end, color=1, thickness=1) # draw line
        precision = get_precision(bin_inv, bin_line)
        if precision > .9:
            segment_dict[count] = {"line": line, "precision": precision}
            count += 1
    segment_dict = filter_overlap(segment_dict)
    print(time.time()-time_start)

    # =========================== FIND INTERSECTIONS =================================
    intersections = []
    segment_combinations = itertools.combinations(segment_dict,2)
    for couple_segment in segment_combinations:
        segment1_id, segment2_id = couple_segment
        segment1 = segment_dict[segment1_id]['line']
        segment2 = segment_dict[segment2_id]['line']
        intersection_point = find_intersection(segment1, segment2)
        if intersection_point != None and intersection_point not in node_coords:
            intersections.append(intersection_point)
    node_coords = node_coords + intersections
    data["node_coords"] = node_coords
    data["num_nodes"] = len(data["node_coords"])
    data["node_names"] = [None]*data["num_nodes"]
        

    # =========================== ADD SEGMENTS TO DATA ===============================
    segments = []
    kdtree = cKDTree(data["node_coords"])
    for segment in segment_dict:
        start_node, end_node = segment_dict[segment]["line"]
        distances, ids = kdtree.query([start_node, end_node])
        if distances[0] < 1e-5 and distances[1] < 1e-5:
            segments.append(ids.tolist())
    data["segments"] = segments
    data["num_segments"] = len(data["segments"])
    data["segment_names"] = [None]*data["num_segments"]
    # data = detectArea(data)
    # ============================ REMOVE TO CENTER CANVAS ===========================
    node_coords = []
    for node_coord in data["node_coords"]:
        node_coords.append([node_coord[0]+100, node_coord[1]+100])
    data["node_coords"] = node_coords
    return data
