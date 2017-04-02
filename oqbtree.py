import numpy as np
"""A Hierarchical Adaptive Meshmesh indexing tranlation and rotation space.

Combining octree (for indexing tranlation space) and quad-tree (for indexing sphere) to indexing all configurations of two rigid body.
        ^
       Z|1--+
        |_______
       /|      /|3-++
      / | +++ / |
     /__|___7/  |
 +-+5|  |____|__|__Y__>
     | /0--- | /2-+-
     |/      |/
     |_______|
   X/4+--    6++-
   v       
   

"""


# This dictionary is used by the findBranch function, to return the correct branch index
DIRLOOKUP = {'+++':7, '-++':3, '--+':1, '+-+':5, '++-':6, '-+-':2, '---':0, '+--':4}
#### End Globals ####
E_HIGH = 100.0
DIST_CUTOFF = 2.5 ** 2
HIGH = np.array([E_HIGH,E_HIGH,E_HIGH,E_HIGH,E_HIGH,E_HIGH,E_HIGH])

class conf:
    def __init__(self, node_idx, position=None, vector=None, angle = None,value=HIGH):
        self.idx = node_idx
        self.position = position
        self.vector = vector
        self.angle = angle
        self.value = value

class Node:
    """Node.

    """
    def __init__(self,node_idx=None, centre=None, size=None, leaf_num=None):
        self.error = 100.0
        self.centre = centre
        self.size = size
        self.isLeafNode = True
        self.idx = node_idx
        self.leaf_num = leaf_num
        # children store region
        self.children = [None for i in range(self.leaf_num)] # the branches should have order
        # grids store mesh grids
        self.grids = []
        self.testgrid = []
        self.parent = None

class Bitree:
    """Bittree

    """
    def __init__(self, node_idx, centre, size, position, direction):
        self.idx = node_idx
        self.position = position
        self.direct = direction
        self.centre = centre
        self.centre = size
        self.root = Node(node_idx, centre, size, leaf_num=2)
        self.root.grids.append(conf(node_idx+'C0',self.position, self.direct, centre - size))
        #self.root.gridsa.append(conf(node_idx+'C0',self.position, self.direct, centre, 0.0))
        self.root.grids.append(conf(node_idx+'C1',self.position, self.direct, centre + size))
        self.allnodes = {}
        self.allgrids = {}
        self.iterateGrid()
        self.iterateNode()
        self.subdivideNode(self.root)

    def grepGrid(self, angle):
        for grid in self.allgrids.values():
            delta = (grid.angle - angle) ** 2
            if delta < 0.0001:
                return grid
        return None

    def subdivideNode(self, parent):
        parent.isLeafNode = False
        size = parent.size/2.0
        centre = (parent.centre - size, parent.centre + size )
        for i in range(2):
            child = Node(parent.idx+str(i),centre[i], size, 2)
            angles = [centre[i]-size, centre[i]+size]
            for j in range(2):
                grid = self.grepGrid(angles[j])
                if not grid:
                    grid = conf(child.idx + 'C%d'%(j), self.position, self.direct, angles[j])
                child.grids.append(grid)
                child.parent = parent
            parent.children[i] = child
        self.iterateGrid()
        self.iterateNode()
        parent.testgrid.append(self.grepGrid(parent.centre))

    def fill(self, conf_idx, value):
        """fill conf after generation 
        """
        self.addNode(conf_idx)
        if conf_idx in self.allgrids:
            if conf_idx == self.root.idx + 'C0':
                self.root.grids[1].value = value
            self.allgrids[conf_idx].value = value
        else:
            raise Exception("Con't fill conf %s\n"%(conf_idx))

    def addNode(self,node_idx):
        node_idx = node_idx.split('C')[0]
        pre_idx, idxs = node_idx.split('N')
        pre_idx += 'N' 
        for i in idxs:
            pre_idx +=  str(i)
            if pre_idx not in self.allnodes:
                self.subdivideNode(self.allnodes[pre_idx[:-1]])

    def interpolation(self, angle, node=None, neighbors=None):
        if node is None: node = self.root
        if neighbors is None:neighbors = self.findNeighbors(node, angle)
        v1 = neighbors[0].value
        v2 = neighbors[1].value
        w1 = angle - neighbors[0].angle
        w2 = neighbors[1].angle -angle
        value = (v1 * w1 + v2 * w2)/(w1 + w2)
        return value

    def findNeighbors(self, node, angle):
        _neighbor = None
        if node == None:
            return None  
        elif node.isLeafNode:
            _neighbor = (node.grids[0], node.grids[1])
            return _neighbor
        else:
            child = self.findChild(node, angle)
            return self.findNeighbors(node.children[child],angle)
            
    def findChild(self, node, angle):
        child_idx = None
        if angle < node.centre: 
            child_idx = 0
        else:
            child_idx = 1
        return  child_idx

    def iterateGrid(self):
        self.allgrids = {}
        for conf in self._iterateGrid_help(self.root):
            if conf.idx not in self.allgrids:
                self.allgrids[conf.idx] = conf
        del self.allgrids[self.root.idx + 'C1']
        
    def _iterateGrid_help(self, node):
        """iterate all conf, not unique

        """
        for conf in node.grids:
            if conf != None:yield conf
        for child in node.children:
            if child == None:continue
            for c in self._iterateGrid_help(child):
                yield c 

    def iterateNode(self):
        self.allnodes = {}
        self.leafNodes = {}
        for n in self._iterateNode_help(self.root):
            if n.idx not in self.allnodes:
                self.allnodes[n.idx] = n
            if n.isLeafNode is True:
                self.leafNodes[n.idx] = n 

    def _iterateNode_help(self, node):
        if node != None:
            yield node 
        for child in node.children:
            if child == None: continue
            for n in self._iterateNode_help(child):
                yield  n
            
