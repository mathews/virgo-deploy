## -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 00:32:38 2016

@author: mathews
"""

import os,shutil,logging,platform,subprocess,time,psutil,commands

log = logging.getLogger("deploy")

class BundleDeployer:
    def __init__(self,virgo_home,localRepo,timeout,app_success_log):
        '''

        :param virgo_home:
        :param localRepo:
        :return:
        '''
        self._virgo_home = virgo_home
        self._localRepo = localRepo
        self._timeout = timeout
        self._app_success_log = app_success_log
        self.shutteddown = False

        abs_virgo_repo = virgo_home + os.path.sep +localRepo

        if not os.path.exists(abs_virgo_repo):
            try:
                os.mkdir(abs_virgo_repo)
            except Exception, e:
                self._localRepo = None
                log.error('error creating local repository path in virgo!', e)

        self._abbr_home = self.getAbbreviatedPath(virgo_home)




    def _isInPickup(self,fileName):
        '''

        :param fileName:
        :return:
        '''

        return os.path.exists(self._virgo_home + os.path.sep +'pickup' +  os.path.sep + fileName )


    def getAbbreviatedPath(self,path):
        '''
        windows will abbreviate the path name,
        and use the abbreviated path name for process properties
        we here rely on windows command to get the abbreviated path name
        :param path:
        :return:
        '''

        abbr_path = path

        sys = os.name


        if sys == 'nt':
            n = path.rfind(os.path.sep)
            parent  = path[0:n]
            current = path[n+1:]

            p =  subprocess.Popen('dir /x',stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True,cwd=parent)
            out = p.communicate()
            out1 = out[0].splitlines()

            for x in out1:
                if x.find(current) != -1 and x.find('<DIR>') != -1:
                    path_attr = x.split(' ')
                    #if path_attr[17] == current:
                    abbr_path =  parent +os.path.sep +path_attr[16]
                    log.info(' got windows abbrevited path as ' +  abbr_path)

        log.info(' got abbrevited path as ' +  abbr_path)

        return abbr_path



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
        log.debug('going to shutdown Virgo ...... ')

        ps = psutil.pids()

        #log.debug('got processes - ' + str(ps))

        for p in ps:
            try:
                proc = psutil.Process(p)

                if proc.cwd() == self._abbr_home:

                    log.info('found process with cwd as virgo_home, cwd = '+ proc.cwd())

                    #if the virgo process was started within five minutes
                    if time.time()-proc.create_time() < 300:
                        error_msg = 'virgo process - ' + str(p) + ' was started within five minutes!!!'
                        log.error(error_msg)
                        raise Exception(error_msg)
                    else:
                        proc.terminate()
                        log.warning('virgo process - ' + str(p) + ' is terminated!!!')
                        #break
            except psutil.AccessDenied:
                pass
            except Exception ,e:
                log.error('Error shutting down virgo!!!')
                raise e
        # mark shutted down
        self.shutteddown = True

    def cleanDir(self, Dir ):
        '''
        some java program will write very deep file directories,
        just as the temp file of tomcat or OSGI container.
        this will cause the python stack overflow
        Please notice these circumstances

        :param Dir:
        :return:
        '''
        if os.path.isdir( Dir ):
            paths = os.listdir( Dir )
            for path in paths:
                filePath = os.path.join( Dir, path )
                if os.path.isfile( filePath ):
                    try:
                        os.remove( filePath )
                    except os.error:
                        log.error( "remove %s error." %filePath )
                elif os.path.isdir( filePath ):
                    if filePath[-4:].lower() == ".svn".lower():
                        continue
                    shutil.rmtree(filePath,True)
        return True

    def clearPath(self,path):
        '''
        reply on the os commands to delete the whole file tree
        :param path:
        :return:
        '''
        if os.name == 'nt':
            del_cmd = 'rd/s/q '
        else:
            del_cmd = 'rm -Rf '

        os.system(del_cmd + path)




    def restartVirgo(self):
        '''
        kill the old process, as the shutdown.sh doesn't work oftern.
        start the virgo with the startup.sh script
        :return:
        '''
        log.info('about to restart virgo ...... ')

        if platform.system()=='Linux':
            suffix = '.sh'
        else:
            suffix = '.bat'

        log.debug('prefix and suffix are ready!!! ')

        # try to shutdown  virgo first
        commd_prefix = os.path.join(self._virgo_home, 'bin')

        log.debug('commd_prefix = '+commd_prefix)

        #shutdown = prefix + commd_prefix+ 'shutdown'+ suffix
        #shut_proc = subprocess.Popen(shutdown, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True,cwd=commd_prefix)
        #shut_proc.wait()

        if not self.shutteddown:
            log.info('virgo is going to be shutted down!!!')

            self.shutdownVirgo(self._virgo_home)

            log.info('virgo shutted down successfully ...... ')


        self.clearPath(os.path.join( self._virgo_home, 'serviceability','logs'))
        self.clearPath(os.path.join( self._virgo_home, 'serviceability','eventlogs'))
        self.clearPath(os.path.join( self._virgo_home, 'work'))


        start_cmd = os.path.join( commd_prefix, 'startup'+ suffix)

        log.info('start_cmd = ' + start_cmd)

        log.info('virgo starting ...... ')

        DETACHED_PROCESS = 8
        p =  subprocess.Popen(start_cmd,shell=True,cwd=commd_prefix,creationflags=DETACHED_PROCESS, close_fds=True)
        #p =  subprocess.Popen(start_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True,cwd=commd_prefix)
        #Note here, the virgo process will never end, you should not wait for it to terminate
        #p.communicate()
        #p.wait()
        log.info('virgo process is started as pid - '+ str(p.pid))


        log.info('virgo is starting, about to check the log file!')

        log_file = self._virgo_home+os.path.sep +'serviceability' + os.path.sep + 'logs'+ os.path.sep + 'log.log'

        time_out_count = 4

        while not os.path.exists(log_file):
            time.sleep(10)
            time_out_count = time_out_count-1
            if(time_out_count==0):
                log.error('virgo logging failed to start within 60 sec')
                #break
                raise Exception('virgo logging failed to start within 60 sec')

        # virgo needs a long time to start up, this will cause the salt-minion fail to return
        '''
        if time_out_count!=0 :
            with open(log_file,'r') as vlog:
                time_out_count = self._timeout/10
                while True:
                    logs = vlog.readline()

                    #if logs.find("Started plan 'org.eclipse.virgo.apps.admin.plan' version '3.0.0'") != -1:
                    if logs.find(self._app_success_log) != -1:
                        log.info('virgo started applications successfully!!!')
                        break

                    time.sleep(10)
                    time_out_count = time_out_count-1
                    if(time_out_count==0):
                        log.error('virgo failed to start your applications within' + str(self._timeout) + ' sec')
                        break
        '''
