#!/usr/local/bin/python3
#encoding=utf-8

from utils import VB_table
from parse import objs
from parse import bus_set as nodes
from model import T3windings


# 基准功率100兆瓦
SB = 100

# 对所有对象的参数进行标幺化
def standardize(obj_dict, node_set):
    for i in obj_dict['generator']:
        i.std_Z1 = i.Z1 * (i.baseKV ** 2 / i.MVA) * (SB / VB_table[i.baseKV] ** 2)
        i.std_Z0 = i.Z0 * (i.baseKV ** 2 / i.MVA) * (SB / VB_table[i.baseKV] ** 2)
        i.std_Y1 = 1 / i.std_Z1 if i.std_Z1 not in [0, 0j] else 0
        i.std_Y0 = 1 / i.std_Z0 if i.std_Z0 not in [0, 0j] else 0
        # print(i.__dict__)
    for i in obj_dict['transformer']:
        if i.windings is 2:
            vb = VB_table[nodes[i.buses[0]].baseKV]
            i.std_Z1 = complex(0, (i.XHL / 100) * (i.baseKV[0] ** 2 / i.MVA) * (SB / vb ** 2))
            i.std_Y1 = 1 / i.std_Z1
            # print(i.__dict__)
        elif i.windings is 3:
            vbh = VB_table[i.baseKV[0]]
            vbm = VB_table[i.baseKV[1]]
            vbl = VB_table[i.baseKV[2]]
            i.std_Z1H = complex(0, (i.XH / 100) * (i.baseKV[0] ** 2 / i.MVA[0]) * (SB / vbh ** 2))
            i.std_Z1M = complex(0, (i.XM / 100) * (i.baseKV[1] ** 2 / i.MVA[1]) * (SB / vbm ** 2))
            i.std_Z1L = complex(0, (i.XL / 100) * (i.baseKV[2] ** 2 / i.MVA[2]) * (SB / vbl ** 2))
            # 星-三角变换
            i.std_Z1HL = i.std_Z1H + i.std_Z1L + i.std_Z1H * i.std_Z1L / i.std_Z1M
            i.std_Z1HM = i.std_Z1H + i.std_Z1M + i.std_Z1H * i.std_Z1M / i.std_Z1L
            i.std_Z1ML = i.std_Z1M + i.std_Z1L + i.std_Z1M * i.std_Z1L / i.std_Z1H
            i.std_Y1HL = 1 / i.std_Z1HL
            i.std_Y1HM = 1 / i.std_Z1HM
            i.std_Y1ML = 1 / i.std_Z1ML
            # 方便计算自导纳，与对应求取自导纳的节点对应
            i.std_Y1 = [i.std_Y1HL + i.std_Y1HM, i.std_Y1HM + i.std_Y1ML, i.std_Y1HL + i.std_Y1ML]
            # 方便计算互导纳，分别对应 中低/高低/高中 三边的导纳
            i.std_Y1_delta = [i.std_Y1ML, i.std_Y1HL, i.std_Y1HM]
    for i in obj_dict['line']:
        base = node_set[i.bus1].baseKV
        i.std_Z1 = i.Z1 * (SB / VB_table[base] ** 2)
        i.std_Z0 = i.Z0 * (SB / VB_table[base] ** 2)
        i.std_Y1 = 1 / i.std_Z1
        i.std_Y0 = 1 / i.std_Z0
        # print(i.__dict__)

# 形成导纳矩阵
def form_Ymtx(node_set):
    # 系数矩阵存储优化策略
    # 一维使用list，即数组存储每一行
    # 二维使用dict，即哈希表，将节点编号记为索引，导纳作为值
    # 这种策略优于链表，因为哈希表的查询时间复杂度为o(1)
    ymtx = [{} for i in range(len(node_set))]
    node_list = [None] * len(node_set)
    # 第一次循环，形成自导纳
    # 并生成node_list，即按序号排序的数组
    for node in node_set:
        node = node_set[node]
        node_list[node.index] = node
        yii = 0
        for obj in node.objs:
            if type(obj) is not T3windings:
                yii += obj.std_Y1
            else:
                yindex = obj.baseKV.index(node.baseKV)
                yii += obj.std_Y1[yindex]
        ymtx[node.index][node.index] = yii

    # 第二次循环，补充完互导纳
    # 存储优化策略，只储存下半矩阵
    for k,node in enumerate(node_list):
        obj_set1 = set(node.objs)
        for i in range(k):
            obj_set2 = set(node_list[i].objs)
            obj_ij = obj_set1.intersection(obj_set2)
            yij = 0
            for obj in obj_ij:
                if type(obj) is not T3windings:
                    yij -= obj.std_Y1
                else:
                    side_index1 = obj.baseKV.index(node.baseKV)
                    side_index2 = obj.baseKV.index(node_list[i].baseKV)
                    yindex = abs(side_index1 + side_index2 - 3)
                    yij -= obj.std_Y1_delta[yindex]
            if yij:
                ymtx[k][i] = yij
    return ymtx


if __name__ == '__main__':
    standardize(objs, nodes)
    m = form_Ymtx(nodes)
    for i in m:
        print(i)