class Quadtree:
    """QuadTree to index sphere

    """
    def __init__(self, com, node_idx):
        """init 6 grids and 8 triangles in root node.
        
        com is centre of mass.
        grid order is like '4', triangles child is anti o' clock from (1,1,1)
        """
        self.position = com
        self.idx = node_idx
        self.root = Node(node_idx, centre=com, size = 4*np.pi, leaf_num= 8)
        self.root.directs = np.array([[0., 0., 1.], #North
                                      [1., 0., 0.],[0., 1., 0.],[-1., 0., 0.],[0.,-1.,0.], # equator
                                      [0., 0., -1.0] # South
                                       ])
        for i in range(6):
            self.root.grids.append(Bitree(node_idx + 'N%d'%(i), 0.0, np.pi, 
                                          self.position, self.root.directs[i]))
        self.allnodes = {}
        self.allgrids = {}
        self.iterateGrid()
        self.iterateNode()
        _grid_idx = [ [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1], 
                      [5, 1, 2], [5, 2, 3], [5, 3, 4], [5, 4, 1]
                    ]
        for i in range(8):
            #three grids id in vertex A, B , C
            A, B, C = _grid_idx[i]
            idx = self.idx + str(i)
            directs = np.array([self.root.directs[A], 
                self.root.directs[B], 
                self.root.directs[C]])
            centre = np.sum(directs, axis=0)
            centre /= np.linalg.norm(centre)
            area = self._triang_area(directs[0], directs[1], directs[2])
            child = Node(idx, centre, area, leaf_num=4)
            child.parent = self.root
            Agrid = self.grepGrid(directs[0])
            Bgrid = self.grepGrid(directs[1])
            Cgrid = self.grepGrid(directs[2])
            child.grids = [Agrid,Bgrid,Cgrid ]
            child.directs = directs
            key = self.findChild(self.root, centre)
            self.root.children[key] = child 
        self.root.isLeafNode = False
        self.iterateGrid()
        self.iterateNode()
        for child in self.root.children:
            self.subdivideNode(child)
                
    def grepGrid(self, vector):
        """check if a grid(bitree) exists by distance of two vector
        
        """
        for grid in self.allgrids.values():
            delta = np.linalg.norm(grid.direct - vector)
            if delta < 0.001:
                return grid
        return None

    def subdivideNode(self, parent):
        parent.isLeafNode = False
        grids = parent.grids
        directs = parent.directs
        directs = np.array([directs[0],directs[1],directs[2],
                            (directs[0] + directs[1]),
                            directs[1] + directs[2],
                            directs[2] + directs[0]
                             ])
        #       0
        #     3   5
        #   1   4   2
        for i in range(3,6):
            directs[i] = directs[i]/np.linalg.norm(directs[i])
            grid = self.grepGrid(directs[i])
            if not grid:
                grid = Bitree(parent.idx + 'N%d'%(i), 0.0, np.pi, 
                              self.position, directs[i])
            grids.append(grid)
            parent.testgrid.append(grid)
        
        _grid_idx = [ [0,3,5], [3,1,4], [5,4,2], [3,4,5]]
        for i in range(4):
            A,B,C = _grid_idx[i]
            idx = parent.idx + str(i)
            child_directs = np.array([directs[A], directs[B], directs[C]])
            centre = np.sum(child_directs, axis=0)        
            centre /= np.linalg.norm(centre)
            area = self._sphere_triang_area(directs[A], directs[B], directs[C])
            child = Node(idx, centre, area, leaf_num=4)
            child.directs = child_directs
            child.grids = [grids[A],grids[B],grids[C]]
            child.parent = parent
            parent.children[i] = child
        self.iterateGrid()
        self.iterateNode()


    def fill(self, conf_idx, value):
        """fill conf after generation 
        """
        self.addNode(conf_idx)
        grid_idx = conf_idx.split('N')[0] + 'N' + conf_idx.split('N')[1][0]
        if grid_idx in self.allgrids:
            self.allgrids[grid_idx].fill(conf_idx, value)
        else:
            raise Exception("Con't fill conf %s\n"%(conf_idx))

    def addNode(self, conf_idx):
        node_idx = conf_idx.split('N')[0]
        pre_idx, idxs = node_idx.split('R')
        pre_idx += 'R' 
        for i in idxs:
            pre_idx +=   str(i)
            if pre_idx not in self.allnodes:
                self.subdivideNode(self.allnodes[pre_idx[:-1]])

    def interpolation(self, vector, angle, node=None, neighbors=None, sphere=False):
        if node is None: node = self.root
        if neighbors is None:neighbors = self.findNeighbors(node, vector)
        v1 = neighbors[0].interpolation(angle)
        v2 = neighbors[1].interpolation(angle)
        v3 = neighbors[2].interpolation(angle)
        if sphere:
            w1 = self._sphere_triang_area(neighbors[1].direct,neighbors[2].direct,vector)
            w2 = self._sphere_triang_area(neighbors[0].direct,neighbors[2].direct,vector)
            w3 = self._sphere_triang_area(neighbors[1].direct,neighbors[0].direct,vector)
        else:
            w1 = self._triang_area(neighbors[1].direct,neighbors[2].direct,vector)
            w2 = self._triang_area(neighbors[0].direct,neighbors[2].direct,vector)
            w3 = self._triang_area(neighbors[1].direct,neighbors[0].direct,vector)
        value = (v1 * w1 + v2 * w2 + v3 * w3)/(w1 + w2 + w3)
        return value

    def findNeighbors(self, node, vector):
        _neighbor = None
        if node == None:
            return None  
        elif node.isLeafNode:
            _neighbor = (node.grids[0], node.grids[1], node.grids[2])
            return _neighbor
        else:
            child = self.findChild(node, vector)
            return self.findNeighbors(node.children[child],vector)
            
    def findChild(self, node, vector):
        if node is self.root:
            key = ''
            for i in range(3):
                if vector[i] >= 0:
                    key += '+'
                else:
                    key += '-'
            return DIRLOOKUP[key]
        else:
            # three middle point of triangle is the directs of 4 th children
            mids = node.children[3].directs
            solve = np.linalg.solve(mids.T, vector)
            if solve[0] < 0: return 2
            if solve[1] < 0: return 0
            if solve[2] < 0: return 1
            return 3

    def iterateGrid(self):
        self.allgrids = {}
        for conf in self._iterateGrid_help(self.root):
            if conf.idx not in self.allgrids:
                self.allgrids[conf.idx] = conf
        
    def _iterateGrid_help(self, node):
        """iterate all conf, not unique

        """
        for conf in node.grids:
            if conf != None:yield conf
        for child in node.children:
            if child == None: continue
            for c in self._iterateGrid_help(child):
                yield c 

    def iterateNode(self):
        self.allnodes = {}
        self.leafNodes = {}
        for n in self._iterateNode_help(self.root):
            if n.idx not in self.allnodes:
                self.allnodes[n.idx] = n
            if n.isLeafNode is True:
                self.leafNodes[n.idx] = n 

    def _iterateNode_help(self, node):
        if node != None :
            yield node 
        for child in node.children:
            if child == None: continue
            for n in self._iterateNode_help(child):
                yield  n
    
    def _vet2ang(self, x, y):
        """get the angle of 2 vector

        """
        lx = np.sqrt(np.dot(x,x))
        ly = np.sqrt(np.dot(y,y))
        cos_angle = np.dot(x,y)/(lx * ly)
        angle = np.arccos(cos_angle)
        return angle

    def _sphere_triang_area(self, OA,OB,OC, r = 1):
        """get area of spherical triangle from 3 vectors (O point to surface).

        """
        a = self._vet2ang(OB,OC)
        b = self._vet2ang(OA,OC)
        c = self._vet2ang(OA,OB)
        if a == 0.0 or b == 0.0 or c == 0.0:
            return 0.0
        cosA = (np.cos(a) - np.cos(b)*np.cos(c))/(np.sin(b)*np.sin(c))
        cosB = (np.cos(b) - np.cos(a)*np.cos(c))/(np.sin(a)*np.sin(c))
        cosC = (np.cos(c) - np.cos(b)*np.cos(a))/(np.sin(b)*np.sin(a))
        E = np.arccos(cosA) + np.arccos(cosB) + np.arccos(cosC) - np.pi
        return (E * r**2)
    def _triang_area(self, OA,OB,OC):
        """treat sphere_triangle as triangle.

        """
        return 0.5 * np.linalg.norm( np.cross( OB-OA, OC-OA ) )



