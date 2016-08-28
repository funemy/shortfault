#!/usr/local/bin/python3
#encoding=utf-8

import re
from utils import param_format
from model import Line, Bus, Generator, T2windings, T3windings, Source

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
    return bus_set

def split_param(fn):
    def _deco(s):
        param_str = [x.strip() for x in s.split(',')]
        param_str[0] = 'name=' + param_str[0].split('.')[1]
        param_dict = dict([tuple(x.split('=')) for x in param_str])
        for k in param_dict:
            param_dict[k] = param_format(param_dict[k])
        return fn(param_dict)
    return _deco

@split_param
def parse_source(source_params):
    return Source(**source_params)

@split_param
def parse_line(line_params):
    return Line(**line_params)

@split_param
def parse_generator(generator_params):
    return Generator(**generator_params)

@split_param
def parse_transformer(transformer_params):
    transformer_params['windings'] = int(transformer_params['windings'])
    if transformer_params['windings'] is 2:
        return T2windings(**transformer_params)
    elif transformer_params['windings'] is 3:
        return T3windings(**transformer_params)

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



if __name__ == '__main__':
    a = parse_models('test.model')
    for i in a:
        print(a[i].__dict__)
