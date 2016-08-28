#!/usr/local/bin/python3
#encoding=utf-8

from utils import INF

# 电网中设备的基础电气模型
# 所有电气模型均继承自该模型
# 设置所有电气模型的共有属性和方法
# name 电气元件名
# 阻抗的含义在不同元件可能不同
class ElectricModel(object):
    def __init__(self, **params):
        self.name = params['name']
        self.R1 = params['R1'] if 'R1' in params else 0
        self.X1 = params['X1'] if 'X1' in params else 0
        self.R0 = params['R0'] if 'R0' in params else 0
        self.X0 = params['X0'] if 'X0' in params else 0
        self.Z1 = complex(self.R1, self.X1)
        self.Z0 = complex(self.R0, self.X0)
        self.Y1 = 1 / self.Z1 if self.Z1 not in [0, 0j] else INF
        self.Y0 = 1 / self.Z0 if self.Z0 not in [0, 0j] else INF

class Source(ElectricModel):
    def __init__(self, **params):
        params['R1'] = INF
        params['X1'] = 0
        params['R0'] = INF
        params['X0'] = 0
        super().__init__(**params)
        self.bus = params['bus']
        self.baseKV = params['baseKV']

# 输电线路模型
# 阻抗参数代表每公里电阻，单位欧姆
class Line(ElectricModel):
    def __init__(self, **params):
        super().__init__(**params)
        self.bus1 = params['bus1']
        self.bus2 = params['bus2']
        self.buses = [self.bus1, self.bus2]
        self.length = params['length']
        self.unit = params['unit']

# 母线模型
# name 母线名
# objs 表示连接到母线上的对象
class Bus(object):
    def __init__(self, name, objs, baseKV, index):
        self.name = name
        self.objs = [objs]
        self.baseKV = baseKV
        self.index = index

# 发电机模型
# X1为电机次暂态电抗标幺值
class Generator(ElectricModel):
    def __init__(self, **params):
        super().__init__(**params)
        self.bus = params['bus']
        self.baseKV = params['baseKV']
        self.MVA = params['MVA']

# 变压器模型
# 由该类派生出2绕组和3绕组变压器
# conn线圈的接线方式
class Transformer(ElectricModel):
    def __init__(self, **params):
        super().__init__(**params)
        self.MVA = params['MVA']
        self.windings = params['windings']
        self.Xn = params['Xn'] if 'Xn' in params else 0
        self.conn = params['conn']
        self.XHL = params['XHL']
        self.buses = params['buses']
        self.baseKV = params['baseKV']

# 双绕组变压器模型
class T2windings(Transformer):
    def __init__(self, **params):
        super().__init__(**params)

# 三绕组变压器模型
class T3windings(Transformer):
    def __init__(self, **params):
        super().__init__(**params)
        self.XHM = params['XHM']
        self.XML = params['XML']

if __name__ == '__main__':
    pass