class Octree:
    """QuadTree to index sphere

    """
    def __init__(self, centre=(0.,0.,0.), size=12.0, symmetry=None):
        """init octree by symmetry, and add 
        
        com is centre of mass.
        node_idx will be like "T123R123N123C123"
        T:translocation, R:rotation, R:normal, C:configuration
        """
        self.allnodes = {}
        self.allgrids = {}
        self.sym = symmetry #used by self.subdivideNode()
        self.root = Node('wtr_wtrT', centre=centre, size = 12.0, leaf_num= 8)
        self.subdivideNode(self.root)
        if self.sym == 1:
            for key,i in DIRLOOKUP.items():
                if key[2]=='-':
                    self.root.children[i]=None
        elif self.sym == 2:
            for key,i in DIRLOOKUP.items():
                if key[2]=='-' or key[1]=='-':
                    self.root.children[i]=None
        elif self.sym == 3:
            for key,i in DIRLOOKUP.items():
                if key[2]=='-' or key[1]=='-' or key[0]=='-':
                    self.root.children[i]=None
        else:
            if self.sym != None:
                raise Exception("translation symmetry has only 1,2 and 3.")
        #regeneration nodes and grids list for deleting Node.
        self.iterateGrid()
        self.iterateNode()
        for child in self.root.children:
            if child != None:
                self.subdivideNode(child)
        
    def grepGrid(self, vector):
        """check if a grid(bitree) exists by distance of two vector
        print(self.root.children)
        
        """
        for grid in self.allgrids.values():
            delta = np.linalg.norm(grid.position - vector)
            if delta < 0.001:
                return grid
        return None

    def _grid_positions(self,node,offset=None):
        if offset==None:offset = node.size
        offsets = np.array([[-offset,-offset,-offset],
                            [-offset,-offset,+offset],
                            [-offset,+offset,-offset],
                            [-offset,+offset,+offset],
                            [+offset,-offset,-offset],
                            [+offset,-offset,+offset],
                            [+offset,+offset,-offset],
                            [+offset,+offset,+offset]
                            ])
        return node.centre + offsets

    def _newCentre(self,node):
        offset = node.size/2.0
        return self._grid_positions(node,offset)
        
    def subdivideNode(self, parent):
        parent.isLeafNode = False
        newCentre = self._newCentre(parent)
        grid_positions = self._grid_positions(parent)
        for i in range(8):
            child = Node(parent.idx + str(i), centre=newCentre[i], 
                         size = parent.size/2.0, leaf_num= 8)
            for j, pos in enumerate(self._grid_positions(child)):
                grid = self.grepGrid(pos)
                if not grid:
                    grid = Quadtree(pos, child.idx+'R%d'%(j))
                child.grids.append(grid)
            parent.children[i] = child
            child.parent = parent
        self.iterateGrid()
        self.iterateNode()
        parent.testgrid.append(self.grepGrid(parent.centre))

    def fill(self, conf_idx, value):
        """fill conf after generation 
        """
        self.addNode(conf_idx)
        grid_idx = conf_idx.split('R')[0] + 'R' + conf_idx.split('R')[1][0]
        if grid_idx in self.allgrids:
            self.allgrids[grid_idx].fill(conf_idx, value)
        else:
            raise  Exception("Con't fill conf %s\n"%(conf_idx))

    def addNode(self,node_idx):
        node_idx = node_idx.split('R')[0]
        pre_idx, idxs = node_idx.split('T')
        pre_idx += 'T' 
        for i in idxs:
            pre_idx += str(i)
            if pre_idx not in self.allnodes:
                self.subdivideNode(self.allnodes[pre_idx[:-1]])

    def interpolation(self, position, vector, angle, node=None, neighbors=None):
        if np.dot(position, position) < DIST_CUTOFF:
            return np.array([100.0,100.0,100.0,100.0,100.0,100.0,100.0])
        if np.dot(position, position) >  144.0:
            return np.array([0.0,0.0,0.0,0.0,0.0,0.0,0.0])
        if node is None: node = self.root
        if neighbors is None: neighbors = self.findNeighbors(node, position)
        ndim = len(position)        
        v = np.zeros((8,ndim + 7))
        for i in range(8):
            v[i,0:ndim] = neighbors[i].position
            v[i,ndim:] = neighbors[i].interpolation(vector, angle)
        for dim in range(ndim):
            vtx_delta = 2**(ndim - dim - 1)
            for vtx in range(vtx_delta):
                v[vtx, ndim:] += (  (v[vtx + vtx_delta, ndim:] - v[vtx, ndim:]) * 
                                (position[dim] - v[vtx,dim])/ (v [vtx + vtx_delta, dim] - v[vtx, dim])
                             )
        return v[0,ndim:]

    def findNeighbors(self, node, vector):
        _neighbor = None
        if node == None:
            return None  
        elif node.isLeafNode:
            _neighbor = node.grids
            return _neighbor
        else:
            child = self.findChild(node, vector)
            return self.findNeighbors(node.children[child],vector)
            
    def findChild(self, node, vector):
        key = ''
        for i in range(3):
            if vector[i] >= node.centre[i]:
                key += '+'
            else:
                key += '-'
        return DIRLOOKUP[key]

    def iterateGrid(self):
        self.allgrids = {}
        for conf in self._iterateGrid_help(self.root):
            if conf.idx not in self.allgrids:
                self.allgrids[conf.idx] = conf
        
    def _iterateGrid_help(self, node):
        """iterate all conf, not unique

        """
        for conf in node.grids:
            if conf != None:
                yield conf
                #print(conf.idx,conf)
        for child in node.children:
            if child == None:continue
            for c in self._iterateGrid_help(child):
                yield c  

    def iterateNode(self):
        self.allnodes = {}
        self.leafNodes = {}
        for n in self._iterateNode_help(self.root):
            if n.idx not in self.allnodes:
                self.allnodes[n.idx] = n
            if n.isLeafNode is True:
                self.leafNodes[n.idx] = n 

    def _iterateNode_help(self, node):
        if node != None:
            yield node 
        for child in node.children:
            if child == None:continue
            for n in self._iterateNode_help(child):
                yield  n 


