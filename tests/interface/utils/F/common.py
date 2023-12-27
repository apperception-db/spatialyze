from spatialyze.predicate import GenSqlVisitor, objects, camera
from spatialyze.utils.F import *
from spatialyze.utils.F.custom_fn import custom_fn


o = objects[0]
o1 = objects[1]
o2 = objects[2]
o3 = objects[3]
o4 = objects[4]

c = camera

gen = GenSqlVisitor()