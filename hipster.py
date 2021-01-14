#####################################################################################
# HIPSTER - Homogeneous to Inhomogeneous rock Properties for Stress TEnsor Research	#
# Version 1.3																		#
# License: GPLv3																	#
# Moritz O. Ziegler - mziegler@gfz-potsdam.de										#
# Manual: http://github.com/MorZieg/HIPSTER											#
# Download: http://github.com/MorZieg/HIPSTER										#
#####################################################################################
import numpy as np

class rock:
 def __init__(self, unit, E, E_sig, nu, nu_sig, rho, rho_sig):
  self.unit = unit
  self.E = E
  self.E_sig = E_sig
  self.nu = nu
  self.nu_sig = nu_sig
  self.rho = rho
  self.rho_sig = rho_sig

#####################################################################################
# 									USER INPUT 										#
#####################################################################################
input_geometry = 'mwe_elements_elset.set'

distrib = 'normal'
strata = ['Top','Bottom']
output_name = 'test'
solver = 'abaqus'

Top = rock('Top',25E9,0,0.25,0,2500,0)
Bottom = rock('Bottom',25E9,2.5E9,0.25,0.1,2500,500)


#####################################################################################
def main(input_geometry,strata,distrib,output_name,solver):
 check(input_geometry,strata,distrib,output_name,solver)
 
 print ('Running HIPSTER v1.3')
 
 # Reading the input files and assign the corrseponding elements or element-sets to a variable
 if input_geometry[-9:] == 'elset.inp' or input_geometry[-10:] == 'elset.geom':
  # Expected to assign material properties to element sets provided by an Abaqus input file.
  print('Reading element set definitions from Abaqus *.inp or *.geom file')
  set = input_elsets(input_geometry)
  
 elif input_geometry[-3:] == 'inp' or input_geometry[-4:] == 'geom':
  # Expected to assign material properties to elements provided by an Abaqus input file.
  print('Reading element definitions from Abaqus *.inp or *.geom file')
  [elems,set] = input_elems(input_geometry)
  
 elif input_geometry[-9:] == 'elset.set':
  # Expected to assign material properties to element sets provided by an APPLE PY output file.
  print('Reading element set definitions from APPLE PY elements *.set file')
  set = set_elsets(input_geometry)
  
 elif input_geometry[-3:] == 'set':
  # Expected to assign material properties to elements provided by an APPLE PY output file.
  print('Reading element definitions from APPLE PY elements *.set file')
  [elems,set] = set_elems(input_geometry)
  
 else:
  print('ERROR! Specify a valid input type.')
 
 # Assign material properties and write to file.
 # Here it is distinguished whether a Moose or an Abaqus output is required.
 # The same function can be used for element-wise or element-set-wise assignment. The variable elems is only required for element-wise assignment.
 if solver == 'abaqus':
  print('Writing Abaqus File.')
  if input_geometry[-9:] == 'elset.inp' or input_geometry[-10:] == 'elset.geom' or input_geometry[-9:] == 'elset.set':
   print('Assigning material properties element-set-wise.')
   write_abq_file(strata,distrib,output_name,set)
   
  elif input_geometry[-3:] == 'inp' or input_geometry[-4:] == 'geom' or input_geometry[-3:] == 'set':
   print('Assigning material properties element-wise.')
   write_abq_file(strata,distrib,output_name,set,elems)
  
  
 elif solver == 'moose':
  print('Writing Moose File.')
  if input_geometry[-9:] == 'elset.inp' or input_geometry[-10:] == 'elset.geom' or input_geometry[-9:] == 'elset.set':
   print('Assigning material properties element-set-wise.')
   write_mse_file(strata,distrib,output_name,set)
   
  elif input_geometry[-3:] == 'inp' or input_geometry[-4:] == 'geom' or input_geometry[-3:] == 'set':
   print('Assigning material properties element-wise.')
   write_mse_file(strata,distrib,output_name,set,elems)
 
 print('Material properties successfully assigned!')
 
#####################################################################################
def check(input_geometry,strata,distrib,output_name,solver):
 # Checking input data
 import sys
 
 if distrib != 'normal' and distrib != 'uniform':
  print('ERROR! Please specify a supported distribution of material properties.')
  sys.exit()
 
 if '.' in output_name:
  print('ERROR! The variable \"output_name\" must not include a file extension.')
  sys.exit()
 
 if solver != 'abaqus' and solver != 'moose':
  print('ERROR! Please specify a supported solver.')
  sys.exit()
 
