import re

class CreateLabel:
    def __init__(self):
        pass
    def create_label(self, orbital_up, orbital_down, atom_no_up, atom_no_down):
        def number_range(lst):
            '''returns a string representing a range of numbers, eg. 1-4,5,10-11'''
            result = []
            i = 0
            while i < len(lst):
                start = lst[i]
                end = start
                while i + 1 < len(lst) and lst[i + 1] - lst[i] == 1:
                    end = lst[i + 1]
                    i += 1
                if start == end:
                    result.append(str(start))
                else:
                    result.append(f"{start}-{end}")
                i += 1
            string_result = ",".join(result) + ","
            return " many atoms!," if len(string_result) > 20 else string_result

        orblst = sorted(set(orbital_down + orbital_up))
        atomlst = sorted(set(atom_no_down + atom_no_up), key=lambda x: (
        re.match(r'\D+', x).group(), int(re.match(r'\d+', x[len(re.match(r'\D+', x).group()):]).group())))
        lst = [orblst, atomlst]

        count_orb_in_label = [lst[0].count(o) for o in ['s', 'p', 'd', 'f']]

        orblbl = []
        if count_orb_in_label[0] == 1:
            orblbl.append('s')
        if count_orb_in_label[1] == 3:
            orblbl.append('p')
        else:
            orblbl.extend([orb for orb in lst[0] if orb.startswith('p')])
        if count_orb_in_label[2] == 5:
            orblbl.append('d')
        else:
            orblbl.extend([orb for orb in lst[0] if orb.startswith('d')])
        if count_orb_in_label[3] == 7:
            orblbl.append('f')
        else:
            orblbl.extend([orb for orb in lst[0] if orb.startswith('f')])

        atomlst_group = {}
        for atom in lst[1]:
            key = re.match(r'\D+', atom).group()
            if key in atomlst_group:
                atomlst_group[key].append(int(re.match(r'\d+', atom[len(key):]).group()))
            else:
                atomlst_group[key] = [int(re.match(r'\d+', atom[len(key):]).group())]

        atomlbl = [f"{key}{number_range(sorted(values))}" for key, values in atomlst_group.items()]

        merged_label = atomlbl + orblbl
        return " ".join(merged_label)


# Example usage:
orbital_up = ['s', 'p1', 'p2', 'p3']
orbital_down = ['s', 'd1', 'd2', 'd3', 'd4', 'd5']
atom_no_up = ['C1', 'O2', 'N3']
atom_no_down = ['H1', 'H2', 'H3', 'H4']

print(create_label(orbital_up, orbital_down, atom_no_up, atom_no_down))