from huffmancoding import *


freqs=FrequencyTable([5,4,3,2,1])
#print(freqs)
#freqs.increment(0)
#print(freqs)
#freqs._check_symbol(0)
#freqs.set(4,10)
print(freqs)
tree=freqs.build_code_tree()
print(tree)
print(tree.get_code(0))