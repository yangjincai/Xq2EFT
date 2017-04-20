"""A Hierarchical Adaptive Mesh indexing tranlation and rotation space.

Combining octree (for indexing tranlation space) and 
cubed-sphere quaterion to index all configurations of two rigid body.

Octree grid order:like N\\N, this is a Z-like order
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
import numpy as np
import pdb
np.seterr(invalid='warn')


# This dictionary is used by the findBranch function, to return the correct branch index
DIRLOOKUP = {'+++':7, '-++':3, '--+':1, '+-+':5, '++-':6, '-+-':2, '---':0, '+--':4}
#### End Globals ####
#E_HIGH = 100.0
E_HIGH = 0.0 # default value set as 0.0 maybe more retionable
DIST_CUTOFF = 2.5 ** 2
HIGH = np.array([E_HIGH,E_HIGH,E_HIGH,E_HIGH,E_HIGH,E_HIGH,E_HIGH])
CONFS = [] # save confs in the order of creation
GOLDEN = (1 + 5 ** 0.5) / 2

class conf:
    def __init__(self, idx, location=None, q=None,values=HIGH):
        self.idx = idx
        self.pos =  {} # position in angle cubic
        self.loc = location # location  in  translation space (r, theta, phi)
        self.q = q
        self.values = values

class Node:
    """Node.

    """
    def __init__(self, idx=None, pos=None, size=None, leaf_num=None):
        self.error = 100.0
        self.pos = pos
        self.size = size
        self.isLeafNode  = True
        self.idx = idx
        self.leaf_num = leaf_num
        # children store region
        self.children = [None for i in range(self.leaf_num)] # the branches should have order
        # grids store mesh grids
        self.grids = []
        self.testgrid = []
        self.parent = None


class Octree:
    """QuadTree to index sphere

    """
    def __init__(self, idx, pos, size, next_level_id):
        """init octree by symmetry, and add 
        
        com is pos of mass.
        node_idx will be like "T123R123N123C123"
        T:translocation, R:rotation, R:normal, C:configuration
        """
        self.idx = idx
        self.pos = pos
        self.size = size
        self.nID = next_level_id
        self.allnodes = {}
        self.allgrids = {}
        self.gDict = dict()
        self.root = Node(idx, pos, size, leaf_num= 8)
        self.allnodes[self.root.idx] = self.root
        #print("init a Tree idx:%10s loc:r,%6.3f phi,%6.3f theta,%6.3f"%(self.idx, self.pos[0], self.pos[1],self.pos[2])  )
 
    def _triLinearInterp(self, pos, matrix):
        ndim = len(pos)        
        v = martix # position + values
        for dim in range(ndim):
            vtx_delta = 2**(ndim - dim - 1)
            for vtx in range(vtx_delta):
                v[vtx, ndim:] += (  (v[vtx + vtx_delta, ndim:] - v[vtx, ndim:]) * 
                                (pos[ dim] - v[vtx,dim])/ (v [vtx + vtx_delta, dim] - v[vtx, dim])
                               ) 
        return v[0,ndim:]

    def addNode(self, idx):
        node_idx = idx.split(self.nID)[0]
        if node_idx in self.allnodes:return
        #pdb.set_trace()
        #self._addNode_help(node_idx[:-1])
        idxs = ''
        while node_idx not in self.allnodes:
            idxs = node_idx[-1]+ idxs
            node_idx = node_idx[:-1]
        for i in idxs:
            if self.allnodes[node_idx].isLeafNode:
                self.subdivideNode(self.allnodes[node_idx])
            node_idx += i
   
    def _addNode_help(self, node_idx):
        #print(node_idx)
        if node_idx in self.allnodes:
            if self.allnodes[node_idx].isLeafNode:
                self.subdivideNode(self.allnodes[node_idx])
        else:
            self._addNode_help(node_idx[:-1])
            self.subdivideNode(self.allnodes[node_idx])

    def grepGrid(self, vector):
        """check if a grid(bitree) exists by distance of two vector
        print(self.root.children)
        
        """
        for grid in self.allgrids.values():
            delta = np.linalg.norm(grid.pos - vector)
            if delta < 0.001:
                return grid
        return None

    def _grid_positions(self,node,offset=None):
        if offset is None:offset = node.size
        offsets = np.array([[-offset[0],-offset[1],-offset[2]],
                            [-offset[0],-offset[1],+offset[2]],
                            [-offset[0],+offset[1],-offset[2]],
                            [-offset[0],+offset[1],+offset[2]],
                            [+offset[0],-offset[1],-offset[2]],
                            [+offset[0],-offset[1],+offset[2]],
                            [+offset[0],+offset[1],-offset[2]],
                            [+offset[0],+offset[1],+offset[2]]
                             ]) 
        return node.pos + offsets

    def _newCentre(self,node):
        offset = node.size/2.0
        return self._grid_positions(node,offset)
        
    def findNeighbors(self, node, vector):
        leaf = self.inWhichNode(node, vector)
        return leaf.grids

    def inWhichNode(self, node, vector):
        _neighbor = None
        if node == None:
            return None  
        elif node.isLeafNode:
            return node
        else:
            if len(vector) == 4 and node is self.root:
                child = np.abs(vector).argmax()
                vector /= vector[chlild]
                vector = np.arctan(vector)
                vector = np.delete(vector,child)
            else:
                child = self.findChild(node, vector)
            return self.inWhichNode(node.children[child],vector)
            
    def findChild(self, node, vector):
        key = ''
        for i in range(3):
            if vector[i] >= node.pos[i]:
                key += '+'
            else:
                key += '-'
        return DIRLOOKUP[key]


    def _np2str(self, q):
        npstr = ''
        for i in q:
            if i  < 0.0000001 and i> -0.0000001:i += 0.0000001
            npstr += 'N%.5f'%(i)
        return npstr


## ---------------------------------------------------------------------------------------------------##
class Qtree(Octree):
    def __init__(self, idx, pos):
        Octree.__init__(self, idx, pos, 16*3.14, 'C') #There 4 sphere in  root ^_^
        self.leafNodes = set()
        self.leafNodes.add(self.root)
        self.subdivideNode(self.root)
        #for i in range(4): self.subdivideNode(self.root.children[i])
        #self.fill(self.root.children[0].idx+'111111C7',0.0)

    def fill(self, idx, values):
        """fill conf after generation 
        """
        # import pdb 
        #pdb.set_trace()
        self.addNode(idx)
        # if idx:wtrR0Q2C7, grid_idx::wtrR0 or wtrR0Q2
        if idx in self.allgrids:
            self.allgrids[idx].values = values
        else:
            raise Exception("Con't fill conf %s\n"%(idx))
            
    def subdivideNode(self, parent):
        parent.isLeafNode = False
        self.leafNodes.remove(parent)
        childnum = 8
        if parent is self.root:
            childnum = 4
            for i in range(4):
                child = Node(self.idx + '%d'%(i), np.array([0.,0.,0.]), 
                         np.array([np.pi/4., np.pi/4., np.pi/4.]), 8)
                parent.children[i] = child
        else:
            newCentre = self._newCentre(parent)
            for i in range(8):
                child = Node(parent.idx + str(i), pos=newCentre[i],
                        size = parent.size/2.0, leaf_num= 8)
                parent.children[i] = child
        
        for i in range(childnum):
            child = parent.children[i]
            self.leafNodes.add(child)
            self.allnodes[child.idx] = child
            for j, pos_ndx in enumerate(self._grid_positions(child)):
                idx = child.idx+'%s%d'%(self.nID,j)
                q = self._ndx2q(child.idx, pos_ndx)
                npstr = self._np2str(q)
                grid = None
                if npstr in self.gDict:
                    grid = self.gDict[npstr]
                else:
                    grid = conf(idx, tuple(self.pos), tuple(q)) 
                    CONFS.append(grid)
                    self.gDict[npstr] = grid
                    self.allgrids[grid.idx]=grid
                    # self.pos is translation space coord
                grid.pos[idx] = pos_ndx
                child.grids.append(grid)
            # add testgrid
            idx = child.idx+'%s8'%(self.nID)
            q = self._ndx2q(child.idx, child.pos)
            npstr = self._np2str(q)
            if npstr in self.gDict:
                grid = self.gDict[npstr]
            else:
                grid = conf(idx, tuple(self.pos), tuple(q)) 
                CONFS.append(grid)
                self.gDict[npstr] = grid
                self.allgrids[grid.idx]=grid
                self.allgrids[grid.idx] = grid
            child.testgrid.append(grid)
            child.parent = parent
        #self.iterateGrid()
        #self.iterateNode()
        #parent.testgrid.append(self.grepGrid(self._ndx2q(parent.idx, parent.pos)))
                
    def interpolation(self, q, node=None, neighbors=None):
        cubeID, ndx = self._q2ndx(q)
        if node is None: 
            node = self.root.children[cubeID]
        #else:
        #    pos = self.pos
        #    if np.dot(pos, pos) < DIST_CUTOFF
        #        return np.array([100.0,100.0,100.0,100.0,100.0,100.0,100.0])
        #    if np.dot(pos, pos) >  144.0:
        #        return np.array([0.0,0.0,0.0,0.0,0.0,0.0,0.0])
        if neighbors is None: 
            if not node.isLeafNode:
                node = self.inWhichNode(node, ndx)
            neighbors = node.grids

        ndim = len(ndx)        
        v = np.zeros((8,ndim + 7))
        for i in range(8):
            v[i,0:ndim] = neighbors[i].pos[node.idx+'%s%d'%(self.nID,i)]# neigbor is conf, conf.pos is angle index
            v[i,ndim:] = neighbors[i].values
        for dim in range(ndim):
            vtx_delta = 2**(ndim - dim - 1)
            for vtx in range(vtx_delta):
                #if np.abs(v[vtx + vtx_delta, dim] - v[vtx, dim]) < 0.000001:
                   # pdb.set_trace()
                    #print(ndx[dim], v[vtx,dim],v[vtx + vtx_delta, dim])
                v[vtx, ndim:] += (  (v[vtx + vtx_delta, ndim:] - v[vtx, ndim:]) * 
                    (ndx[dim] - v[vtx,dim])/ (v[vtx + vtx_delta, dim] - v[vtx, dim])
                    )
        return v[0,ndim:]

    def _q2ndx(self, q):
        q = np.copy(q)
        cubeID = np.abs(q).argmax()
        q /= q[cubeID]
        q = np.arctan(q)
        ndx = np.delete(q, cubeID)
        return cubeID, ndx

    def _ndx2q(self, cubeID, ndx):
        cubeID = str(cubeID)
        cubeID = cubeID.replace(self.idx,'')[0]
        cubeID = int(cubeID)
        ndx = np.tan(ndx)
        q = np.insert(ndx, cubeID, 1.0)
        q /= np.linalg.norm(q)
        if q[0] < 0:
            q = -q
        if q[1] < 0: #water symmstery
            q[0], q[1], q[2], q[3] = -q[1], q[0], q[3], -q[2]
        if q[0]== q[1] == 0:
            if q[2] ==  0 or q[3] ==  0:
                q = np.array([0., 0., 1., 0.])
        if q[2]== q[3] == 0:
            if q[0] ==  0 or q[1] ==  0:
                q = np.array([1., 0., 0., 0.])
        return q


class Rtree(Octree):
    def __init__(self, idx, symmetry=2):
        self.r_size = (7.-2.)*(2.-GOLDEN)
        Octree.__init__(self, idx, np.array([2+self.r_size, 0., np.pi/2.]), # centre, r, phi, theta
                                    np.array([self.r_size, np.pi/2., np.pi/2.]), 'Q') # size and rotation level idx
        self.leafNodes = set()
        self.leafNodes.add(self.root)
        self.subdivideNode(self.root)
#        for i in self.root.children:
#            if i is not None:self.subdivideNode(i)
    def _sph2xyz(self, sph):
        r,phi,theta = sph
        x = r * np.cos(phi) * np.cos(theta)
        y = r * np.cos(phi) * np.sin(theta)
        z = r * np.sin(phi)
        return (x,y,z)

    def fill(self, idx, values):
        """fill conf after generation 
        """
        #import pdb 
        #pdb.set_trace()
        self.addNode(idx)
        # if idx:wtrR0Q2C7, grid_idx::wtrR0 or wtrR0Q2
        grid_idx = idx[ :idx.find(self.nID) + 2]
        if grid_idx in self.allgrids:
            self.allgrids[grid_idx].fill(idx, values)
        else:
            raise Exception("Con't fill conf %s\n"%(idx))

    def _grid_positions_golden(self,node,offset=None):
        if offset is None:offset = node.size
        offsets = np.array([[-offset[0],-offset[1],-offset[2]],
                            [-offset[0],-offset[1],+offset[2]],
                            [-offset[0],+offset[1],-offset[2]],
                            [-offset[0],+offset[1],+offset[2]],
                            [+offset[0]*GOLDEN,-offset[1],-offset[2]],
                            [+offset[0]*GOLDEN,-offset[1],+offset[2]],
                            [+offset[0]*GOLDEN,+offset[1],-offset[2]],
                            [+offset[0]*GOLDEN,+offset[1],+offset[2]]
                             ])  
        return node.pos + offsets

    def _newCentre_golden(self,node):
        offset = (node.size[0] * (GOLDEN-1.), node.size[1]*0.5, node.size[2]*0.5)
        return self._grid_positions(node,offset)

    def subdivideNode(self, parent):
        parent.isLeafNode = False
        self.leafNodes.remove(parent)
        newCentre = self._newCentre_golden(parent)
        if parent is self.root:
            for key in DIRLOOKUP:
                if key[1] == '-': continue
                i = DIRLOOKUP[key]
                if i < 4:
                    size_factor = (2.-GOLDEN, 0.5, 0.5)
                else:
                    size_factor = (GOLDEN - 1., 0.5, 0.5)
                child = Node(parent.idx + str(i), pos=newCentre[i], 
                             size = parent.size * size_factor, leaf_num= 8)
                parent.children[i] = child
        else:
            for i in range(8):
                if i < 4:
                    size_factor = (2.-GOLDEN, 0.5, 0.5)
                else:
                    size_factor = (GOLDEN - 1., 0.5, 0.5)
                child = Node(parent.idx + str(i), pos=newCentre[i], 
                             size = parent.size * size_factor, leaf_num= 8)
                parent.children[i] = child
        for i in range(8):
            child = parent.children[i]
            if child is None:continue
            self.leafNodes.add(child)
            self.allnodes[child.idx] = child
            for j, pos in enumerate(self._grid_positions_golden(child)):
                idx = child.idx+'%s%d'%(self.nID,j)
                xyz = self._sph2xyz(pos)
                npstr = self._np2str(xyz)
                if npstr not in self.gDict:
                    self.gDict[npstr] = Qtree(idx, pos)
                grid = self.gDict[npstr]
                self.allgrids[grid.idx]=grid
                child.grids.append(grid)
            xyz = self._sph2xyz(child.pos)
            npstr = self._np2str(xyz)
            idx = child.idx+'%s8'%(self.nID)
            if npstr not in self.gDict:
                self.gDict[npstr] = Qtree(idx, child.pos)
            grid = self.gDict[npstr]
            self.allgrids[idx]=grid
            child.testgrid.append(grid)
            child.parent = parent

    def interpolation(self, pos, q, node=None, neighbors=None):
        #if np.dot(pos, pos) < DIST_CUTOFF:
        #    return np.array([100.0,100.0,100.0,100.0,100.0,100.0,100.0])
        #if np.dot(pos, pos) >  144.0:
        #    return np.array([0.0,0.0,0.0,0.0,0.0,0.0,0.0])
        #if node is None: node = self.root.children[self.findChild(self.root, self._sph2xyz(pos))]
        if node is None: node = self.root
        if neighbors is None: neighbors = self.findNeighbors(node, pos)
        ndim = len(pos)        
        v = np.zeros((8,ndim + 7))
        #print('#'*4 +"interp pos is %.5f %.5f %.5f"%tuple(pos)+ '#'*4)
        for i in range(8):
            v[i,0:ndim] = neighbors[i].pos
            #print(neighbors[i].idx + ' %.5f'*3%tuple(neighbors[i].pos))
            v[i,ndim:] = neighbors[i].interpolation(q)
        for dim in range(ndim):
            vtx_delta = 2**(ndim - dim - 1)
            for vtx in range(vtx_delta):
                v[vtx, ndim:] += ((v[vtx + vtx_delta, ndim:] - v[vtx, ndim:]) * 
                    (pos[dim] - v[vtx,dim])/ (v [vtx + vtx_delta, dim] - v[vtx, dim])
                    )
        return v[0,ndim:]

class Xtree(Octree):
    def __init__(self, idx, symmetry=2):
        Octree.__init__(self,idx,
                        np.array([0., 0., 0.]), np.array([12., 12., 12.]), 'Q') # size and rotation level idx
        self.leafNodes = set()
        self.leafNodes.add(self.root)
        self.subdivideNode(self.root)
#        for i in self.root.children:
#            if i is not None:self.subdivideNode(i)


    def fill(self, idx, values):
        """fill conf after generation 
        """
        #import pdb 
        #pdb.set_trace()
        self.addNode(idx)
        # if idx:wtrR0Q2C7, grid_idx::wtrR0 or wtrR0Q2
        grid_idx = idx[ :idx.find(self.nID) + 2]
        #print(grid_idx)
        #print(self.allgrids)
        if grid_idx in self.allgrids:
            self.allgrids[grid_idx].fill(idx, values)
        else:
            raise Exception("Con't fill conf %s\n"%(idx))

    def interpolation(self, pos, q, node=None, neighbors=None):
        #if np.dot(pos, pos) < DIST_CUTOFF:
        #    return np.array([100.0,100.0,100.0,100.0,100.0,100.0,100.0])
        #if np.dot(pos, pos) >  144.0:
        #    return np.array([0.0,0.0,0.0,0.0,0.0,0.0,0.0])
        if node is None: node = self.root
        if neighbors is None: neighbors = self.findNeighbors(node, pos)
        ndim = len(pos)        
        v = np.zeros((8,ndim + 7))
        #print('#'*4 +"interp pos is %.5f %.5f %.5f"%tuple(pos)+ '#'*4)
        for i in range(8):
            v[i,0:ndim] = neighbors[i].pos
            #print(neighbors[i].idx + ' %.5f'*3%tuple(neighbors[i].pos))
            v[i,ndim:] = neighbors[i].interpolation(q)
        for dim in range(ndim):
            vtx_delta = 2**(ndim - dim - 1)
            for vtx in range(vtx_delta):
                v[vtx, ndim:] += ((v[vtx + vtx_delta, ndim:] - v[vtx, ndim:]) * 
                    (pos[dim] - v[vtx,dim])/ (v [vtx + vtx_delta, dim] - v[vtx, dim])
                    )
        return v[0,ndim:]
    
    def subdivideNode(self, parent):
        parent.isLeafNode = False
        self.leafNodes.remove(parent)
        newCentre = self._newCentre(parent)
        if parent is self.root:
            keys = []
            for k in DIRLOOKUP.keys():
                if '-' in k[1]:continue
                if '-' in k[2]:continue
                keys.append(k)
            for k in keys:
                i = DIRLOOKUP[k]
                child = Node(parent.idx + str(i), pos=newCentre[i], 
                             size = parent.size/2.0, leaf_num= 8)
                parent.children[i] = child
        else:
            for i in range(8):
                child = Node(parent.idx + str(i), pos=newCentre[i], 
                             size = parent.size/2.0, leaf_num= 8)
                parent.children[i] = child
        for i in range(8):
            child = parent.children[i]
            if child is None:continue
            self.leafNodes.add(child)
            self.allnodes[child.idx] = child
            for j, pos in enumerate(self._grid_positions(child)):
                idx = child.idx+'%s%d'%(self.nID,j)
                npstr = self._np2str(pos)
                if npstr not in self.gDict:
                    self.gDict[npstr] = Qtree(idx, pos)
                grid = self.gDict[npstr]
                self.allgrids[grid.idx]=grid
                child.grids.append(grid)
            idx = child.idx+'%s8'%(self.nID)
            npstr = self._np2str(child.pos)
            if npstr not in self.gDict:
                self.gDict[npstr] = Qtree(idx, child.pos)
            grid = self.gDict[npstr]
            self.allgrids[grid.idx]=grid
            child.testgrid.append(grid)
            child.parent = parent
################### Above: basic tree, node, grid(conf) class ######################
################### Below: basic mesh class ########################################
import pickle
class  mesh:
    def __init__(self):
        self.mesh = Rtree('wtr_wtrR')
        self.confs = set()
        self.confs.update(self._iter_conf())
        self.n = len(self.confs)
    def updateDatabase(self, filename):
        #self.confs = set()
        self.mesh = pickle.load(open(filename, "rb"))
        self.confs.update(self._iter_conf())
        self.n = len(self.confs)
        print("There are %d confs in this mesh."%(self.n))
        
    def dumpDatabase(self, filename):
        pickle.dump(self.mesh, open(filename, "wb"), True)
        print("Total %d confs saved in database %s"%(self.n, filename))

    def fill(self, conf_idx, values):
        self.mesh.fill(conf_idx, values)
    
    def fill_with_f(self, f, confs = None,filename='mesh.dat'):
        if confs is None: confs = self.confs
        n = len(confs)
        n_count = 1
        for conf in confs:
            if n_count%1000 == 1:
                print('-'*8 + "filling %10d/%d"%(n_count,n)+'-'*8)
            n_count += 1
            #self.fill(conf.idx, f(conf.loc, conf.q))
            conf.values =  f(conf.loc, conf.q)
        #self.save(confs)
        
    def interpolate(self, R, q):
        return self.mesh.interpolation(R, q)

    def load(self, filename):
        load_count = 0
        with open(filename,'r') as f:
            for i in f:
                if load_count%10000 == 0: print('>'*8+"Loaded %10d conf"%(load_count)+'<'*8)
                load_count += 1
                if i[0] == '#':continue
                i = i.split()
                if len(i) != 8:continue
                idx = i[0]
                #if idx=="wtr_wtrR360Q60C0":pdb.set_trace()
                values = np.array([float(v) for v in i[1:]])
                self.mesh.fill(idx, values)
        self._iter_conf()
    
    def save(self, confs=None, filename='mesh.dat'):
        if confs is None:confs=CONFS
        if self.database_name != None: filename = self.database_name
        with open(filename, 'w') as f:
            for conf in confs:
                conf_str='%s'%(conf.idx) + ' %f'*7%tuple(conf.values) + '\n'
                f.write(conf_str)

    def gen_x(self):
        for conf in self._iter_conf(self):
            yield (conf.loc, conf.q)
    
    def _iter_conf(self):
        for Qtree in self.mesh.gDict.values():
            for conf in Qtree.gDict.values():
                yield conf
    def _iter_grid(self):
        for Qtree in self.mesh.gDict.values():
            yield Qtree

    def _grid_conf(self):
        for Qtree in self.mesh.gDict.values():
            yield Qtree.root.children[0].grids[0]

    def QLeafNodes(self):
        for RNode in self.RLeafNodes():
            for Qtree in RNode.grids:
                for n in Qtree.leafNodes:
                    n.tree = Qtree
                    yield n

    def RLeafNodes(self):
        for n in self.mesh.leafNodes:
            n.tree = self.mesh
            yield n
        
            
        
        
if __name__ == "__main__":
    pass