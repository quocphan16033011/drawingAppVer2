# from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
# from ..models.Article import Article
# from ..serializers import ArticleSerializer
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import status
import json
<<<<<<< HEAD
import re
import base64


# Create your views here.
# @csrf_exempt
# @api_view(['GET', 'POST'])
# def article_list(request):
#     if request.method == 'GET':
#         # articles = Article.objects.all()
#         # serializer = ArticleSerializer(articles, many=True)
#         # return JsonResponse(serializer.data, safe = False)
#         obj = json.load(open('UIp_FE.json'))
#         return JsonResponse(obj, safe = False)

#     elif request.method == 'POST':
#         data = JSONParser().parse(request)
#         with open("data.json", "w") as inputFile:
#             inputFile.write(str(data))
#         return JsonResponse(data, status=status.HTTP_201_CREATED)
=======
import cv2
import numpy as np
>>>>>>> 9527a0dbeef0ef8209bb54ce62263d94a24ffc79

class ArticleAPIView(APIView):
    
    def get(self, request):
        obj = json.load(open('UIp_FE.json'))
        return JsonResponse(obj, safe = False)
    
    def post(self, request):

        data = JSONParser().parse(request)
<<<<<<< HEAD
        with open("data.json", "w") as inputFile:
            inputFile.write(str(data))
        # return JsonResponse(data, status=status.HTTP_201_CREATED)
        obj = json.load(open('UIp_FE.json'))
        return JsonResponse(obj, safe = False)

        # dataUrlPattern = re.compile('data:image/(png|jpeg);base64,(.*)$')
        # ImageData = request.POST.get('hidden_image_field')
        # ImageData = dataUrlPattern.match(ImageData).group(2)

        # # If none or len 0, means illegal image data
        # if ImageData == None or len(ImageData) == 0:
        #     # PRINT ERROR MESSAGE HERE
        #     pass

        # # Decode the 64 bit string into 32 bit
        # ImageData = base64.b64decode(ImageData)
=======
        # with open("data.json", "w") as resultFile:
        #     json.dump(data, resultFile)

        # =============== GET NODE COORDINATES AND SEGMENTS ============================
        raw_node_coords = data['node_coords']
        segments = data['segments']

        # =============== SCALE AND ROUND NODE COORDINATES =========================
        scale = 4
        node_coords = [[round(x*scale),round(y*scale)] for [x,y] in raw_node_coords]

        # =============== CREATE MATRIX =============================
        matrix = np.zeros((6000, 6000), 'uint8')


        # =============== DRAW SEGMENTS ============================
        for segment in segments:
            start_node = node_coords[segment[0]]
            end_node = node_coords[segment[1]]
            cv2.line(matrix, start_node, end_node,(255,0,0),2)

        # =============== MATRIX PREPROCESSING ==============================
        th, im_th = cv2.threshold(matrix, 127, 255, cv2.THRESH_BINARY_INV)
        # mask used to flood filling
        h, w = im_th.shape[:2] # notice the size needs to be 2 pixels than the image.
        mask = np.zeros((h+2, w+2), np.uint8)
        cv2.floodFill(matrix, mask, (0,0), 255) # floodfill from point (0, 0)
        matrix = cv2.bitwise_not(matrix) # invert foolfilled image

        # =============== FIND CONTOURS =============================
        contours, _ = cv2.findContours(matrix, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        surface_nodes = [] # list of nodes that make a surface
        surface_segments = [] # list of segments that make a surface
        surfaces = [] # list of many surfaces
        surface_names = [] # list of surface names

        # =============== FIND WHICH NODES THAT MAKE A SURFACE =============================
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.009 * cv2.arcLength(contour, True), True)

            #convert array to list
            contour_list = approx.ravel()

            for i in range(0,len(contour_list)):
                if i % 2 == 0:
                    x = contour_list[i]
                    y = contour_list[i+1]
                    min_var = 9999
                    for num_node in range(0,len(node_coords)):
                        delta =  abs(x-node_coords[num_node][0]) + abs(y-node_coords[num_node][1])
                        if delta < min_var:
                            min_var = delta
                            true_node = num_node #node which have the smallest delta is the most correct point
                    surface_nodes.append(true_node)

        # =============== FIND WHICH SEGMENTS THAT MAKE A SURFACE FROM THOSE NODES =============================
            surface_nodes_copy = surface_nodes.copy()
            surface_nodes_copy.append(surface_nodes[0])
            
            for i in range(0, len(surface_nodes)):
                segment1 = [surface_nodes_copy[i], surface_nodes_copy[i+1]]
                segment2 = [surface_nodes_copy[i+1], surface_nodes_copy[i]]
                for j in range(0, len(segments)):
                    if segment1 == segments[j] or segment2 == segments[j]:
                        surface_segments.append(j)
                        break
        
            # if surface_segment != []:
            if len(surface_segments) >= 3:
                surfaces.append(surface_nodes)
                surface_names.append(None)
            surface_nodes = []
            surface_segments = []
            surface_nodes_copy = []
        
        data['surfaces'] = surfaces
        data['surface_names'] = surface_names
        # with open("result.json", "w") as resultFile:
        #     json.dump(data, resultFile)
        return JsonResponse(data, safe = False)

        #     resultFile.write(str(data))
        # obj = json.load(open('UIp_FE.json'))
        # return JsonResponse(obj, safe = False)
>>>>>>> 9527a0dbeef0ef8209bb54ce62263d94a24ffc79
