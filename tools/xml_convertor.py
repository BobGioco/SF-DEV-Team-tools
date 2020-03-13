import xml.etree.ElementTree as et
import json
import numpy as np
import pandas as pd
from pandas.io.json import json_normalize


from xml.etree import cElementTree as ElementTree

class _XmlListConfig(list):
    def __init__(self, aList):
        for element in aList:
            if element:
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(_XmlDictConfig(element))
                elif element[0].tag == element[1].tag:
                    self.append(_XmlListConfig(element))
            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)


class _XmlDictConfig(dict):
    '''
    Example usage:

    >>> tree = ElementTree.parse('your_file.xml')
    >>> root = tree.getroot()
    >>> xmldict = XmlDictConfig(root)

    Or, if you want to use an XML string:

    >>> root = ElementTree.XML(xml_string)
    >>> xmldict = XmlDictConfig(root)

    And then use xmldict for what it is... a dict.
    '''
    def __init__(self, parent_element):
        if parent_element.items():
            self.update(dict(parent_element.items()))
        for element in parent_element:
            if element:
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = _XmlDictConfig(element)
                else:
                    aDict = {element[0].tag: _XmlListConfig(element)}
                if element.items():
                    aDict.update(dict(element.items()))
                self.update({element.tag: aDict})
            elif element.items():
                self.update({element.tag: dict(element.items())})
            else:
                self.update({element.tag: element.text})


class XML_parser():
    """
    Example usage:
    data=XML_parser('dataset.xml')

    get_DateFrame returns converted dataset as Pandas DataFrame
    >>> data.get_DateFrame()

    get_dict returns converted dataset as dictionary
    >>> data.get_dict()


    get_fields() returns a set of field/column names
    >>> data.get_fields()
    {'_Citation_InvestigatorList_Initials',
     '_Citation_ChemicalList_12_NameOfSubstance',
     '_Citation_Investigator_Name',
     '_Citation_Article_Author_Name',
     '_Citation_Investigator__Affiliation',
     '_Citation_Article_Author_ValidYN',
     '_Citation_Article_Author_Affiliation',
     '_Citation_Article_Author_Name'}

    get_null_values_in_column returns Pandas DataFrame with count of null values for every field/column in dataset
    >>> data.get_null_values_in_column()

    version: 0.1
    author: JS
    """
    def __init__(self,filename):
        self.root = et.parse(filename).getroot()
        self.data = json.loads(json.dumps(_XmlListConfig(self.root)))
        self.keys_set=set()
        self.row={}
        self._data_keys()
        self.target_dct=self._dict_setup(self.keys_set)

        self._data_values()

    def _dict_setup(self,keys):
        target_dct={}
        for key in keys:
            target_dct[key]=[]
        return target_dct

    def _template(self,keys):
        template={}
        for key in keys:
            template[key]=None
        return template

    def _data_keys(self):
        for i in self.data:
            self._get_keys(i)

    def _data_values(self):
        for i in self.data:
            self.row=self._template(self.keys_set)
            self._get_values(i)
            for key in self.target_dct.keys():
                self.target_dct[key].append(self.row[key])
            self.row={}

    def _get_keys(self,dct,master=''):
        if isinstance(dct,dict):
            for key,value in dct.items():
                if isinstance(value,dict) or isinstance(value,list):
                    self._get_keys(value,f"{master}_{key}")
                else:
                    self.keys_set.add(f"{master}_{key}")
        elif isinstance(dct,list):
            for count,i in enumerate(dct):
                if isinstance(i,dict) or isinstance(i,list):
                    self._get_keys(i,f"{master}_{count}")
                else:
                    self.keys_set.add(f"{master}_{count}")

    def _get_values(self,dct,master=''):
        if isinstance(dct,dict):
            for key,value in dct.items():
                if isinstance(value,dict) or isinstance(value,list):
                    self._get_values(value,f"{master}_{key}")
                else:
                    self.row[f"{master}_{key}"]=value
        elif isinstance(dct,list):
            for count,i in enumerate(dct):
                if isinstance(i,dict) or isinstance(i,list):
                    self._get_values(i,f"{master}_{count}")
                else:
                    self.row[f"{master}_{count}"]=i

    def get_DateFrame(self):
        return pd.DataFrame(self.target_dct)

    def get_fields(self):
        return self.keys_set

    def get_dict(self):
        return self.target_dct

    def get_null_values_in_column(self):
        df=pd.DataFrame(self.target_dct)
        an_dct={'column_name':[],'none_values':[]}
        for count,column in enumerate(df.columns):
            an_dct['column_name'].append(column)
            an_dct['none_values'].append(len(df[df[column].isnull()][column]))
        return pd.DataFrame(an_dct)
