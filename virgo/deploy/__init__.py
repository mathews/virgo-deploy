## -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 00:32:38 2016

@author: mathews
"""

import os,shutil,logging,platform,subprocess,time,psutil

log = logging.getLogger("deploy")

class BundleDeployer:
    def __init__(self,virgo_home,localRepo):
        '''

        :param virgo_home:
        :param localRepo:
        :return:
        '''
        self._virgo_home = virgo_home
        self._localRepo = localRepo

        abs_virgo_repo = virgo_home + os.path.sep +localRepo

        if not os.path.exists(abs_virgo_repo):
            try:
                os.mkdir(abs_virgo_repo)
            except Exception, e:
                self._localRepo = None
                log.error('error creating local repository path in virgo!', e)


    def _isInPickup(self,fileName):
        '''

        :param fileName:
        :return:
        '''

        return os.path.exists(self._virgo_home + os.path.sep +'pickup' +  os.path.sep + fileName )


    def deploy(self,fileName):
        '''
        copy bundles into pickup if the old one is there,
        else copy into local maven repository path
        :param fileName:
        :return:
        '''
        p,f = os.path.split(fileName)

        try:

            if self._isInPickup(f):
                #copy file to pickup
                shutil.copy(fileName,  self._virgo_home + os.path.sep +'pickup' +  os.path.sep + f )
                log.info('copied into virgo pickup!!!')
            else:
                #copy file to repository
                shutil.copy(fileName,  self._virgo_home + os.path.sep + self._localRepo +  os.path.sep + f)
                log.info('copied into virgo local repository!!!')

            log.info('finished copying file ' + fileName + ' into virgo!')
        except Exception, e:
            log.error('error copy file ' + fileName + ' into virgo',e)
            raise e

    def shutdownVirgo(self,virgo_home):
        '''

        :return:
        '''
        ps = psutil.pids()

        for p in ps:
            try:
                proc = psutil.Process(p)
                if proc.cwd() == virgo_home:
                    #if the virgo process was started within five minutes
                    if time.time()-proc.create_time() < 300:
                        error_msg = 'virgo process - ' + str(p) + ' was started within five minutes!!!'
                        log.error(error_msg)
                        raise Exception(error_msg)
                    else:
                        proc.terminate()
                        log.warning('virgo process - ' + str(p) + ' is terminated!!!')
                        break
            except psutil.AccessDenied:
                pass
            except Exception ,e:
                log.error('Error shutting down virgo!!!')
                raise e

    def clearPath(self,path):

        if os.path.exists(path):
            files_in_path = os.listdir(path)

            for t in files_in_path:
                filepath = os.path.join( path, t )
                if os.path.isfile(filepath):
                    os.remove(filepath)
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath,True)


    def restartVirgo(self):
        '''
        kill the old process, as the shutdown.sh doesn't work oftern.
        start the virgo with the startup.sh script
        :return:
        '''

        if platform.system()=='Linux':
            prefix = ''
            suffix = '.sh &'
        else:
            prefix = 'start /b '
            suffix = '.bat'

        # try to shutdown  virgo first
        commd_prefix = self._virgo_home+os.path.sep +'bin' + os.path.sep

        shutdown = prefix + commd_prefix+ 'shutdown'+ suffix

        #shut_proc = subprocess.Popen(shutdown, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True,cwd=commd_prefix)
        #shut_proc.wait()
        #log.info('virgo shutted down successfully!!!')

        self.shutdownVirgo(self._virgo_home)


        self.clearPath(os.path.join( self._virgo_home, 'serviceability' + os.path.sep + 'logs'))
        self.clearPath(os.path.join( self._virgo_home, 'serviceability' + os.path.sep + 'eventlogs'))
        self.clearPath(os.path.join( self._virgo_home, 'work'))


        start_cmd = prefix +  commd_prefix+ 'startup'+ suffix

        log.info('start_cmd = ' + start_cmd)

        log.info('virgo starting ...... ')

        p =  subprocess.Popen(start_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True,cwd=commd_prefix)
        p.wait()

        log_file = self._virgo_home+os.path.sep +'serviceability' + os.path.sep + 'logs'+ os.path.sep + 'log.log'

        time_out = 4

        while not os.path.exists(log_file):
            time.sleep(10)
            time_out = time_out-1
            if(time_out==0):
                log.error('virgo logging failed to start within 40 sec')
                break


        if time_out!=0 :
            with open(log_file,'r') as vlog:
                while True:
                    logs = vlog.readline()

                    if logs.find("Started plan 'org.eclipse.virgo.apps.admin.plan' version '3.0.0'") != -1:
                        log.info('virgo started successfully!!!')
                        break
