#!/usr/local/bin/python3
#encoding=utf-8

import re
from utils import param_format
from model import Line, Bus, Generator, T2windings, T3windings, Source

# 读取建模model文件
# 将建模语句按对象类型分类
def read_model_file(path):
    line_states = []
    generator_states = []
    transformer_states = []
    source_states = []
    with open(path, 'r') as model_file:
        models = model_file.readlines()
        for m in models:
            m = m.strip()
            if m:
                statement = m.split(',')
                type_pattern = re.compile(r'[nN]ew\s(?P<type>[^\.]+)\.')
                model_type = type_pattern.match(m).group('type')
                if model_type in ['line', 'Line']:
                    line_states.append(m)
                elif model_type in ['generator', 'Generator']:
                    generator_states.append(m)
                elif model_type in ['transformer', 'Transformer']:
                    transformer_states.append(m)
                elif model_type in ['source', 'Source']:
                    source_states.append(m)
    return dict({
        'line_states': line_states,
        'generator_states': generator_states,
        'transformer_states': transformer_states,
        'source_states': source_states
    })


# 按声明对象的类型解析声明语句
# 返回实例化后的对象
# 将实例化后的结果存入model_dict方便后续建模
def parse_models(path):
    model_dict = {'line': [],
                  'generator': [],
                  'transformer': [],
                  'source': []}
    statements = read_model_file(path)
    for s in statements['line_states']:
        model_dict['line'].append(parse_line(s))
    for s in statements['generator_states']:
        model_dict['generator'].append(parse_generator(s))
    for s in statements['transformer_states']:
        model_dict['transformer'].append(parse_transformer(s))
    for s in statements['source_states']:
        model_dict['source'].append(parse_source(s))

    bus_set = init_bus(model_dict)
    return (model_dict, bus_set)

# 装饰器
# 在解析前将参数进行拆分
# 拆分后的语言保存在param_dict中
# 所有参数都要经过param_format函数进行类型转换
# 数字字符串统一转换为float，字符串不变
def split_param(fn):
    def _deco(s):
        param_str = [x.strip() for x in s.split(',')]
        param_str[0] = 'name=' + param_str[0].split('.')[1]
        param_dict = dict([tuple(x.split('=')) for x in param_str])
        for k in param_dict:
            param_dict[k] = param_format(param_dict[k])
        return fn(param_dict)
    return _deco

# 解析电源建模语句
@split_param
def parse_source(source_params):
    return Source(**source_params)

# 解析线路建模语句
@split_param
def parse_line(line_params):
    return Line(**line_params)

# 解析发电机建模语句
@split_param
def parse_generator(generator_params):
    return Generator(**generator_params)

# 解析变压器建模语句
@split_param
def parse_transformer(transformer_params):
    transformer_params['windings'] = int(transformer_params['windings'])
    if transformer_params['windings'] is 2:
        return T2windings(**transformer_params)
    elif transformer_params['windings'] is 3:
        return T3windings(**transformer_params)

# 接受完成建模后的对象字典model_dict
# 遍历对象，实例化bus对象
# 将母线存储在字典中，所有电路元件存储在所连母线的obj属性中
# 母线及故障计算时的节点

# 节点优化策略，从电路的外端逐渐向中心编号
def init_bus(model_dict):
    bus_set = {}
    for i in model_dict['generator']:
        if i.bus not in bus_set:
            bus_set[i.bus] = Bus(i.bus, i, i.baseKV, len(bus_set))
        else:
            bus_set[i.bus].objs.append(i)
    for i in model_dict['source']:
        if i.bus not in bus_set:
            bus_set[i.bus] = Bus(i.bus, i, i.baseKV, len(bus_set))
        else:
            bus_set[i.bus].objs.append(i)
    for i in model_dict['transformer']:
        for k,b in enumerate(i.buses):
            if b not in bus_set:
                bus_set[b] = Bus(b, i, i.baseKV[k], len(bus_set))
            else:
                bus_set[b].objs.append(i)
    init_line_bus(model_dict['line'], bus_set)
    return bus_set

# 从line对象中提取母线
# 因为line对象需要从两侧从中间提取，从而确定母线电压等级
# 需要递归调用
# 用于比算例更复杂的电网
def init_line_bus(line_models, bus_set):
    count = 0
    for i in line_models:
        if i.bus1 not in bus_set and i.bus2 in bus_set:
            bus_set[i.bus1] = Bus(i.bus1, i, bus_set[i.bus2].baseKV, len(bus_set))
            bus_set[i.bus2].objs.append(i)
        elif i.bus2 not in bus_set and i.bus1 in bus_set:
            bus_set[i.bus2] = Bus(i.bus2, i, bus_set[i.bus1].baseKV, len(bus_set))
            bus_set[i.bus1].objs.append(i)
        elif i.bus1 in bus_set and i.bus2 in bus_set:
            if i not in bus_set[i.bus1].objs:
                bus_set[i.bus1].objs.append(i)
            if i not in bus_set[i.bus2].objs:
                bus_set[i.bus2].objs.append(i)
            count += 1
    if count == len(line_models):
        return
    else:
        init_line_bus(line_models, bus_set)
    return


model_path = 'test.model'
[objs, bus_set] = parse_models(model_path)

if __name__ == '__main__':
    a = parse_models('test.model')
    print(a[1]['岳-35kV'].objs[0].__dict__)
    for i in a[1]:
        print(a[1][i].__dict__)
