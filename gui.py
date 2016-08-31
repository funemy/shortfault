from main import main, output, parse_models, get_node_list
from tkinter import ttk, filedialog
import tkinter as tk
import os

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master, padx=15, pady=5)
        self.grid()
        self.create_data_list()
        self.create_entry()
        self.create_result()
        self.create_label()
        self.create_button()

    def create_label(self):
        self.name_label1 = tk.Label(self, text='电气1302  李彦泽')
        self.name_label2 = tk.Label(self, text='U201311800')
        self.name_label1.grid(column=1, row=4)
        self.name_label2.grid(column=1, row=5)

    def create_data_list(self):
        self.generator_label = tk.Label(self, text='发电机参数')
        self.generator_label.grid()
        self.device_info1 = ttk.Treeview(self, show='headings', selectmode='none', column=('设备名','母线', '电压等级', '额定功率', '次暂态电抗'), height=4)
        self.device_info1.column('设备名', width=105, anchor='center')
        self.device_info1.column('母线', width=105, anchor='center')
        self.device_info1.column('电压等级', width=105, anchor='center')
        self.device_info1.column('额定功率', width=105, anchor='center')
        self.device_info1.column('次暂态电抗', width=105, anchor='center')
        self.device_info1.heading('设备名', text='设备名')
        self.device_info1.heading('母线', text='母线')
        self.device_info1.heading('电压等级', text='电压等级')
        self.device_info1.heading('额定功率', text='额定功率(MVA)')
        self.device_info1.heading('次暂态电抗', text='次暂态电抗(标幺)')
        self.device_info1.grid()

        self.transformer_label = tk.Label(self, text='变压器参数')
        self.transformer_label.grid()
        self.device_info2 = ttk.Treeview(self, show='headings', selectmode='none', column=('设备名','绕组数', '母线', '额定功率', '接线方式','短路电压百分比'), height=4)
        self.device_info2.column('设备名', width=90, anchor='center')
        self.device_info2.column('绕组数', width=40, anchor='center')
        self.device_info2.column('母线', width=100, anchor='center')
        self.device_info2.column('额定功率', width=100, anchor='center')
        self.device_info2.column('接线方式', width=100, anchor='center')
        self.device_info2.column('短路电压百分比', width=100, anchor='center')
        self.device_info2.heading('设备名', text='设备名')
        self.device_info2.heading('绕组数', text='绕组数')
        self.device_info2.heading('母线', text='母线')
        self.device_info2.heading('额定功率', text='额定功率')
        self.device_info2.heading('接线方式', text='接线方式')
        self.device_info2.heading('短路电压百分比', text='短路电压百分比')
        self.device_info2.grid()

        self.line_label = tk.Label(self, text='线路参数')
        self.line_label.grid()
        self.device_info3 = ttk.Treeview(self, show='headings', selectmode='none', column=('线路名','母线', 'R1', 'X1', 'R0', 'X0', '距离'), height=4)
        self.device_info3.column('线路名', width=100, anchor='center', stretch=tk.NO)
        self.device_info3.column('母线', width=100, anchor='center', stretch=tk.NO)
        self.device_info3.column('R1', width=65, anchor='center', stretch=tk.NO)
        self.device_info3.column('X1', width=65, anchor='center', stretch=tk.NO)
        self.device_info3.column('R0', width=65, anchor='center', stretch=tk.NO)
        self.device_info3.column('X0', width=65, anchor='center', stretch=tk.NO)
        self.device_info3.column('距离', width=65, anchor='center', stretch=tk.NO)
        self.device_info3.heading('线路名', text='线路名')
        self.device_info3.heading('母线', text='母线')
        self.device_info3.heading('R1', text='R1/km')
        self.device_info3.heading('X1', text='X1/km')
        self.device_info3.heading('R0', text='R0/km')
        self.device_info3.heading('X0', text='X0/km')
        self.device_info3.heading('距离', text='距离(km)')
        self.device_info3.grid()

        self.source_label = tk.Label(self, text='电源参数')
        self.source_label.grid()
        self.device_info4 = ttk.Treeview(self, show='headings', selectmode='none', column=('名称','母线', '电压等级', '额定短路功率'), height=1)
        self.device_info4.column('名称', width=125, anchor='center')
        self.device_info4.column('母线', width=125, anchor='center')
        self.device_info4.column('电压等级', width=125, anchor='center')
        self.device_info4.column('额定短路功率', width=125, anchor='center')
        self.device_info4.heading('名称', text='名称')
        self.device_info4.heading('母线', text='母线')
        self.device_info4.heading('电压等级', text='电压等级')
        self.device_info4.heading('额定短路功率', text='额定短路功率')
        self.device_info4.grid()

    def open_file_dialog(self):
        self.data_file = tk.filedialog.askopenfile()
        self.path = self.data_file.name
        if os.path.split(self.path)[1].split('.')[1] == 'model':
            self.show_device_info()

    def show_device_info(self):
        if hasattr(self, 'iids'):
            self.clear_old_data()
        [objs, nodes] = parse_models(self.path)
        node_list = get_node_list(nodes)
        self.node_list = node_list
        self.iids = {
            'generator': [],
            'transformer': [],
            'line': [],
            'source': [],
            'node': [],
            'result': []
        }
        for o in objs['generator']:
            self.device_info1.config(height=len(objs['generator']))
            tmp = self.device_info1.insert('', tk.END, values=(o.name, o.bus, o.baseKV, o.MVA, o.X1))
            self.iids['generator'].append(tmp)

        for o in objs['transformer']:
            self.device_info2.config(height=len(objs['transformer']))
            if o.windings == 2:
                tmp = self.device_info2.insert('', tk.END, values=(o.name, o.windings, o.buses, o.MVA, o.conn, o.XHL))
                self.iids['transformer'].append(tmp)
            elif o.windings == 3:
                tmp = self.device_info2.insert('', tk.END, values=(o.name, o.windings, o.buses, o.MVA, o.conn, str([o.XHM, o.XHL, o.XML])))
                self.iids['transformer'].append(tmp)

        for o in objs['line']:
            self.device_info3.config(height=len(objs['line']))
            tmp = self.device_info3.insert('', tk.END, values=(o.name, o.buses, o.unit_R1, o.unit_X1, o.unit_R0, o.unit_X0, o.length))
            self.iids['line'].append(tmp)

        for o in objs['source']:
            self.device_info4.config(height=len(objs['source']))
            tmp = self.device_info4.insert('',tk.END, values=(o.name,o.bus,o.baseKV,o.Ss))
            self.iids['source'].append(tmp)

        for i,n in enumerate(node_list):
            tmp = self.select_node.insert('', tk.END, values=(i, n.name))
            self.iids['node'].append(tmp)

    def clear_old_data(self):
        self.device_info1.delete(*self.iids['generator'])
        self.device_info2.delete(*self.iids['transformer'])
        self.device_info3.delete(*self.iids['line'])
        self.device_info4.delete(*self.iids['source'])
        self.select_node.delete(*self.iids['node'])
        self.result.delete(*self.iids['result'])

    def get_result(self):
        self.result.delete(*self.iids['result'])
        iid = self.select_node.focus()
        j = self.select_node.index(iid)
        result = main(self.path, j)
        If_real = round(result['If'].real, 3)
        If_imag = round(result['If'].imag, 3)
        If = str(complex(If_real, If_imag))
        If_named_real = round(result['If_named'].real, 3)
        If_named_imag = round(result['If_named'].imag, 3)
        If_named = str(complex(If_named_real, If_named_imag))
        tmp = self.result.insert('', tk.END, values=(j, self.node_list[j].name, If, If_named))
        self.iids['result'].append(tmp)

    def create_button(self):
        self.select_file = tk.Button(self, text='选择文件', command=self.open_file_dialog)
        self.output = tk.Button(self, text='输出结果', command=self.get_result)
        self.select_file.grid(column=1, row=6)
        self.output.grid(column=1, row=7)

    def create_entry(self):
        self.select_node_label = tk.Label(self, text='选择短路点')
        self.select_node_label.grid(column=1, row=0)
        self.select_node = ttk.Treeview(self, show='headings', column=('编号','节点'), height=4)
        self.select_node.column('编号', width=125, anchor='center')
        self.select_node.column('节点', width=125, anchor='center')
        self.select_node.heading('编号', text='编号')
        self.select_node.heading('节点', text='节点')
        self.select_node.grid(column=1, row=1)

    def create_result(self):
        self.result_label = tk.Label(self, text='计算结果')
        self.result_label.grid(column=1, row=2)
        self.result = ttk.Treeview(self, show='headings', column=('编号', '节点', '短路电流标幺值', '短路电流有名值'), height=2)
        self.result.column('编号', width=50, anchor='center')
        self.result.column('节点', width=125, anchor='center')
        self.result.column('短路电流标幺值', width=125, anchor='center')
        self.result.column('短路电流有名值', width=125, anchor='center')
        self.result.heading('编号', text='编号')
        self.result.heading('节点', text='节点')
        self.result.heading('短路电流标幺值', text='短路电流标幺值')
        self.result.heading('短路电流有名值', text='短路电流有名值(kA)')
        self.result.grid(column=1, row=3)



if __name__ == '__main__':
    app = Application()
    app.master.title('短路计算')
    app.mainloop()
