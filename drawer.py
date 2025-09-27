''' the need for a smoothening filter is felt '''
import numpy as np
from PIL import Image
import os


class Position:

 '''To reset the origin and make sensible pixel position indices'''

 def __init__(self, size = (500, 500), origin = None, bg_color = [255, 255, 255]):
  self.size = size
  self.rows, self.cols = size
  self.origin = origin
  self.centre = int(self.size[0]//2), int(self.size[1]//2)
  if type(origin) == type(None):
   self.origin = self.centre            # origin set-up here according to the tkinter & PIL convention. Here (0, 0) is in the centre
  self.bg = list(bg_color)
  self.bg_color = bg_color
  rowlist = [self.bg] * self.cols
  self.bigcolm = [rowlist] * self.rows
  self.mutarr = np.array(self.bigcolm)              # mutable version of self.arr, made as list multiplication holds references to factor lists
  self.drew_dict = dict()               # used by smooth_line, not clean solution
  self.tempim_modcount = 1                 # current solution for avoiding tempim naming clash, subject to change    

  ''' 11/8/2025. Changing the nature of curvesets. As it was realized by list vs. dict search test, list search slows quickly with size.
               Now curvesets will map name (`str` object) to a dict that maps point to bool. '''
  self.curvesets = {}                  # keys to be user-assigned names (hence unique) to curvesets, values the list of points composing the curveset

 def pilcoords(self, x, y):
  x = x + self.origin[1]
  y = self.origin[0] - y
  if x not in range(self.cols) or y not in range(self.rows):
   raise ValueError('coordinates `x` & `y` must be within the image frame size w.r.t. the origin set-up')
  return (x, y)

 def in_bound(self, point):
  try:
   x, y = self.pilcoords(*point)
   return True
  except:
   return False  

 def draw_point(self, x, y, color = [0, 0, 0]):
  x, y = self.pilcoords(x, y)
  self.mutarr[y][x] = color

 def xor_checker2(self, point1, point2):  
  x1, y1 = point1
  x2, y2 = point2

  if x1//1 == x2//1 and y1//1 == y2//1:
   return (x1, y1)                        # or return (x2, y2), doesn't matter in this case
  if x1//1 == x2//1:
   if y2//1 > y1//1:
    d = 1
   else:
    d = -1
   nyl = range(int(y1//1), int(y2//1)+d, d)
   pxllist = []
   for y in nyl:
    pxllist.append((x1//1, y//1))
   return pxllist

  if y1//1 == y2//1:
   if x2//1 > x1//1:
    d = 1
   else:
    d = -1
   nxl = range(int(x1//1), int(x2//1)+d, d)
   pxllist = []
   for x in nxl:
    pxllist.append((x//1, y1//1))
   return pxllist

  a = (y2-y1)/(x2-x1)
  b = y1-a*x1

  if x2//1 > x1//1:
   dx = 1
  else:
   dx = -1
  nxl = range(int(x1//1), int(x2//1)+dx, dx)
  if y2//1 > y1//1:
   dy = 1
  else:
   dy = -1
  nyl = range(int(y1//1), int(y2//1)+dy, dy)

  pxllist = []
  for x in nxl:
   if (x, (a*x+b)//1) not in pxllist:
    pxllist.append((x, (a*x+b)//1))
  for y in nyl:
   if (((y-b)/a)//1, y) not in pxllist:
    pxllist.append((((y-b)/a)//1, y))
 
  xmin = min(x1, x2)
  ymin = min(y1, y2)
  xmax = max(x1, x2)
  ymax = max(y1, y2)
  xmin = xmin//1
  ymin = ymin//1
  xmax = xmax//1
  ymax = ymax//1
 
  i = 0
  for j in range(len(pxllist)):
   I = pxllist[j-i]
   if I[0] < xmin or I[0] > xmax or I[1] < ymin or I[1] > ymax:
    del pxllist[j-i]
    i += 1
  
  return pxllist


 def line_segment(self, point1, point2, color = [0, 0, 0], curvename = None):
   marked_points = dict(zip([i for i in self.xor_checker2(point1, point2)], [False]*len(self.xor_checker2(point1, point2))))
   if curvename:
    try:
     self.curvesets[curvename]
    except:
     self.curvesets[curvename] = {}
   for i in self.xor_checker2(point1, point2):
    ix = int(i[0])
    iy = int(i[1])
    if not marked_points[i]:
     self.draw_point(ix, iy, color = color)
     marked_points[i] = True
     if curvename:
      self.curvesets[curvename][(ix, iy)] = True
#      print(i, 'from line_segment')
 def plot(self, xlist, ylist, color = [0]*3, curvename = None):
 # to draw multiple line_segments, along the points in zip(xlist, ylist)
  if len(xlist) != len(ylist):
   raise ValueError('`xlist` & `ylist` must be of same size')

  points = list(zip(xlist, ylist))
  for i in range(len(xlist) - 1):
   self.line_segment(points[i], points[i+1], color = color, curvename = curvename)       # the curve work is just forwarded to line_segment

 # test function, for seeing effect of imposing an inequality rather than a strict equality on the pixel coords satisfying the equation of a line
 def smooth_line(self, point1, point2, tolerance = None, smoothness = None, thickness = 1, color = [0]*3):
  x1, y1 = point1
  x2, y2 = point2
  xmin = min(x1, x2)
  ymin = min(y1, y2)
  xmax = max(x1, x2)
  ymax = max(y1, y2)
  if x1//1 == x2//1:
   for x in range(int((xmin-thickness)//1), int((xmax+thickness)//1)):
    for y in range(int((ymin)//1), int((ymax+thickness)//1)):
     if self.in_bound((int(x//1), int(y//1))):
      self.draw_point(int(x//1), int(y//1), color = color)
      self.drew_dict[(int(x//1), int(y//1))] = color
   return
  pxllist = []
  a = (y2-y1)/(x2-x1)
  b = y1-a*x1

  if a == 0:
   tol, smo = 0.5, 1
  elif abs(a) < 0.05:
   tol, smo = 1, 2
  elif 0.05 <= abs(a) <= 1:
   tol, smo = 0.5, 2        # smo was 2
  elif 1 < abs(a) < 1.6:
   tol, smo = 0.75, 2
  elif 1.6 <= abs(a) < 2:
   tol, smo = 1, 2.5
  elif 2 <= abs(a) < 2.8:
   tol, smo = 1.25, 3.5
  elif 2.8 <= abs(a) < 3:
   tol, smo = 1.5, 3.75
  elif 3 <= abs(a) < 4:
   tol, smo = 1.5, abs(a) + 0.75
  elif 4 <= abs(a) < 5:
   tol, smo = 2, abs(a) + 1.5
  elif 5 <= abs(a) < 6:
   tol, smo = 2.5, abs(a) + 2
  elif abs(a) >= 6:
   tol, smo = abs(a)/2, abs(a) * 1.5 + 1
  
  tolerance, smoothness = tol, smo
  if a != 0:
   bin_len = max(5, int(abs(a)//1), int(abs(1/a)//1)) + 1
   if bin_len > 100:
    bin_len = 100
   col_r, col_g, col_b = color[0], color[1], color[2]
   r_dif, g_dif, b_dif = self.bg_color[0] - col_r, self.bg_color[1] - col_g, self.bg_color[2] - col_b
   bins = [[col_r+int(r_dif//(bin_len))*i, col_g+int(g_dif//(bin_len))*i, col_b+int(b_dif//(bin_len))*i] for i in range(1, bin_len)]
   print(bins, ' <-- bins')
  else:
   bins = [[0]*3 for i in range(5)]
 
  for x in range(int((xmin-thickness)//1), int((xmax+thickness)//1+1)):
   for y in range(int((ymin-thickness)//1), int((ymax+thickness)//1+1)):
    if abs(y-a*x-b) <= tolerance and self.in_bound((int(x//1), int(y//1))):
     pxllist.append((int(x//1), int(y//1)))
    if tolerance < abs(y-a*x-b) < smoothness and self.in_bound((int(x//1), int(y//1))):
     percen = abs(y-a*x-b)-tolerance
     delta = smoothness-tolerance
     accuracy_color_bindex = int((percen/delta*len(bins))//1)
     print(accuracy_color_bindex, 'bindex used')
     if accuracy_color_bindex > len(bins) - 1:
      accuracy_color_bindex = len(bins) - 1
      print('saahhhhh')
     try:
      if self.drew_dict[(int(x//1), int(y//1))] > bins[accuracy_color_bindex]:
       raise
     except:
      self.draw_point(int(x//1), int(y//1), color = bins[accuracy_color_bindex])
      self.drew_dict[(int(x//1), int(y//1))] = bins[accuracy_color_bindex]
  for pxl in pxllist:
   self.draw_point(*pxl, color = color)
   self.drew_dict[pxl] = color

 def _color_tendify(self, gradlist, color):
  ''' `gradlist` param is the list of (collinear) pixels that need to be gradiented; fading from `color` to `self.bg_color` '''
  L = len(gradlist)
  # debate to put an upper bound on `L`, like in `smooth_line`
  col_r, col_g, col_b = color[0], color[1], color[2]
  r_dif, g_dif, b_dif = self.bg_color[0] - col_r, self.bg_color[1] - col_g, self.bg_color[2] - col_b
  color_bins = [[col_r+int(r_dif*i/(L+1)), col_g+int(g_dif*i/(L+1)), col_b+int(b_dif*i/(L+1))] for i in range(1, L+1)]
#  print(color_bins, 'color_bins')
  return color_bins

 def draw_box(self, x, y, side, thickness = 1, color = [0]*3, filled = False, fillcolor = [255, 0, 0]):
  ''' draw square box of side length `side` and bottom-left corner at x, y. `side` is the length of the outer perimeter of the box'''
  if thickness != 1:
   for j in range(0, thickness):
    self.draw_box(x+j, y+j, side - 2*j, color = color)
  else:
   self.line_segment((x, y), (x, y+side), color = color)
   self.line_segment((x, y), (x+side, y), color = color)
   self.line_segment((x+side, y), (x+side, y+side), color = color)
   self.line_segment((x, y+side), (x+side, y+side), color = color)

  if filled:
  # a gradient fill can also be applied
   for i in range(x + thickness, x + thickness + side - 2*thickness + 1):
    for j in range(y+ thickness, y+ thickness + side - 2*thickness + 1):
     self.draw_point(i, j, color = fillcolor)


 def _color_dist(self, color1, color2):
  ''' Finds the "closeness" of `color1` from `color2`, as if they are points in 3-D space. '''
  r1, b1, g1, r2, b2, g2 = *color1, *color2
  return ((r2 - r1)**2 + (g2 - g1)**2 + (b2 - b1)**2)**0.5

 def smoothen(self, curve, array = None):
 # array param necessary for later works
  if type(array) == type(None):
   array = self.mutarr
  if curve not in self.curvesets:
   raise NameError('no curve named %s exists'%curve)

  for pxl3 in self.curvesets[curve].keys():
   x, y = self.pilcoords(*pxl3)
   curve_color = array[x][y]
   if list(curve_color) == [255]*3:
    print(pxl3, 'what this x&y?')
    print(self.curvesets[curve].keys())
    raise
   print(curve_color, 'curve\'s color')
   break
  # curve's periphery is to be determined

  neintensity = {}              # map from point (on periphery) to number of non-diagonal neighbours in the curve (1-4, 0 not possible)
  borderdict = {}          # dict search is much faster than list search

  for pxl in self.curvesets[curve]:
   for neigh in self.neighbourhood(pxl, curve, within = False, diagonal = False):
    if neigh not in self.curvesets[curve]:
     borderdict[neigh] = True

  for borderpix in borderdict:
   edgecount = 0
   for neigh in self.neighbourhood(borderpix, diagonal = False):
    if neigh in self.curvesets[curve]:
     edgecount += 1
   neintensity[borderpix] = edgecount

  print(len(neintensity))
  print(len(borderdict))

  for borderpix in neintensity:
   if neintensity[borderpix] >= 2:
   # determine direction of gradient flow, and whether if gradient is to be flown from both ways
    for neigh in self.neighbourhood(borderpix, diagonal = False):
    # simpler to do all the drawing work in this for-loop for each of the neighs
     if neigh in neintensity:                                   # instead of try-except blocks, dict search beforehand can also be used
      if neintensity[neigh] >= 1:
       # some data structure to store info of which pixels are to be gradiented for each particular neigh
       gradlist = []               # will be remade for each neigh of borderpix
       bx, by = borderpix
       bordx, bordy = neigh[0] - bx, neigh[1] - by
       gradlist.append(borderpix)
       while (bx+bordx, by+bordy) in neintensity:             # keys of borderdict and neintensity are same
        gradlist.append((bx+bordx, by+bordy))
        if bordx != 0:
         bordx += bordx//abs(bordx)
        if bordy != 0:
         bordy += bordy//abs(bordy)

       if neintensity[gradlist[0]] == 2 and neintensity[gradlist[-1]] == 2:
       # check for two-way gradient flow
        halfpoint = (len(gradlist)+1)//2
        gradhalf1 = gradlist[:halfpoint]
        if len(gradlist)%2 == 0:
         gradhalf2 = gradlist[-1:halfpoint-1:-1]
        else:
         gradhalf2 = gradlist[-1:halfpoint-2:-1]
        if len(gradhalf1) != len(gradhalf2):
         raise RuntimeError('paglagaye hai sab')
        grad_colors = self._color_tendify(gradhalf1, color = curve_color)
        cols_and_poses = list(zip(grad_colors, gradhalf1)) + list(zip(grad_colors, gradhalf2))
        for cap in cols_and_poses:
         x, y = self.pilcoords(*cap[1])
         pre_color = array[y][x]
         if self._color_dist(pre_color, curve_color) > self._color_dist(cap[0], curve_color):
          self.draw_point(*cap[1], color = cap[0])
       else:
        grad_colors = self._color_tendify(gradlist, color = curve_color)
        cols_and_poses = list(zip(grad_colors, gradlist))
        for cap in cols_and_poses:
         x, y = self.pilcoords(*cap[1])
         pre_color = array[y][x]
         if self._color_dist(pre_color, curve_color) > self._color_dist(cap[0], curve_color):
          self.draw_point(*cap[1], color = cap[0])

    # should pixels with neintensity value 4 be colored the curve color, or be tendified towards self.bg_color?
    corner_col = self._color_tendify([borderpix], color = curve_color)[0]
    x, y = self.pilcoords(*borderpix)
    pre_color = array[y][x]
    if self._color_dist(pre_color, curve_color) > self._color_dist(corner_col, curve_color):
     self.draw_point(*borderpix, color = corner_col)


 def neighbourhood(self, point, curveset = None, within = False, diagonal = True):
  # `within` param specifies if the pixels only within the curve are to be considered
  if not curveset and within:
   raise ValueError('`within` must be given with a curvename')
  if within:
   if point not in self.curvesets[curveset]:
    print(point, 'strange point')
    raise ValueError('The pixel isn\'t itself in the hood')
  neighs = []
  x, y = point
  if within:
   if diagonal:
    for i in [-1, 0, 1]:
     for j in [-1, 0, 1]:
      if (x+i, y+j) in self.curvesets[curveset]:
       neighs.append((x+i, y+j))
   else:
    for i in [-1, 1]:
     if (x+i, y) in self.curvesets[curveset]:
      neighs.append((x+i, y))
    for j in [-1, 1]:    
     if (x, y+j) in self.curvesets[curveset]:
      neighs.append((x, y+j))
  else:
   if diagonal:
    for i in [-1, 0, 1]:
     for j in [-1, 0, 1]:
      neighs.append((x+i, y+j))
   else:
    for i in [-1, 1]:
     neighs.append((x+i, y))
    for j in [-1, 1]:    
     neighs.append((x, y+j))
  if (x, y) in neighs:
   neighs.remove((x, y))
  return neighs   

 def homeomorph(self, curve1, curve2, mainpoint1, mainpoint2, steps = 50, direction1 = None, direction2 = None):
  # direction param is to be string of; one of u, d, l, r (up, down, ...)
  # (there is a need for direction)
  size1, size2 = len(self.curvesets[curve1]), len(self.curvesets[curve2])
  print('sizes', size1, size2)
  bigsize = max(size1, size2)
  minisize = min(size1, size2) 

  def unpiler(count1, count2):         # if count2 > count1, count2 keeps decreasing till they are equal. count2 must be > 0
   ratio_bag = []
   n1 = count1
   n2 = count2
   while n2 > 1:
    diff = (n1//n2)
    ratio_bag.append(diff)
    n1 -= diff
    n2 -= 1
   ratio_bag.append(n1)
   return ratio_bag

  size_bag = unpiler(bigsize, minisize)          # to keep track of how many pixels of curve1 should map to one pixel of curve2
  correspondance = {}               # keys the points of curve1 (tuple of tuples), and values points of curve2 (tuple of tuples)

  # first the case of open curves, it is to be ensured that the end point is chosen, for satisfaction
  marked1_dict = dict(zip([pxl for pxl in self.curvesets[curve1]], [False]*size1))
  marked2_dict = dict(zip([pxl for pxl in self.curvesets[curve2]], [False]*size2))
  
  neighwise1_constructer = [mainpoint1]
  neighwise2_constructer = [mainpoint2]
  neighbourwise1 = []
  neighbourwise2 = []

  crossed1_pxls = []
  if direction1:    # same for direction2
   waydict = {'u':(0, 1), 'd':(0, -1), 'l':(-1, 0), 'r':(1, 0)}
   if waydict[direction1][0] == 0:
   # case of horizontal crossed pixels
    upordown = waydict[direction1][1]
    thick_check_count = 0                      # to move back and forth, sweeping all pixels along the thickness of curve
    mp1x, mp1y = mainpoint1
    while (mp1x + thick_check_count, mp1y + upordown) in self.curvesets[curve1] or (mp1x - thick_check_count, mp1y + upordown) in self.curvesets[curve1]:
     if (mp1x + thick_check_count, mp1y + upordown) in self.curvesets[curve1]:
      crossed1_pxls.append((mp1x + thick_check_count, mp1y + upordown))
     if (mp1x - thick_check_count, mp1y + upordown) in self.curvesets[curve1]:
      crossed1_pxls.append((mp1x - thick_check_count, mp1y + upordown))
     thick_check_count += 1
   else:
   # case of vertical crossed pixels
    leforig = waydict[direction1][0]
    thick_check_count = 0
    mp1x, mp1y = mainpoint1
    while (mp1x + leforig, mp1y + thick_check_count) in self.curvesets[curve1] or (mp1x + leforig, mp1y + thick_check_count) in self.curvesets[curve1]:
     if (mp1x + leforig, mp1y + thick_check_count) in self.curvesets[curve1]:
      crossed1_pxls.append((mp1x + leforig, mp1y + thick_check_count))
     if (mp1x + leforig, mp1y - thick_check_count) in self.curvesets[curve1]:
      crossed1_pxls.append((mp1x + leforig, mp1y - thick_check_count))
     thick_check_count += 1

  crossed2_pxls = []
  if direction2:
   waydict = {'u':(0, 1), 'd':(0, -1), 'l':(-1, 0), 'r':(1, 0)}
   if waydict[direction2][0] == 0:
   # case of horizontal crossed pixels
    upordown = waydict[direction2][1]
    thick_check_count = 0
    mp2x, mp2y = mainpoint2
    while (mp2x + thick_check_count, mp2y + upordown) in self.curvesets[curve2] or (mp2x - thick_check_count, mp2y + upordown) in self.curvesets[curve2]:
     if (mp2x + thick_check_count, mp2y + upordown) in self.curvesets[curve2]:
      crossed2_pxls.append((mp2x + thick_check_count, mp2y + upordown))
     if (mp2x - thick_check_count, mp2y + upordown) in self.curvesets[curve2]:
      crossed2_pxls.append((mp2x - thick_check_count, mp2y + upordown))
     thick_check_count += 1
   else:
   # case of vertical crossed pixels
    leforig = waydict[direction2][0]
    thick_check_count = 0
    mp2x, mp2y = mainpoint2
    while (mp2x + leforig, mp2y + thick_check_count) in self.curvesets[curve2] or (mp2x + leforig, mp2y + thick_check_count) in self.curvesets[curve2]:
     if (mp2x + leforig, mp2y + thick_check_count) in self.curvesets[curve2]:
      crossed2_pxls.append((mp2x + leforig, mp2y + thick_check_count))
     if (mp2x + leforig, mp2y - thick_check_count) in self.curvesets[curve2]:
      crossed2_pxls.append((mp2x + leforig, mp2y - thick_check_count))
     thick_check_count += 1

  print(crossed2_pxls)
  print('crossed2_pxls')
  # now to employ safety count in case of direction(s)

  marked1_dict[mainpoint1] = True
  neighbourwise1.append(mainpoint1)
  marked1_count = 1
  while marked1_count < size1:
   temp_neigh1_list = []
   for pxl in neighwise1_constructer:
    neighbours1 = self.neighbourhood(pxl, curve1)
    for neighbour in neighbours1:
     if direction1:
      if not marked1_dict[neighbour] and neighbour not in crossed1_pxls:
       neighbourwise1.append(neighbour)
       temp_neigh1_list.append(neighbour)
       marked1_dict[neighbour] = True
       marked1_count += 1
      if not marked1_dict[neighbour] and neighbour in crossed1_pxls and marked1_count > 0.5*size1:
       neighbourwise1.append(neighbour)
       temp_neigh1_list.append(neighbour)
       marked1_dict[neighbour] = True
       marked1_count += 1

     else:
      if not marked1_dict[neighbour]:
       neighbourwise1.append(neighbour)
       temp_neigh1_list.append(neighbour)
       marked1_dict[neighbour] = True
       marked1_count += 1
   neighwise1_constructer = temp_neigh1_list


  marked2_dict[mainpoint2] = True
  neighbourwise2.append(mainpoint2)
  marked2_count = 1
  while marked2_count < size2:
   temp_neigh2_list = []
   for pxl in neighwise2_constructer:
    neighbours2 = self.neighbourhood(pxl, curve2)
    for neighbour in neighbours2:
     if direction2:
      if not marked2_dict[neighbour] and neighbour not in crossed2_pxls:
       neighbourwise2.append(neighbour)
       temp_neigh2_list.append(neighbour)
       marked2_dict[neighbour] = True
       marked2_count += 1
      if not marked2_dict[neighbour] and neighbour in crossed2_pxls and marked2_count > 0.5*size2:
       neighbourwise2.append(neighbour)
       temp_neigh2_list.append(neighbour)
       marked2_dict[neighbour] = True
       marked2_count += 1

     else:
      if not marked2_dict[neighbour]:
       neighbourwise2.append(neighbour)
       temp_neigh2_list.append(neighbour)
       marked2_dict[neighbour] = True
       marked2_count += 1
   neighwise2_constructer = temp_neigh2_list

  print(neighbourwise2)
  print('neighbourwise2', len(neighbourwise2))

  if bigsize == size1:
  # iterate through each pixel of curve2
   corr_index = 0                      # index to change when enough pixels corresponding to one point in curve2 have been visited
   while corr_index < len(size_bag):
    active1_pxls = []
    while len(active1_pxls) < size_bag[corr_index]:
     active1_pxls.append(neighbourwise1[0])
     del neighbourwise1[0]
    correspondance[tuple(active1_pxls)] = (neighbourwise2[corr_index],)       # many to one
    corr_index += 1

  else:
   # iterate through each pixel of curve1, in else block means size2 > size1
   corr_index = 0
   while corr_index < len(size_bag):
    active2_pxls = []
    while len(active2_pxls) < size_bag[corr_index]:                           # len(size_bag) always equal to count2
     active2_pxls.append(neighbourwise2[0])
     del neighbourwise2[0]
    correspondance[(neighbourwise1[corr_index],)] = tuple(active2_pxls)       # one to many 
    corr_index += 1

  # now to obtain homeomorph motions derived from duparr, according to `steps` parameter 
  def xysteps_stepper(xdif, ydif, steps):

   if xdif == 0:
    x_steppings = [0]*steps
   elif xdif == 1:
    x_steppings = [1] + [0]*(steps-1)
   elif xdif == -1:
    x_steppings = [-1] + [0]*(steps-1)
   
   elif abs(xdif) >= steps:
    x_steppings = unpiler(xdif, steps)
   else:                                               # in else block means steps > abs(xdif)
    if xdif > 0:
     sign_xdif = 1
    else:
     sign_xdif = -1
    xsteps = steps
    xstepdiffs = unpiler(steps, abs(xdif))                   # this has len abs(xdif)
    marked_xsteps = []
    for xdiff in xstepdiffs:
     xsteps -= xdiff
     marked_xsteps.append(xsteps)                            # so marked_xsteps also has abs(xdif)
    x_steppings = []
    for i in range(steps):
     if i in marked_xsteps:
      x_steppings.append(sign_xdif)
     else:
      x_steppings.append(0)                                  # but this always has len steps

   if ydif == 0:
    y_steppings = [0]*steps
   elif ydif == 1:
    y_steppings = [1] + [0]*(steps-1)
   elif ydif == -1:
    y_steppings = [-1] + [0]*(steps-1)
   
   elif abs(ydif) >= steps:
    y_steppings = unpiler(ydif, steps)
   else:
    if ydif > 0:
     sign_ydif = 1
    else:
     sign_ydif = -1
    ysteps = steps
    ystepdiffs = unpiler(steps, abs(ydif))
    marked_ysteps = []
    for ydiff in ystepdiffs:
     ysteps -= ydiff
     marked_ysteps.append(ysteps)
    y_steppings = []
    for i in range(steps):
     if i in marked_ysteps:
      y_steppings.append(sign_ydif)
     else:
      y_steppings.append(0)

   return x_steppings, y_steppings


  # now time for omega computation, might be too heavy
  supermassive_list = []
  for key in correspondance:                                   # key will always be a tuple
   if len(correspondance[key]) > 1:                            # in this block means size1 < size2
    print(correspondance[key], 'corr of key', key)
    pxl = key[0]
    x1, y1 = pxl
    for val in correspondance[key]:
     destination = val
     x2, y2 = destination

     x_pxl_motion, y_pxl_motion = xysteps_stepper(x2-x1, y2-y1, steps)        # both have length steps
     # BUG: x2-x1 & y2-y1 not what they are supposed to be  ## patched ##

     x_pxl_poses = []                                                         # so this
     y_pxl_poses = []                                                         # and this will also have length steps
     xd = x1
     for xdif in x_pxl_motion:
      xd += xdif
      x_pxl_poses.append(xd)
     yd = y1
     for ydif in y_pxl_motion:
      yd += ydif
      y_pxl_poses.append(yd)

     supermassive_list.append(list(zip(x_pxl_poses, y_pxl_poses)))                  # list of zip also has length steps

   else:
    for pxl in key:
     destination = correspondance[key][0]
     x1, y1 = pxl
     x2, y2 = destination
     x_pxl_motion, y_pxl_motion = xysteps_stepper(x2-x1, y2-y1, steps)
     x_pxl_poses = []
     y_pxl_poses = []
     for xdif in x_pxl_motion:
      x1 += xdif
      x_pxl_poses.append(x1)
     for ydif in y_pxl_motion:
      y1 += ydif
      y_pxl_poses.append(y1)

     supermassive_list.append(list(zip(x_pxl_poses, y_pxl_poses)))


  # copies of mutarr are needed, as outputting images might not be ideal, mutarrs allow further modification
  homeo_mutarrlist = []

  for i in range(steps):
   duparr = np.copy(self.mutarr)
   for poses in supermassive_list:
    x, y = poses[i]
    x, y = self.pilcoords(x, y)
    duparr[y][x] = [0, 255, 0]
   homeo_mutarrlist.append(duparr)

  return homeo_mutarrlist


  if direction1:
   pass   
  

 def draw_circle(self, radius, centre = None, thickness = 1, filled = False, edgecolor = None, color = [0]*3, curvename = None):
  if centre == None:
   centre = 0, 0
  cx, cy = centre

  if edgecolor == None:
   edgecolor = color

  if curvename:
   try:
    self.curvesets[curvename]
   except:
    self.curvesets[curvename] = {}
  for x in range(-radius-thickness + cx, radius + thickness + cx + 1):
   for y in range(-radius-thickness + cy, radius + thickness + cy + 1):
    if (radius-1)**2 <= (x-cx)**2 + (y-cy)**2 < (radius + thickness)**2:
     self.draw_point(x, y, color = edgecolor)
     if curvename:
      self.curvesets[curvename][(x, y)] = True
    if filled:
     if (x-cx)**2 + (y-cy)**2 < (radius-1)**2:
      self.draw_point(x, y, color = color)    
      if curvename:
       self.curvesets[curvename][(x, y)] = True

 def writext(self, text, xpos = None, ypos = None, arr = None, fontcolor = 'black', font = 'arial'):
  if type(arr) == None:
   arr = self.mutarr
  file_codename = r'tempims\\___drawer_tempim%.4d___.png'%self.tempim_modcount
  self.create_im(arr).save(file_codename)
  if xpos == None:
   xpos = self.centre[0]
  if ypos == None:
   ypos = self.centre[1]

  xpos, ypos = self.pilcoords(xpos, ypos)

  cmd = f'ffmpeg -i {file_codename} -vf "drawtext=fontfile=C\\\:/Windows/Fonts/{font}.ttf:fontsize=20:fontcolor={fontcolor}:x={xpos}:y={ypos}:text=\'{text}\'" C:\\Users\\VizDr\\OneDrive\\Desktop\\codes\\PIL\\tempims\\___drawer_out%.4d.png'%self.tempim_modcount
  self.tempim_modcount += 1
  os.popen(cmd)
  # the parsing (?) of this command raises a SyntaxWarning, avoided by either `-W ignore` flag in CLI or by importing warnings

 # 2/8/2025. Changing create_im to default to self.mutarr, rather than be limited only to self.mutarr
 def create_im(self, arr = None):
  if type(arr) == type(None):
   arr = self.mutarr
  imarr = np.array(arr, dtype = np.uint8)                   # imarr, having dtype uint8 doesn't support integer assignment (why?)
  im = Image.fromarray(imarr)
  return im



class myTurtle(Position):

 def __init__(self, other, pos = None, face = np.pi/2):
  self.face = face
  self.origin = other.origin 
  self.rows, self.cols = other.size
  self.mutarr = other.mutarr
  self.bg_color = other.bg_color
  if type(pos) == type(None):
   self.pos = (0, 0)                         # position of the origin
  else:
   self.pos = pos                            # position w.r.t. the origin
  self.truepos = self.pos                    # `truepos` created to avoid error build-up
  self.bigcolm = other.bigcolm
  self.mutarr = other.mutarr
  self.turtpixes = []

 def move(self, path_type, color = [0, 0, 0]):
  if type(path_type) == str and path_type[1] == 'x':
   self.move_nsew(path_type, color = color)
  elif type(path_type) == str and 'a' in path_type:
   self.move_direction(path_type, color = color)
  elif type(path_type) == str and 'a' not in path_type:
   self.move_direction(path_type + 'a+0', color = color)

 def move_direction(self, path, color):
  path_length, direction = path.split('a')
  path_length = int(path_length)               # necessity of int to be enquired
  if direction[0] in ['+', '-']:
   self.face += float(direction)
  else:
   self.face = float(direction)
  newpos = self.truepos[0] + path_length*np.cos(self.face), self.truepos[1] + path_length*np.sin(self.face)         
  # choice of `newpos` being on integer lattice
  self.line_segment(self.truepos, newpos, color = color)
  self.truepos = newpos
  self.pos = int(newpos[0]//1), int(newpos[1]//1)

 def move_nsew(self, path, color):

  # directions : 'u' (up), 'd' (down), 'l' (left), 'r' (right)
  num_directions = {'u':(0, 1), 'd':(0, -1), 'l':(-1, 0), 'r':(1, 0)}
  direction, path_length = path.split('x')
  path_length = int(path_length)
  direction = num_directions[direction]
  pxllist = []
  took_steps = 0
  while took_steps < path_length:
   if self.in_bound(self.pos):
    pxllist.append(self.pos)
   took_steps += 1
   self.pos = (self.pos[0] + direction[0], self.pos[1] + direction[1])
  
  for pxl in pxllist:
   self.draw_point(*pxl, color = color)

 def shift(self, *newpos_shift):
  newpos = self.pos[0] + newpos_shift[0], self.pos[1] + newpos_shift[1]
  newtruepos = self.truepos[0] + newpos_shift[0], self.truepos[1] + newpos_shift[1]
  if self.in_bound(newpos):
   self.pos = newpos
   self.truepos = newtruepos
  else:
   Warning('Can\'t shift outside boundary')

 def turtle_out_of_shell(self):

  if self.turtpixes != []:
   # work, no need for else block
   for pixes in self.turtpixes:
    pilxy, pixel = pixes
    pilx, pily = pilxy
    self.mutarr[pily][pilx] = np.array(pixel)
   self.turtpixes = []

  dum_origin = self.origin

  y, x = self.pilcoords(*self.pos)
  self.origin = x, y
  #work
  turtle_body = [(0, 6), (0, 7), (0, 8), (-1, 6), (-1, 7), (-1, 8), (-2, 5), (-2, 4), (-1, 5), (-1, 4), (0, 5), (0, 4), (1, 5), (1, 4), (-2, 3), (-2, 2), (-1, 3), (-1, 2), (0, 3), (0, 2), (1, 3), (1, 2), (-2, 1), (-2, 0), (-1, 1), (-1, 0), (0, 1), (0, 0), (1, 1), (1, 0), (-2, -1), (-1, -1), (0, -1), (1, -1), (-2, -2), (-3, -2), (-3, -3), (-4, -4), (1, -2), (2, -2), (2, -3), (2, -4), (2, -5), (2, 1), (2, 2), (2, 3), (3, 3), (3, 4), (4, 3), (4, 4), (5, 4), (5, 5), (5, 6), (5, 7), (-3, 1), (-3, 2), (-3, 3), (-4, 3), (-5, 3), (-5, 4), (-5, 5), (-6, 5), (-6, 6)]
  # list of points that encapsulate the turtle's body's graphics

  for pxl in turtle_body:
   x, y = pxl
   mag = (x**2 + y**2)**0.5
   if mag == 0:
    pilpoint = self.pilcoords(int(x//1), int(y//1))
    mutcol = list(self.mutarr[pilpoint[1]][pilpoint[0]])
    if mutcol != self.bg_color:
   
     self.turtpixes.append((pilpoint, mutcol))
    self.draw_point(int(x//1), int(y//1), color = [100]*3)
   else:
    cos_ang = x/mag
    sin_ang = y/mag
    rot_ang = self.face - np.pi/2
    new_x = (np.cos(rot_ang)*cos_ang - np.sin(rot_ang)*sin_ang)*mag
    new_y = (np.sin(rot_ang)*cos_ang + np.cos(rot_ang)*sin_ang)*mag
    pilpoint = self.pilcoords(int(new_x//1), int(new_y//1)) 
    mutcol = list(self.mutarr[pilpoint[1]][pilpoint[0]])
    if mutcol != self.bg_color:
     print(mutcol, type(mutcol), self.bg_color, type(self.bg_color))
     self.turtpixes.append((pilpoint, mutcol))
    if self.in_bound((int(new_x//1), int(new_y//1))):
     self.draw_point(int(new_x//1), int(new_y//1), color = [100]*3)              # turtle's default color is [100, 100, 100]
  self.origin = dum_origin                                 # to not confuse further draws
  print('Origin reverted back to (%d, %d)'%self.origin)





Op = Position((1080, 1920))

# left & right x margins: 80, 80
# top & bottom y margins: 100, 250 (still 400 y space would remain)

Op.draw_box(0, 0, 100)
Op.writext('Pb', 50, 50)

Op.create_im().show()
