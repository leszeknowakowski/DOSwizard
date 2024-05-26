original_list = ["O1", "O2", "O3", "O4", "O5", "O6", "O7", "O8", "O9", "O10", "O11", "O62", "O63", "O64", "O65",
                 "Co66", "Co67", "Co68", "Co69", "Co70", "Co71", "Co72", "Co73", "Co74", "Co75", "Ce76", "Ce77"]

types_list = ['O', "Co", "Ce"]

# Initialize nested list for partitions
partitioned_lists = [[] for _ in range(len(types_list))]

# Partition the original list
for item in original_list:
    for i, atom in enumerate(types_list):
        if item.startswith(atom):
            partitioned_lists[i].append(item)
            break  # Once found, no need to continue checking other atoms

print(partitioned_lists)
