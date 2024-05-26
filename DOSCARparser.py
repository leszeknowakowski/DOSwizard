import os
import numpy as np
import matplotlib.pyplot as plt


class DOSCARparser:

    def __init__(self, file):
        with open(file, 'r') as file:
            lines = file.readlines()
            number_of_atoms = int(lines[0].strip().split()[0])
            info_line_full = lines[5]
            info_line = info_line_full.strip().split()
            stop_nrg, start_nrg, nedos, efermi = [info_line[i] for i in range(4)]
            nedos = int(nedos)
            dos_parts = list(self.splitter(lines[6:], nedos+1))
            lines = []
            total_dos = [line.strip().split() for line in dos_parts[0]]
            self.total_dos_energy = list(map(lambda  sublist: sublist[0], total_dos))
            self.total_dos_alfa = list(map(lambda sublist: sublist[1], total_dos))
            self.total_dos_beta = list(map(lambda sublist: sublist[2], total_dos))
            dos_parts = [list for list in dos_parts[1:]]
            dos_parts = [[line.strip().split() for line in sublist] for sublist in dos_parts]
            self.dos_parts = [[[float(x) for x in list[1:]] for list in sublist] for sublist in dos_parts]

    def splitter(self, list, size):
        for i in range(0, len(list), size):
            yield list[i:i + size - 1]

if __name__ == "__main__":
    doscar = DOSCARparser("D:\\OneDrive - Uniwersytet Jagielloński\\modelowanie DFT\\czasteczki\\O2\\DOSCAR")
    atom = doscar.dos_parts[0]
    alfa = [list[2] for list in atom]
    beta = [list[3] for list in atom]
    nrg = doscar.total_dos_energy

    plt.plot(alfa, nrg)
    plt.plot([-x for x in beta], nrg)
    plt.axis([-1,1,0,300])
    plt.show()
    print('end')