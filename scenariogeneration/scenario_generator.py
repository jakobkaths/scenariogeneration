import itertools
import os
import numpy as np
import shutil
import sys


class ScenarioGenerator():
    """ ScenarioTemplate is a class that should be inherited by a Scenario class in order to generate xodr and xosc files based on pyoscx and pyodrx

        Two main uses, in your generation class define self.parameters as either as
         - a dict of lists, where the lists are the values you want to sweep over, all permutations of these sets will be generated
         - a list of dicts, where the dicts are identical and each element in the list is one scenario

        Attributes
        ----------
            road_file (str): name of the roadfile,

            parameters (dict of lists, or list of dicts): parameter sets to be used

            naming (str): two options
    """
    def __init__(self):
        self.road_file = ''
        self.parameters = {}
        self.naming = 'numerical' # can be 'numerical', 'parameter'
        self._it = 0
        self._generation_folder = ''
        self._write_relative_road_path = False
    def road(self,**kwargs):
        """ Dummy method for generating an OpenDRIVE road

            Should be overwritten by the user, and return a pyodrx.OpenDrive object

            Return
            ------
                sce (pyodrx.OpenDrive): a road on pyodrx format
        """
        return []

    def scenario(self,**kwargs):
        """ Dummy method for generating a OpenScenario file
            
            Should be overwritten by the user, and return a pyoscx.Scenario object

            Return
            ------
                sce (pyoscx.Scenario): a scenario on pyoscx format
        """
        return []

    def _create_folder_structure(self,generation_folder):
        """ method to create a folder structure (if needed) to generate the scenarios and roads in

            Parameters
            ----------
                generation_folder (str): the path to a folder where the files should be generated

        """
        
        if not os.path.exists(generation_folder):
            os.mkdir(generation_folder)
            os.mkdir(os.path.join(generation_folder,'xosc'))
            os.mkdir(os.path.join(generation_folder,'xodr'))
        self._generation_folder = generation_folder
    def print_permutations(self,override_parameters = None):
        """print_permutations will create a printout to view all permutations created

            Parameters
            ----------               
                override_parameters (list of dicts, or dict of lists): overrides the self.parameters attribute

        """
        if override_parameters:
            self.parameters = override_parameters
        self._handle_input_parameters()
        it = 0
        for p in self.all_permutations:
            print('Permutation: ' + str(it))
            printstr = ''
            for key, value in p.items():
                printstr += key + ': ' + str(value) + ', '
            print(printstr)
            it += 1

    def _handle_input_parameters(self):
        """ _handle_input_parameters takes care of different types of parameters inputs, such as list of dicts or a dict of lists

        """

        if isinstance(self.parameters,dict):
            self._create_permutations()
            print('Generated ' + str(len(self.all_permutations)) + ' scenarios, using all permutations of parameters input...')

        elif isinstance(self.parameters,list):
            print('Using parameters as a list of cases')
            self.all_permutations = self.parameters

  
        
    
    def _generate_road_and_scenario(self,permutation):
        """ _generate_road_and_scenario takes a permutation and generates the road/scenario (if specified)

            Parameters
            ----------
                permutation (dict): the parameter dict of the wanted scenario

            Returns
            -------
                open_scenario_file (str), open_drive_file (str)
        """
        scenario_name = self._get_scenario_name(permutation)
        self.road_file = ''
        scenario_file = ''

        road = self.road(**permutation)
        if road:
            self.road_file = os.path.abspath(os.path.join(self._generation_folder,'xodr',scenario_name+'.xodr'))
            if self.write_relative_road_path:
                self.road_file = self.road_file.replace(os.path.abspath(self._generation_folder),os.path.pardir)
            road.write_xml(self.road_file)

        sce = self.scenario(**permutation)
        if sce:
            scenario_file = os.path.join(self._generation_folder,'xosc',scenario_name+'.xosc')
            sce.write_xml(scenario_file)
        return scenario_file, self.road_file

    def _get_scenario_name(self,permutation):
        """ _get_scenario_name generates the name of the wanted file, based on the permutation

            Returns
            -------
                scenario_name (str)
        """
        name_prefix = ''

        if self.naming == 'numerical':
            name_prefix = str(self._it)
            self._it += 1
        elif self.naming == 'parameter':
            for  key, value in permutation.items():
                name_prefix += '_' + key.replace('\\','-').replace('/','-') + '-' + str(value).replace('\\','-').replace('/','-')
        else:
            raise NameError('Attribute naming, can only be "numerical" or "parameter", not ' + self.naming)

        return os.path.basename(sys.modules[self.__class__.__module__].__file__).split('.')[0]+name_prefix


    def generate_single(self,generation_folder, order = 'first',override_parameters = None, write_relative_road_path = False):
        """ generate_single will generate only one scenario


        """
        self.write_relative_road_path = write_relative_road_path
        self._create_folder_structure(generation_folder)
        if override_parameters:
            print('Overriding inputs via input')
            self.parameters = override_parameters
        self._handle_input_parameters()

        if isinstance(order,str):
            if order == 'first':
                it = 0
            elif order == 'middle':
                it = int(np.floor(len(self.all_permutations)/2))
            elif order == 'random':
                it = int(np.floor(np.random.rand()*len(self.all_permutations)))
        else:
            it = order

        return self._generate_road_and_scenario(self.all_permutations[it])


    def generate(self,generation_folder,override_parameters = None, write_relative_road_path = False):
        """ generate uses the pyoscx.Scenario defined in the method scenario and the pyodrx.OpenDrive (optional) in the road method
            together with the parameters attribute to generate scenarios and roads for all permutations defined and save those files
            in the generation_folder.
        
            Parameters
            ----------
                generation_folder (str): the path to a folder where the files should be generated
                
                override_parameters (list of dicts, or dict of lists): overrides the self.parameters attribute
        """
        self.write_relative_road_path = write_relative_road_path
        scenario_files = []
        road_files = []
        self._create_folder_structure(generation_folder)
        if override_parameters:
            print('Overriding inputs via input')
            self.parameters = override_parameters
        self._handle_input_parameters()
    
        for p in self.all_permutations:
            
            scenario_file,road_file = self._generate_road_and_scenario(p)
            scenario_files.append(scenario_file)
            road_files.append(road_file)

        return scenario_files, road_files

    def _create_permutations(self):
        """ generates all permutations of the defined parameters.

            Returns
            -------
                scenario_files (list of str): all scenenario files generated
        """
        parameterlist = []
        for key in self.parameters:
            parameterlist.append(self.parameters[key])

        available_permutations = list(itertools.product(*parameterlist))
        self.all_permutations = []
        keys = list(self.parameters.keys())
        for p in available_permutations:
            inputdict = {}
            for i in range(len(self.parameters)):
                inputdict[keys[i]] = p[i]
            self.all_permutations.append(inputdict)