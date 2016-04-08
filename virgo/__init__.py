from virgo.vjenkins import JenkinsBuilder
from virgo.httpclient import BundleDownloader
from virgo.httpclient import BUNDLE_TYPES
from virgo.deploy import BundleDeployer
from virgo.email import EmailClient
from multiprocessing import Process
import logging, os, sys, time

log = logging.getLogger("virgo-deploy")


def _process_bundles_file(file_name):
    '''
    parse the string for bundle group, name , version and bundle type
    escape if the line is empty or starts with a #
    :param file_name:
    :return:
    '''
    bundles = list()
    with open(file_name, 'r') as fd:
        for line in fd.readlines():
            line = line.strip()
            if not len(line) or line.startswith('#'):
                continue
            bundle = line.split(',')
            if len(bundle) < 4:
                raise  Exception('bundle format error!!!')
            bundles.append(bundle)

    return bundles

def _process_pillar_bundles(bundles_list):
    '''
    parse the bundle config in pillar data

    :param bundles_list:
    :return:
    '''
    bundles = list()

    for line in bundles_list:
        line = line.strip()
        if not len(line) or line.startswith('#'):
            continue
        bundle = line.split(',')
        if len(bundle) < 4:
            raise  Exception('bundle format error!!!')
        bundles.append(bundle)

    return bundles

def ltjob(log_file,app_success_log,timeout, server, port, username, passwd, to):
    '''
    This is a long time job, will take hours to finish,
    so fork in a seperate process, other than the main process,
    and notify the client by email instead

    :return:
    '''

    error = False

    with open(log_file,'r') as vlog:
        time_out_count = timeout/10
        while True:
            logs = vlog.readline()

            #if logs.find("Started plan 'org.eclipse.virgo.apps.admin.plan' version '3.0.0'") != -1:
            if logs.find(app_success_log) != -1:
                log.info('virgo started applications successfully!!!')
                break

            time.sleep(30)
            time_out_count = time_out_count-1
            if(time_out_count==0):
                log.error('virgo failed to start your applications within' + str(timeout) + ' sec')
                error = True
                break

    email = EmailClient(server,port,username,passwd)

    if error:
        email.sendNotif(to,'virgo failed to start your applications within' + str(timeout) + ' sec' )
    else:
        email.sendNotif(to,'virgo started successfully!!!')