## ---------------------------------------------------------------------------------------------------##
import copy
class Grid:
    def __init__(self, centre=(0.,0.,0.), size=12.0, symmetry=None):
        self.mesh = Octree(centre=(0.,0.,0.), size=12.0, symmetry=symmetry)
        self.confs = set()
        self.confs.update(self._iter_conf())
    def fill(self, conf_idx, value):
        self.mesh.fill(conf_idx, value)
    
    def refine(self, f, hopf2PDB, err_cutoff=1.0, filename='mesh.dat'):
        self.database_name = filename # set global filename for self.save
        self.angle_refine_count = 0
        self.axis_refine_count = 0
        self.pos_refine_count = 0
        self.max_err_conf = None
        self.hopf2PDB = hopf2PDB
        self.fill_with_f(f)
        self._refine_pos(f,err_cutoff)
        self.database_name = None
    
    def fill_with_f(self, f, confs = None,filename='mesh.dat'):
        n = len(self.confs)
        n_count = 1
        if confs is None: confs = self.confs
        for conf in confs:
            if n%1000 == 1:
                print('-'*8 + "filling %10d/%d"%(n_count,n)+'-'*8)
            n_count += 1
            if np.dot(conf.position, conf.position) < DIST_CUTOFF: # 2.0**2
                self.fill(conf.idx, 
                    np.array([100.0,100.0,100.0,100.0,100.0,100.0,100.0]))
            elif np.dot(conf.position, conf.position) >  144.0: # 12**2
                self.fill(conf.idx, np.array([0.0,0.0,0.0,0.0,0.0,0.0,0.0]))
            else:
                self.fill(conf.idx, 
                    f(conf.position,conf.vector, conf.angle))
        self.save(confs)
    

    def _refine_pos(self,f,err_cutoff=1.0):
        oldconfs = copy.copy(self.confs)
        fine = False
        while not fine:
            print("%d th time position refinement"%(self.pos_refine_count))
            self.pos_refine_count += 1
            fine = True
            for leaf in self.octLeafNodes():
                node = leaf.parent
                tree = leaf.tree
                node_err = 0
                testgrids = set()
                for quadtree in node.testgrid:
                    for bitree in quadtree.allgrids.values():
                        for conf in bitree.allgrids.values():
                            testgrids.add(conf)
                for g in testgrids:
                    dist2 = np.dot(g.position, g.position)
                    if (np.abs(dist2 - DIST_CUTOFF) <= 2 * node.size**2 
                        and node.size <= 1.0): 
                        print("Escaped the cutoff boundary.\n")
                        node.error = 0.0
                        break
                    g_iterp = tree.interpolation(g.position, g.vector, g.angle, node=node, neighbors=node.grids)
                    err = np.abs(g_iterp - g.value)
                    err = err[0]
                    if err > node_err:
                        node_err = err
                        self.max_err_conf = g
                if node_err < node.error: node.error = node_err
                if node.error > err_cutoff:
                    if node.children[0].isLeafNode:
                        printStr=("max  error  is %5.2f\n"%(node.error)+
                                   "conf:%15s"%(self.max_err_conf.idx)+
                                  " %5.2f"*3%tuple(self.max_err_conf.position)+
                                  " %5.2f"*3%tuple(self.max_err_conf.vector) +
                                  " %5.2f"%(self.max_err_conf.angle) +
                                  '\n' +
                                  "size of node %6.3f\n"%(node.size) +
                                  "conf values is " +
                                  " %5.2f"*7%tuple(self.max_err_conf.value)
                                  ) 
                        print(printStr)
                    for child in node.children:
                        if child.isLeafNode:
                            tree.subdivideNode(child)
                            fine  = False 
            self.confs.update(self._iter_conf())
            newconfs = self.confs.difference(oldconfs)
            print("total %15d confs, %15d new confs\n"%(len(self.confs),len(newconfs)))
            oldconfs = copy.copy(self.confs)
            if len(newconfs) > 0:
                self.fill_with_f(f,newconfs)
            self._refine_axis(f,err_cutoff=err_cutoff)

    def _refine_axis(self,f,err_cutoff=1.0):
        oldconfs = copy.copy(self.confs)
        fine = False
        while not fine:
            print("%d th time axis refinement"%(self.axis_refine_count))
            self.axis_refine_count += 1
            fine = True
            for leaf in self.quadLeafNodes():
                node = leaf.parent
                tree = leaf.tree
                node_err = 0
                testgrids = set()
                for bitree in node.testgrid:
                    for conf in bitree.allgrids.values():
                        testgrids.add(conf)
                for g in testgrids:
                    if g.value[0]==100.0==g.value[1]:
                        node.error = 0
                        break
                    if np.dot(g.position, g.position) < DIST_CUTOFF:
                        g_iterp = np.array([100.0,100.0,100.0,100.0,100.0,100.0,100.0])
                        node.error = 0
                        break
                    else:
                        g_iterp = tree.interpolation(g.vector, g.angle, 
                                                     node, node.grids)
                    err = np.abs(g_iterp - g.value)
                    err = err[0]
                    if err > node_err:
                        node_err = err
                        self.max_err_conf = g
                if node.error == 0:continue
                if node_err < node.error: node.error = node_err
                if node.error > err_cutoff/2:
                    if node.children[0].isLeafNode:
                        printStr=("\nmax  error  is %5.2f\n"%(node.error)+
                                   "conf:%15s"%(self.max_err_conf.idx)+
                                  " %5.2f"*3%tuple(self.max_err_conf.position)+
                                  " %5.2f"*3%tuple(self.max_err_conf.vector) +
                                  " %5.2f"%(self.max_err_conf.angle) +
                                  '\n' +
                                  "area of node %6.3f/4*pi\n"%(node.size) +
                                  "conf values is " +
                                  " %5.2f"*7%tuple(self.max_err_conf.value)
                                  )
                        print(printStr)
                        #with open(self.max_err_conf.idx+'.pdb','w') as f:
                        #    f.write(self.hopf2PDB(self.max_err_conf.position,
                        #                          self.max_err_conf.vector,
                        #                          self.max_err_conf.angle))
                    for child in node.children:
                        if child.isLeafNode:
                            tree. subdivideNode(child)
                            fine = False 
            self.confs.update(self._iter_conf())
            newconfs = self.confs.difference(oldconfs)
            print("total %15d confs, %15d new confs\n"%(len(self.confs),len(newconfs)))
            oldconfs = copy.copy(self.confs)
            if len(newconfs) > 0:
                self.fill_with_f(f,newconfs)
            self._refine_angle(f,err_cutoff=err_cutoff)


    def _refine_angle(self,f,err_cutoff=1.0):
        oldconfs = copy.copy(self.confs)
        fine = False
        while not fine:
            print("%d th time angle refinement"%(self.angle_refine_count))
            self.angle_refine_count += 1
            fine = True
            for leaf in self.biLeafNodes():
                node = leaf.parent
                tree = leaf.tree
                node_err = 0
                for g in node.testgrid:
                    if g.value[0]==100.0==g.value[1]:
                        node.error = 0
                        break
                    if np.dot(g.position, g.position) < DIST_CUTOFF:
                        g_iterp = np.array([100.0,100.0,100.0,100.0,100.0,100.0,100.0])
                        node.error = 0
                        break
                    else:
                        g_iterp = tree.interpolation(g.angle, node, node.grids)
                    err = np.abs(g_iterp - g.value)
                    err = err[0]
                    if err > node_err:
                        node_err = err
                if node.error == 0:continue
                if node_err < node.error: node.error = node_err
                if node.error > err_cutoff/4:
                    for child in node.children:
                        if child.isLeafNode:
                            tree.subdivideNode(child)
                            fine =  False  
            self.confs.update(self._iter_conf())
            newconfs = self.confs.difference(oldconfs)
            print("total %15d confs, %15d new confs\n"%(len(self.confs),len(newconfs)))
            oldconfs = copy.copy(self.confs)
            if len(newconfs) > 0:
                self.fill_with_f(f,newconfs)
        
        
    def interpolate(self, position, vector, angle):
        if np.dot(position, position) < DIST_CUTOFF:
            return np.array([100.0,100.0,100.0,100.0,100.0,100.0,100.0])
        if np.dot(position, position) >  144.0:
            return np.array([0.0,0.0,0.0,0.0,0.0,0.0,0.0])
        return self.mesh.interpolation(position, vector, angle)

    def load(self, filename):
        with open(filename,'r') as f:
            for i in f.readlines():
                if i[0] == '#':continue
                i = i.split()
                if len(i) != 7:continue
                idx = i[0]
                value = np.array([float(v) for v in i[1:]])
                self.mesh.fill(idx, value)
    
    def save(self, confs=None, filename='mesh.dat'):
        if confs is None:confs=self._iter_conf()
        if self.database_name != None: filename = self.database_name
        with open(filename, 'a') as f:
            for conf in confs:
                conf_str='%s'%(conf.idx) + ' %f'*7%tuple(conf.value) + '\n'
                f.write(conf_str)

    def gen_x(self):
        for conf in self._iter_conf(self):
            yield (conf.position, conf.vector, conf.angle)
    
    def _iter_conf(self):
        for quadtree in self.mesh.allgrids.values():
            for bitree in quadtree.allgrids.values():
                for conf in bitree.allgrids.values():
                    yield conf

    def biLeafNodes(self):
        for quadNode in self.quadLeafNodes():
            for bitree in quadNode.grids:
                for n in bitree.leafNodes.values():
                    n.tree = bitree
                    yield n
    def quadLeafNodes(self):
        for octNode in self.octLeafNodes():
            for quadtree in octNode.grids:
                for n in quadtree.leafNodes.values():
                    n.tree = quadtree
                    yield n

    def octLeafNodes(self):
        for n in self.mesh.leafNodes.values():
            n.tree = self.mesh
            yield n
        
            
        
if __name__ == "__main__":
    pass