#####################################################################################
# 			Assignment of material properties and writing of material files			#
#####################################################################################
def write_abq_file(strata,distrib,output_name,set,elems=None):
 
 ## Assign material properties to elements
 print('Start assignment of material properties')
 
 # Create material files for both lithostatic and calibrated model runs.
 mat_ini = open(output_name + '_lithostatic.mat','w')
 mat_ini.write('** Inhomogeneous material properties for lithostatic stress state\n** Created by HIPSTER v1.3 - http://github.com/MorZieg/hipster\n** %s\n**\n** Material definitions\n' % str(np.datetime64('now')))
 
 mat_fin = open(output_name + '.mat','w')
 mat_fin.write('** Inhomogeneous material properties\n** Created by HIPSTER v1.3 - http://github.com/MorZieg/hipster\n** %s\n**\n** Material definitions\n' % str(np.datetime64('now')))
 
 # Define output syntax.
 mat = '*MATERIAL, NAME=rock_%s\n*ELASTIC, TYPE = ISOTROPIC\n%.8g, %.3f, 0.0\n*DENSITY\n%.0f\n**\n'
 sosi = '*SOLID SECTION,ELSET=%s, MATERIAL=rock_%s\n'
 sede = '*ELSET, ELSET=%s_%s\n%s\n'
 headline = '**\n** %s\n**\n'
 
 subset = create_subset(strata,set,elems)
 
 # Draw values from distribution and write material definition
 for x,n in enumerate(strata):
  print('Unit: ' + n)
  
  mat_fin.write(headline % n)
  mat_ini.write(headline % n)
  
  E = eval(n + '.E')
  E_sig = eval(n + '.E_sig')
  nu = eval(n + '.nu')
  nu_sig = eval(n + '.nu_sig')
  rho = eval(n + '.rho')
  rho_sig = eval(n + '.rho_sig')

  if E_sig == 0 and nu_sig == 0 and rho_sig == 0:
   # If the variability in one unit is 0 in all three properties, only one material is created.
   mat_ini.write(mat % (n, E, 0.49, rho))
   mat_fin.write(mat % (n, E, nu, rho))
  else:
   for i,el in enumerate(subset[x]):
    if distrib == 'normal':
     E_elem,nu_elem,rho_elem = normal_distrib(E,E_sig,nu,nu_sig,rho,rho_sig)
    elif distrib =='uniform':
     E_elem,nu_elem,rho_elem = uniform_distrib(E,E_sig,nu,nu_sig,rho,rho_sig)
    
    mat_ini.write(mat % (el, E_elem, 0.49, rho_elem))
    mat_fin.write(mat % (el, E_elem, nu_elem, rho_elem))
 
 if elems is not None:
  # Create an element set per element. This is only required if the materials are element-wise assigned.
  mat_fin.write(headline % 'Element sets')
  mat_ini.write(headline % 'Element sets')
  for x,n in enumerate(set):
   if eval(n + '.E_sig') != 0 or eval(n + '.nu_sig') != 0 or eval(n + '.rho_sig') != 0:
    mat_fin.write(headline % n)
    mat_ini.write(headline % n)
    for _,el in enumerate(elems[x]):
     mat_ini.write(sede % (n, el, el))
     mat_fin.write(sede % (n, el, el))
 
 # Write solid section.
 mat_fin.write(headline % 'Solidsections')
 mat_ini.write(headline % 'Solidsections')
 for x,n in enumerate(strata):
  mat_fin.write(headline % n)
  mat_ini.write(headline % n)
  if eval(n + '.E_sig') == 0 and eval(n + '.nu_sig') == 0 and eval(n + '.rho_sig') == 0:
   if elems is None:
    for i,el in enumerate(subset[x]):
     mat_ini.write(sosi % (el,n))
     mat_fin.write(sosi % (el,n))
   else:
    mat_ini.write(sosi % (n,n))
    mat_fin.write(sosi % (n,n))
  else:
   for i,el in enumerate(subset[x]):
    mat_ini.write(sosi % (el,el))
    mat_fin.write(sosi % (el,el))
 
 mat_fin.close()
 mat_ini.close()
 
