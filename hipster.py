#####################################################################################
# HIPSTER - Homogeneous to Inhomogeneous rock Properties for Stress TEnsor Research	#
# Version 1.01																		#
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
input_geometry = 'solver_deck.geom' # 'elements.set'
distrib = 'uniform'
strata = ['Top','Middle','Bottom']
output_name = 'test'

Top = rock('Top',25E9,0,0.25,0.1,2500,0)
Middle = rock('Middle',35E9,2.5E9,0.21,0.02,2625,250)
Bottom = rock('Bottom',45E9,0,0.24,0,2850,0)

#####################################################################################
def main(input_geometry,strata,distrib,output_name):
	## Reading geometry
	# Loads the units regardless whether they are defined in sets (APPLE PY) or in ELSETS (original solver deck)
	# and read the element numbers
	print 'Running HIPSTER v1.0'
	if input_geometry[-3:] == 'inp' or input_geometry[-4:] == 'geom':
		# Read Element Definitions from the Abaqus input file.
		print 'Reading element definitions from Abaqus *.inp or *.geom file'
		fid = open(input_geometry,'r')
		set = []
		elems = []
		line = fid.readline()
		while True:
			if line[0:9] == '*ELEMENT,':
				x, unit_name = line.split('ELSET=')
				print 'Element set %s read from file' % unit_name[0:-2]
				set.append(unit_name[0:-2])
				elemlist, line = elementread(fid)
				elems.append(elemlist)
				continue
			elif line[0:5] == '*****':
				break
			line = fid.readline()
		fid.close()
		
		
	elif input_geometry[-3:] == 'set':
		# Read Element sets defined by APPLE PY.
		print 'Reading element definitions from APPLE PY elements *.set file'
		fid = open(input_geometry,'r')
		elems = []
		set = []
		line = fid.readline()
		while True:
			if line[0:5] == '*****':
				break
			elif line[0:6] == '*ELSET':
				x, unit_name = line.split('ELSET=')
				print 'Element set %s read from file' % unit_name[0:-1]
				set.append(unit_name[0:-1])
				elements, line = elsetread(fid)
				elems.append(elements)
			else:
				line = fid.readline()
		fid.close()
		
	else:
		print 'ERROR! Specify a valid input type.'
	
	## Assign material properties to elements
	print 'Start assignment of material properties'

	# Create Material distribution and material files for both lithostatic and calibrated model runs.
	matininame = output_name + '_lithostatic.mat'
	mat_ini = open(matininame,'w')
	mat_ini.write('** Inhomogeneous material properties for lithostatic stress state\n** Created by HIPSTER v1.0 - http://github.com/MorZieg/hipster\n** %s\n**\n** Material definitions\n' % str(np.datetime64('now')))
	
	matfinname = output_name + '.mat'
	mat_fin = open(matfinname,'w')
	mat_fin.write('** Inhomogeneous material properties\n** Created by HIPSTER v1.0 - http://github.com/MorZieg/hipster\n** %s\n**\n** Material definitions\n' % str(np.datetime64('now')))
	
	# Draw values from distribution and write material definition
	for x,n in enumerate(strata):
		mat_fin.write('**\n** %s\n**\n' % set[x])
		mat_ini.write('**\n** %s\n**\n' % set[x])
		
		E = eval(n + '.E')
		E_sig = eval(n + '.E_sig')
		nu = eval(n + '.nu')
		nu_sig = eval(n + '.nu_sig')
		rho = eval(n + '.rho')
		rho_sig = eval(n + '.rho_sig')

		if E_sig == 0 and nu_sig == 0 and rho_sig == 0:
			mat_ini.write('*MATERIAL, NAME=rock_%s\n*ELASTIC, TYPE = ISOTROPIC\n%.6g, 0.49, 0.0\n*DENSITY\n%.0f\n**\n' % (set[x], E, rho))
			mat_fin.write('*MATERIAL, NAME=rock_%s\n*ELASTIC, TYPE = ISOTROPIC\n%.8g, %.3f, 0.0\n*DENSITY\n%.0f\n**\n' % (set[x], E, nu, rho))
		else:
			for i,el in enumerate(elems[x]):
				if distrib == 'normal':
					E_elem,nu_elem,rho_elem = normal_distrib(E,E_sig,nu,nu_sig,rho,rho_sig)
				elif distrib =='uniform':
					E_elem,nu_elem,rho_elem = uniform_distrib(E,E_sig,nu,nu_sig,rho,rho_sig)
				mat_ini.write('*MATERIAL, NAME=rock_%s_%s\n*ELASTIC, TYPE = ISOTROPIC\n%.6g, 0.49, 0.0\n*DENSITY\n%.0f\n**\n' % (set[x], el, E_elem, rho_elem))
				mat_fin.write('*MATERIAL, NAME=rock_%s_%s\n*ELASTIC, TYPE = ISOTROPIC\n%.8g, %.3f, 0.0\n*DENSITY\n%.0f\n**\n' % (set[x], el, E_elem, nu_elem, rho_elem))
	
	
	# Create an element set per element
	mat_fin.write('**\n**\n** Element sets\n')
	mat_ini.write('**\n**\n** Element sets\n')
	for x,n in enumerate(strata):
		if eval(n + '.E_sig') != 0 or eval(n + '.nu_sig') != 0 or eval(n + '.rho_sig') != 0:
			mat_fin.write('**\n** %s\n**\n' % set[x])
			mat_ini.write('**\n** %s\n**\n' % set[x])
			for _,el in enumerate(elems[x]):
				mat_ini.write('*ELSET, ELSET=%s_%s\n%s\n' % (set[x], el, el))
				mat_fin.write('*ELSET, ELSET=%s_%s\n%s\n' % (set[x], el, el))
	
	
	# Write solid section.
	mat_fin.write('**\n**\n** Solidsections\n')
	mat_ini.write('**\n**\n** Solidsections\n')
	for x,n in enumerate(strata):
		if eval(n + '.E_sig') == 0 and eval(n + '.nu_sig') == 0 and eval(n + '.rho_sig') == 0:
			mat_fin.write('**\n** %s\n' % set[x])
			mat_ini.write('**\n** %s\n' % set[x])
			mat_ini.write('*SOLIDSECTION,ELSET=%s, MATERIAL=rock_%s\n' % (set[x],set[x]))
			mat_fin.write('*SOLIDSECTION,ELSET=%s, MATERIAL=rock_%s\n' % (set[x],set[x]))
		else:
			mat_fin.write('**\n** %s\n' % set[x])
			mat_ini.write('**\n** %s\n' % set[x])
			for i,el in enumerate(elems[x]):
				mat_ini.write('*SOLIDSECTION,ELSET=%s_%s, MATERIAL=rock_%s_%s\n' % (set[x],el,set[x],el))
				mat_fin.write('*SOLIDSECTION,ELSET=%s_%s, MATERIAL=rock_%s_%s\n' % (set[x],el,set[x],el))

	
	mat_fin.close()
	mat_ini.close()
	
	print 'Material properties successfully assigned!'

#####################################################################################
def normal_distrib(E,E_sig,nu,nu_sig,rho,rho_sig):
	# Draw material properties from a normal distribution specified by the user.
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
	main(input_geometry,strata,distrib,output_name)
#####################################################################################
