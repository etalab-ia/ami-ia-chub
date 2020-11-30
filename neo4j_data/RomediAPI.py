# -*- coding: utf-8 -*-
"""
Spyder Editor

"""

import requests
import json


class RomediAPI:
    """
    An API to detect drug with an endpoint
    
    Attributes:
        url_detection (str): The url of the GetJSONdrugsDetected method
    """
    def __init__(self, url_detection, url_detection_by_type):
        """
        Constructor
        
        Parameters:
            url_detection (str): The url of the GetJSONdrugsDetected method
            url_detection_by_type (str): The url of the GetJSONdrugsDetectedByType method
        """
        self.url_detection = url_detection
        self.url_detection_by_type = url_detection_by_type
    
    def detect_drug(self, content):
        """
        
        Parameters:
            content (str): the label of a drug / a sentence 
        
        Returns:
            A Romedi instance detected with offset positions
        """
        r = requests.post(url=self.url_detection, data=content)
        content = r.content.decode()
        if (r.status_code != 200):
           print(content)
           raise ValueError(""""detect_drug method returned an error: {content} with status code is {status_code}""".format(content=content,
                                                                                                                            status_code=r.status_code))
        json_result = json.loads(content)
        return(json_result)

    
    def detect_drug_by_type(self,content, romedi_type):
        """
        
        Parameters:
            content: free text or the name of drug
            romedi_type: the romedi type of the drug (BN, IN, PIN, INdosage, Dosage ...)
        Returns:
            A tuple (IRI, ) IRI detected
        """
        query_params = {"drugname":content,"romeditype":romedi_type}
        r = requests.get(url=self.url_detection_by_type, params=query_params)
        content = r.content.decode()
        if (r.status_code != 200):
           print(content)
           raise ValueError("""detect_drug_by_type method returned an error: {content} with status code is {status_code}""".format(content=content,
                                                                                                                                   status_code=r.status_code))
        json_result = json.loads(content)
        return json_result