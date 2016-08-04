#!/usr/local/bin/python3
#encoding=utf-8

# 电网中设备的基础电气模型
# 所有电气模型均继承自该模型
# 设置所有电气模型的共有属性和方法
# name 电气元件名
class ElectricModel(object):
    def __init__(self, name, baseKV, R, X, C):
        self._name = name
        self._baseKV = baseKV
        self._R = R
        self._X = X
        self._C = C

# 输电线路模型
class Line(ElectricModel):
    def __init__(self, R, X, C, length):
        super().__init__(self, R, X, C)
        self._length = length

# 母线模型
# name 母线名
# conn 母线所连馈线的list
class Bus():
    def __init__(self, name, conn):
        self._name = name
        if type(conn) is Line:
            self.conn = [conn]
        elif type(conn) is list:
            self.conn = conn
        else:
            raise TypeError("Bus对象只能与Line对象相接")

# 变压器模型
# 由该类派生出2绕组和3绕组变压器
class Transformer(ElectricModel):
    def __init__(self):
        pass

# 发电机模型
class Generator(ElectricModel):
    def __init__(self):
        pass

# 两绕组变压器模型
class T2windings(Transformer):
    def __init__(self):
        pass

# 三绕组变压器模型
class T3windings(Transformer):
    def __init__(self):
        pass
