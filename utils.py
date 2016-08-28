#!/usr/local/bin/python3
#encoding=utf-8

import re
from math import sqrt

sparse_mtx = dict
INF = float('inf')

# 格式化参数数据类型
# 将字符串型数字转换为float
# 字符串保持不变
def param_format(s):
    try:
        float(s)
    except ValueError:
        if s[0] == '[' and s[-1] == ']':
            ptn = re.compile(r'\[(?P<list>.+)\]')
            s = ptn.match(s).group('list').strip().split(' ')
            return [param_format(i) for i in s]
        else:
            return s
    else:
        return float(s)

# 求复数的模
def modulus(cplx):
    return sqrt(cplx.real ** 2 + cplx.imag ** 2)

def ldu():
    pass

if __name__ == '__main__':
    print(param_format('haha'))
    print(param_format('123'))
    print(param_format('2.9'))
    print(param_format('坪-10kV-1'))
    print(modulus(1+2j))
    print(modulus(2j))
    print(modulus(2))