#####################################################################################
def write_mse_file(strata,distrib,output_name,set,elems=None):
 
 # Assign material properties to elements
 print('Start assignment of material properties')
 
 # Currently HIPSTER only supports hexahedral elements in Moose.
 print('ATTENTION! For Moose HIPSTER currently only supports hexahedral elements (HEX8).')
 eltype = 'HEX8'
 
 # Create material files for both lithostatic and calibrated model runs.
 mat_ini = open(output_name + '_lithostatic.txt','w')
 mat_ini.write('# Inhomogeneous material properties for lithostatic stress state\n# Created by HIPSTER v1.3 - http://github.com/MorZieg/hipster\n# %s\n#\n[Material]\n' % str(np.datetime64('now')))
 
 mat_fin = open(output_name + '.txt','w')
 mat_fin.write('# Inhomogeneous material properties\n# Created by HIPSTER v1.3 - http://github.com/MorZieg/hipster\n# %s\n#\n[Material]\n' % str(np.datetime64('now')))
 
 # Define output syntax.
 ep = '  [%s_Young_Poisson]\n type = ComputeIsotropicElasticityTensor\n block = \'%s_%s\'\n youngs_modulus = %.6g\n poissons_ratio = %.3f\n  []\n'
 dens = '  [%s_dens]\n type = GenericConstantMaterial\n block = \'%s_%s\'\n prop_names = density\n prop_values = %.0f\n  []\n'
 
 subset = create_subset(strata,set,elems)
 
 # Draw values from distribution and write material definition
 for x,n in enumerate(strata):
  print('Unit: ' + n)
  
  E = eval(n + '.E')
  E_sig = eval(n + '.E_sig')
  nu = eval(n + '.nu')
  nu_sig = eval(n + '.nu_sig')
  rho = eval(n + '.rho')
  rho_sig = eval(n + '.rho_sig')
  
  if E_sig == 0 and nu_sig == 0 and rho_sig == 0 and elems is not None:
   # If the variability in one unit is 0 in all three properties, only one material is created.
   mat_ini.write(ep % (n, n, eltype, E, 0.49))
   mat_ini.write(dens % (n, n, eltype, rho))
   
   mat_fin.write(ep % (n, n, eltype, E, nu))
   mat_fin.write(dens % (n, n, eltype, rho))
   
  else:
   for i,elset in enumerate(subset[x]):
    if distrib == 'normal':
     E_elem,nu_elem,rho_elem = normal_distrib(E,E_sig,nu,nu_sig,rho,rho_sig)
    elif distrib =='uniform':
     E_elem,nu_elem,rho_elem = uniform_distrib(E,E_sig,nu,nu_sig,rho,rho_sig)
    mat_ini.write(ep % (elset, elset, eltype, E_elem, 0.49))
    mat_ini.write(dens % (elset, elset, eltype, rho_elem))
    
    mat_fin.write(ep % (elset, elset, eltype, E_elem, nu_elem))
    mat_fin.write(dens % (elset, elset, eltype, rho_elem))
 
 mat_ini.write('  [stress]\n type = ComputeLinearElasticStress\n  []\n[]\n')
 mat_fin.write('  [stress]\n type = ComputeLinearElasticStress\n  []\n[]\n')
 
 mat_fin.close()
 mat_ini.close()
 
 if elems is not None:
  #Create an element set per element
  new_elsets = open(output_name + '_elsets.inp','w')
  new_elsets.write('** Element sets\n')
  for x,n in enumerate(set):
   if eval(n + '.E_sig') != 0 or eval(n + '.nu_sig') != 0 or eval(n + '.rho_sig') != 0:
    new_elsets.write('**\n** %s\n**\n' % n)
    for _,el in enumerate(elems[x]):
     new_elsets.write('*ELSET, ELSET=%s_%s\n%s\n' % (n, el, el))
  new_elsets.close()
 
#####################################################################################
def create_subset(strata,set,elems=None):
 # Create or extract the subsets for individual material properties assignment.
 subset = [[] for x in range(len(strata))]
 
 if elems is None:
  for i,n in enumerate(strata):
   for j, m in enumerate(set):
    if n in m:
     subset[i].append(m)
  
 else:
  for i,n in enumerate(strata):
   for j,m in enumerate(set):
    if n in m:
     for k,o in enumerate(elems[j]):
      subset[i].append(m + '_' + str(o))
 
 return subset
 
#####################################################################################
def normal_distrib(E,E_sig,nu,nu_sig,rho,rho_sig):
 # Draw material properties from a normal distribution specified by the user.
 # A sanity check of the material properties is performed.
 # Young's module and Density must not be negative. Poisson ratio has to be >0 and <=0.49.
 while True:
  if E_sig == 0:
   check = E
  else:
   check = np.random.normal(E,E_sig)

  if check > 0:
   E_elem = check
   break
 
 while True:
  if nu_sig == 0:
   check = nu
  else:
   check = np.random.normal(nu,nu_sig)

  if check > 0 and check <= 0.49:
   nu_elem = check
   break
 
 while True:
  if rho_sig == 0:
   check = rho
  else:
   check = np.random.normal(rho,rho_sig)
  
  if check > 0:
   rho_elem = check
   break
 
 return E_elem, nu_elem, rho_elem
 
