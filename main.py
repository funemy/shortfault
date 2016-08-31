#!/usr/local/bin/python3
#encoding=utf-8

from utils import VB_table, ldu, cplx_round
from utils import zf, SB
from parse import parse_models
from model import T3windings, T2windings, Line
from math import sqrt
import xlwt



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
            vb = VB_table[node_set[i.buses[0]].baseKV]
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
    for i in obj_dict['source']:
        i.std_Z1 = complex(0, SB / i.Ss)
        i.std_Y1 = 1 / i.std_Z1

# 形成导纳矩阵
def form_Ymtx(node_set, node_list):
    # 系数矩阵存储优化策略
    # 一维使用list，即数组存储每一行
    # 二维使用dict，即哈希表，将节点编号记为索引，导纳作为值
    # 这种策略优于链表，因为哈希表的查询时间复杂度为o(1)
    ymtx = [{} for i in range(len(node_set))]
    # 第一次循环，形成自导纳
    # 并生成node_list，即按序号排序的数组
    for node in node_set:
        node = node_set[node]
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

# 形成固定列的z阵
# j代表列数
# 若不填写则输出完整z阵
def form_Zmtx(ymtx, j):
    length = len(ymtx)
    [d, u] = ldu(ymtx)
    f = [None for i in range(length)]
    h = [None for i in range(length)]
    zmtx_j = [None for i in range(length)]
    for i in range(length):
        if i < j:
            f[i] = 0
        elif i == j:
            f[i] = 1
        else:
            fi = 0
            for k in range(j, i):
                fi -= u[k][i]*f[k]
            f[i] = fi
        h[i] = f[i] / d[i][i]
    for i in range(length)[::-1]:
        zi_j = h[i]
        for k in range(i+1, length):
            zi_j -= u[i][k] * zmtx_j[k]
        zmtx_j[i] = zi_j
    return zmtx_j

# 计算故障点短路电流
# 以及非故障点的电压电流
def cal_short_fault(zmtx, ymtx, nodes, node_list, objs, j):
    length = len(zmtx)
    If = 1 / (zmtx[j])
    V = [None for i in range(length)]
    for i in range(length):
        if i != j:
            V[i] = 1 - (zmtx[i] / (zmtx[j] + zf))
        else:
            V[i] = 0
    # 计算电压有名值
    V_named = [None for i in range(length)]
    for i in range(length):
        V_named[i] = V[i] * node_list[i].baseKV
    # print(V_named)
    # 计算每条线路电流
    I = {}
    for line in objs['line']:
        V1 = V[nodes[line.bus1].index]
        V2 = V[nodes[line.bus2].index]
        I[line.name] = (V1 - V2) / line.std_Z1
    I_named = {}
    for i in I:
        for o in objs['line']:
            if o.name == i:
                base = nodes[o.bus1].baseKV
        I_named[i] = I[i] * SB / (sqrt(3) * base)
    # print(I)
    # 计算短路点电流有名值
    If_named = If * SB / (sqrt(3) * node_list[j].baseKV)

    # 计算变压器绕组电流
    # 还有问题
    It = {}
    for t in objs['transformer']:
        tmpI = 0
        ratio = 1
        for l in nodes[t.buses[0]].objs:
            if type(l) not in [T2windings, T3windings]:
                tmpI += I[l.name]
            elif l is t:
                continue
            else:
                if type(l.MVA) is list:
                    mva = l.MVA[0]
                else:
                    mva = l.MVA
                if type(t.MVA) is list:
                    tmva = t.MVA[0]
                else:
                    tmva = t.MVA
                ratio *= tmva / (tmva + mva)
        It[t.name] = tmpI * ratio
    It_named = {}
    for i in It:
        It_named[i] = []
        for t in objs['transformer']:
            if t.name == i:
                for v in t.baseKV:
                    if v != 37:
                        It_named[i].append(It[i] * SB / (sqrt(3) * v))
                    else:
                        It_named[i].append(0)
    return {
        'V_std': V,
        'V_named': V_named,
        'I': I,
        'I_named': I_named,
        'If': If,
        'If_named': If_named,
        'It': It,
        'It_named': It_named
    }

def get_node_list(nodes):
    # 形成以编号为顺序的节点list
    node_list = [None] * len(nodes)
    for node in nodes:
        node = nodes[node]
        node_list[node.index] = node
    return node_list