def deploy(proj_names):
    #__opts__ = salt.config.minion_config('/etc/salt/minion')
    #__grains__ = salt.loader.grains(__opts__)


    log.info('pillar items = '+str(__pillar__))

    #get pillar data
    JENKINS_URL = __pillar__['bind']['JENKINS_URL']
    JENKINS_USER = __pillar__['bind']['JENKINS_USER']
    JENKINS_PASSWORD = __pillar__['bind']['JENKINS_PASSWORD']
    JENKINS_NOTIF_MQ_URL = __pillar__['bind']['JENKINS_NOTIF_MQ_URL']
    JENKINS_NOTIF_MQ_QUEUE = __pillar__['bind']['JENKINS_NOTIF_MQ_QUEUE']
    VIRGO_HOME = __pillar__['bind']['VIRGO_HOME']
    VIRGO_LOCAL_REPOSITORY = __pillar__['bind']['VIRGO_LOCAL_REPOSITORY']
    MAVEN_REPOSITORY_URL = __pillar__['bind']['MAVEN_REPOSITORY_URL']
    MAVEN_USER = __pillar__['bind']['MAVEN_USER']
    MAVEN_PASSWORD = __pillar__['bind']['MAVEN_PASSWORD']
    APP_TIME_OUT = __pillar__['bind']['APP_TIME_OUT']
    APP_SUCCESS_LOG = __pillar__['bind']['APP_SUCCESS_LOG']
    EMAIL_SERVER = __pillar__['bind']['EMAIL_SERVER']
    EMAIL_PORT = __pillar__['bind']['EMAIL_PORT']
    EMAIL_USERNAME = __pillar__['bind']['EMAIL_USERNAME']
    EMAIL_PASSWD = __pillar__['bind']['EMAIL_PASSWD']
    EMAIL_TO = __pillar__['bind']['EMAIL_TO']

    BUNDLE_LIST = __pillar__['bundles']['BUNDLE_LIST']


    LOCAL_TEMP_PATH = VIRGO_HOME + os.path.sep + 'work' + os.path.sep + 'tmp'

    log_path = VIRGO_HOME + os.path.sep + 'serviceability'

    if not os.path.exists(log_path):
        os.mkdir(log_path)

    '''
    sorry we cannot wait to config the logging, we want to use immediately

    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%d %b %Y %H:%M:%S',
                    filename= log_path + os.path.sep + 'virgo-deploy.log',
                    filemode='w')
    '''



    log.info('JENKINS_URL = ' +  JENKINS_URL)
    log.info('JENKINS_USER = ' +  JENKINS_USER)
    log.info('JENKINS_NOTIF_MQ_URL = ' +  JENKINS_NOTIF_MQ_URL)
    log.info('JENKINS_NOTIF_MQ_QUEUE = ' +  JENKINS_NOTIF_MQ_QUEUE)
    log.info('VIRGO_HOME = ' +  VIRGO_HOME)
    log.info('VIRGO_LOCAL_REPOSITORY = ' +  VIRGO_LOCAL_REPOSITORY)
    log.info('MAVEN_REPOSITORY_URL = ' +  MAVEN_REPOSITORY_URL)
    log.info('MAVEN_USER = ' +  MAVEN_USER)
    log.info('APP_TIME_OUT = ' +  str(APP_TIME_OUT))
    log.info('APP_SUCCESS_LOG = ' +  APP_SUCCESS_LOG)

    # if the proj_names is a file
    if proj_names == 'bundles':
        #an absolute path file name
        bundles = _process_pillar_bundles(BUNDLE_LIST)
    else:
        bundles =  list()
        if proj_names.find(';') != -1:
            bnds = proj_names.split(';')
            for s in bnds:
                b = s.split(',')
                if len(b) < 4:
                    raise  Exception('bundle format error!!!')
                bundles.append(b)
        else:
            b = proj_names.split(',')
            if len(b) < 4:
                raise  Exception('bundle format error!!!')
            bundles.append(b)

    #builder = JenkinsBuilder(JENKINS_URL, JENKINS_USER,JENKINS_PASSWORD, \
        #                         JENKINS_NOTIF_MQ_URL,JENKINS_NOTIF_MQ_QUEUE)
    downloader = BundleDownloader(MAVEN_REPOSITORY_URL, MAVEN_USER, MAVEN_PASSWORD, LOCAL_TEMP_PATH)
    deploy = BundleDeployer(__salt__,VIRGO_HOME, VIRGO_LOCAL_REPOSITORY,APP_TIME_OUT, APP_SUCCESS_LOG)

    try:
        # shutdown first
        deploy.shutdownVirgo(VIRGO_HOME)

        for bnd in bundles:

            #builder.build_project(proj_name)
            bnd_group = bnd[0]
            bnd_name = bnd[1]
            bnd_version = bnd[2]
            bnd_type = bnd[3]

            tmpBunlde = downloader.download(bnd_group, bnd_name, bnd_version, BUNDLE_TYPES[bnd_type])
            deploy.deploy(tmpBunlde)

        deploy.restartVirgo()

        log_file = VIRGO_HOME+os.path.sep +'serviceability' + os.path.sep + 'logs'+ os.path.sep + 'log.log'

        '''
        some deployments may cost hours to finish,
        we can not keep the salt command line client to wait for hours to terminate.
        so we fork a seperate process to check if the virgo starts correctly.
        and send a email to notify the final deployment result.
        '''
        p = Process(target=ltjob, args=(log_file, APP_SUCCESS_LOG, APP_TIME_OUT, EMAIL_SERVER, \
                                        EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWD, EMAIL_TO))
        p.start()
        log.info('Child process '+str(p.pid) +' started, will notify job results bu email.')
        # we don't wait for the child process to terminate
        #p.join()

    except Exception,e:
        log.error('Error deploying ' + proj_names )
        log.error(str(sys.exc_info()[0]) + ' - ' + str(sys.exc_info()[1]))
        log.error(str(sys.exc_info()))
        return False

    return True