#####################################################################################
def uniform_distrib(E,E_sig,nu,nu_sig,rho,rho_sig):
 # Draw material properties from a range specified by the user.
 # A sanity check of the material properties is performed.
 # Young's module and Density must not be negative. Poisson ratio has to be >0 and <=0.49.
 while True:
  check = np.random.uniform(E - E_sig,E + E_sig,1)
  if check > 0:
   E_elem = check
   break
 
 while True:
  check = np.random.uniform(nu - nu_sig,nu + nu_sig,1)
  if check > 0 and check <= 0.49:
   nu_elem = check
   break
 
 while True:
  check = np.random.uniform(rho - rho_sig,rho + rho_sig,1)
  if check > 0:
   rho_elem = check
   break
 
 return E_elem, nu_elem, rho_elem
 
#####################################################################################
# 						Reading elements and element sets							#
#####################################################################################
def input_elems(input_geometry):
 # Read Element Definitions from the Abaqus input file.
 
 fid = open(input_geometry,'r')
 set = []
 elems = []
 line = fid.readline()
 while True:
  if line[0:9] == '*ELEMENT,':
   x, unit_name = line.split('ELSET=')
   print('Element set %s read from file' % unit_name[0:-1])
   set.append(unit_name[0:-1])
   elemlist, line = elementread(fid)
   elems.append(elemlist)
   continue
  elif line[0:5] == '*****':
   break
  line = fid.readline()
 fid.close()
 
 return [elems,set]
 
#####################################################################################
def input_elsets(input_geometry):
 # Read Element Set Definitions from the Abaqus input file.
 
 fid = open(input_geometry,'r')
 set = []
 line = fid.readline()
 while True:
  if line[0:9] == '*ELEMENT,':
   x, unit_name = line.split('ELSET=')
   set.append(unit_name[0:-1])
   elemlist, line = elementread(fid)
   continue
  elif line[0:5] == '*****':
   break
  line = fid.readline()
 fid.close()
 
 return set
 
#####################################################################################
def set_elems(input_geometry):
 # Read elements from APPLE PY output file
 fid = open(input_geometry,'r')
 elems = []
 set = []
 line = fid.readline()
 while True:
  if line[0:5] == '*****':
   break
  elif line[0:6] == '*ELSET':
   x, unit_name = line.split('ELSET=')
   print('Element set %s read from file' % unit_name[0:-1])
   set.append(unit_name[0:-1])
   elements, line = elsetread(fid)
   elems.append(elements)
  else:
   line = fid.readline()
 fid.close()
 
 return [elems,set]
 
#####################################################################################
def set_elsets(input_geometry):
 # Read element sets from APPLE PY output file
 fid = open(input_geometry,'r')
 set = []
 line = fid.readline()
 while True:
  if line[0:5] == '*****':
   break
  elif line[0:6] == '*ELSET':
   x, unit_name = line.split('ELSET=')
   print('Element set %s read from file' % unit_name[0:-1])
   set.append(unit_name[0:-1])
   elemlist, line = elementread(fid)
   continue
  else:
   line = fid.readline()
 fid.close()
 
 return set
 
#####################################################################################
def elementread(fid):
 # Function reads the element numbers from Abaqus input file definition. Ends as soon as a new element set starts.
 elems = []
 num = 0
 while True:
  line = fid.readline()
  if line[0] == '*':
   break
  linenew = str.replace(line,',',' ')
  linenew = str.split(linenew)
  elems.append(linenew[0])
  while line[-3] == ',':
   line = fid.readline()
 return elems, line
 
#####################################################################################
def elsetread(fid):
 # Function reads element numbers from an element set (as e.g. defined by apple.py). As soon as a new set starts the function ends.
 elems = []
 num = 0
 line = fid.readline()
 while True:
  if line[0] == '*':
   break
  linenew = str.replace(line,',',' ')
  linenew = str.split(linenew)
  [elems.append(num) for _,num in enumerate(linenew)]
  line = fid.readline()
 return elems, line
 
#####################################################################################
if __name__ == '__main__':
 main(input_geometry,strata,distrib,output_name,solver)
#####################################################################################