def output(nodes, node_list, objs, ymtx, zmtx, j, result):
    wb = xlwt.Workbook()
    ws = wb.add_sheet('短路计算结果')
    row_num = 0
    ws.write(row_num, 0, '短路节点序号')
    ws.write(row_num, 1, '短路节点名称')
    ws.write(row_num, 2, '短路电流标幺值')
    ws.write(row_num, 3, '短路电流有名值')

    row_num += 1
    ws.write(row_num, 0, j)
    ws.write(row_num, 1, node_list[j].name)
    ws.write(row_num, 2, str(cplx_round(result['If'], 3)))
    ws.write(row_num, 3, str(cplx_round(result['If_named'], 3)))

    row_num += 2
    ws.write(row_num, 0, 'Y矩阵')
    row_num += 1
    for row in ymtx:
        for i in row:
            item = cplx_round(row[i], 3)
            ws.write(row_num, i, str(item))
        row_num += 1

    row_num += 1
    ws.write(row_num, 0, 'Z矩阵第%d列' % j)
    row_num += 1
    for i,v in enumerate(zmtx):
        ws.write(row_num, i, str(cplx_round(v,3)))

    row_num += 2
    ws.write(row_num, 0, '')

    row_num += 2
    ws.write(row_num, 0, '各节点电压')
    row_num += 1
    ws.write(row_num, 0, '编号')
    ws.write(row_num, 1, '节点名称')
    ws.write(row_num, 2, '电压标幺值')
    ws.write(row_num, 3, '电压基准值')
    row_num += 1
    for i,n in enumerate(node_list):
        ws.write(row_num, 0, i)
        ws.write(row_num, 1, node_list[i].name)
        ws.write(row_num, 2, str(cplx_round(result['V_std'][i], 3)))
        ws.write(row_num, 3, str(cplx_round(result['V_named'][i], 3)))
        row_num += 1

    row_num +=1
    ws.write(row_num, 0, '各支路电流')
    row_num +=1
    ws.write(row_num, 0, '线路')
    row_num +=1
    ws.write(row_num, 0, '线路名称')
    ws.write(row_num, 1, '电流标幺值')
    ws.write(row_num, 2, '电流有名值')
    row_num += 1
    for i in result['I']:
        ws.write(row_num, 0, i)
        ws.write(row_num, 1, str(cplx_round(result['I'][i], 3)))
        ws.write(row_num, 2, str(cplx_round(result['I_named'][i], 3)))
        row_num += 1

    row_num += 1
    ws.write(row_num, 0, '变压器')
    row_num += 1
    ws.write(row_num, 0, '变压器名称')
    ws.write(row_num, 1, '高压侧标幺值')
    ws.write(row_num, 2, '高压侧有名值')
    ws.write(row_num, 3, '中压侧标幺值')
    ws.write(row_num, 4, '中压侧有名值')
    ws.write(row_num, 5, '低压侧标幺值')
    ws.write(row_num, 6, '低压侧有名值')
    row_num += 1
    for i in result['It_named']:
        ws.write(row_num, 0, i)
        ws.write(row_num, 1, str(cplx_round(result['It'][i], 3)))
        ws.write(row_num, 2, str(cplx_round(result['It_named'][i][0], 3)))
        if len(result['It_named'][i]) == 3:
            ws.write(row_num, 3, str(0))
            ws.write(row_num, 4, str(cplx_round(result['It_named'][i][1], 3)))
            ws.write(row_num, 5, str(cplx_round(result['It'][i], 3)))
            ws.write(row_num, 6, str(cplx_round(result['It_named'][i][2], 3)))
        elif len(result['It_named'][i]) == 2:
            ws.write(row_num, 3, "")
            ws.write(row_num, 4, "")
            ws.write(row_num, 5, str(cplx_round(result['It'][i], 3)))
            ws.write(row_num, 6, str(cplx_round(result['It_named'][i][1], 3)))
        row_num += 1

    wb.save('output.xls')

def main(path, j):
    [objs, nodes] = parse_models(path)
    node_list = get_node_list(nodes)
    standardize(objs, nodes)
    ymtx = form_Ymtx(nodes, node_list)
    zmtx = form_Zmtx(ymtx, j)
    result = cal_short_fault(zmtx, ymtx, nodes, node_list, objs, j)
    output(nodes, node_list, objs, ymtx, zmtx, j, result)
    return result


if __name__ == '__main__':
    # 测试用矩阵
    test_m = [
        {0:-2.6515j},
        {1:-2.6515j},
        {2:-5.9645j},
        {3:29.4985-78.7109j},
        {4:1.8111-9.0697j, 0:-1.8182j, 1:-1.8182j},
        {5:1.9389-7.6602j, 2:2.1636j},
        {6:-2.9136j, 5:-0.1731j, 2:3.0867j},
        {7:30.5842-74.5765j, 3:-26.9942+63.8333j, 4:-1.8111+5.4333j},
        {8:6.2222-15.8572j, 7:-1.7790+5.3099j, 5:-1.9389+5.6697j, 3:-2.5044+4.8775j}
    ]
    main('test.model', 3)
