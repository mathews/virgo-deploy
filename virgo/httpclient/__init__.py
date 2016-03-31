## -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 00:32:38 2016

@author: mathews
"""

import requests,os
from requests.auth import HTTPBasicAuth
from StringIO import StringIO
import logging

log = logging.getLogger("httpclient")

BUNDLE_TYPES = {'war':'.war','jar':'.jar','par':'.par'}


class BundleDownloader:
    '''
    download bundles from mvn repository into temporary path
    '''

    def __init__(self, repository_url, user = None, password = None,  temp_path = '/tmp'):
        '''

        :param repository_url:
        :param temp_path:
        :return:
        '''
        self._repository_url = repository_url
        self._user = user
        self._password = password
        self._temp_path = temp_path

        if not os.path.exists(self._temp_path):
            try:
                os.mkdir(self._temp_path)
            except Exception, e:
                self._temp_path = None
                print e



    def download(self,bundle_group,bundle_name,bundle_version,bundle_type):
        '''

        :param bundle_name:
        :return:
        '''

        fileName =  bundle_name + '-' + bundle_version + bundle_type
        url = self._repository_url + '/' + bundle_group.replace('.','/') \
              + '/' + bundle_name+ '/' + bundle_version + '/' + fileName

        log.info('Retrieving bundle from ' + url)

        tmpFile = self._temp_path + os.path.sep + fileName

        try:
            if self._user != None and self._password != None :
                r = requests.get(url, stream=True,auth=HTTPBasicAuth(self._user, self._password))
            else:
                r = requests.get(url, stream=True)

            log.info('response - ' + str(r))

            #cont =  StringIO(r.content)

            if self._temp_path != None:
                if os.path.exists(tmpFile):
                    os.remove(tmpFile)

                with open(tmpFile, 'wb') as fd:
                    for chunk in r.iter_content(64):
                        fd.write(chunk)
                log.info('temp file ' + tmpFile +' is ready !!!')
            else:
                tmpFile = None
        except Exception, e:
            log.error('Error retreive bundles from maven repository!!!')
            raise e

        return tmpFile


