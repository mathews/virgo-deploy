from virgo.vjenkins import JenkinsBuilder
from virgo.httpclient import BundleDownloader
from virgo.httpclient import BUNDLE_TYPES
from virgo.deploy import BundleDeployer

import logging, os, sys

def _process_bundles_file(file_name):
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

def deploy(proj_names):
    #__opts__ = salt.config.minion_config('/etc/salt/minion')
    #__grains__ = salt.loader.grains(__opts__)

    #get pillar data
    JENKINS_URL = __pillar__['JENKINS_URL']
    JENKINS_USER = __pillar__['JENKINS_USER']
    JENKINS_PASSWORD = __pillar__['JENKINS_PASSWORD']
    JENKINS_NOTIF_MQ_URL = __pillar__['JENKINS_NOTIF_MQ_URL']
    JENKINS_NOTIF_MQ_QUEUE = __pillar__['JENKINS_NOTIF_MQ_QUEUE']
    VIRGO_HOME = __pillar__['VIRGO_HOME']
    VIRGO_LOCAL_REPOSITORY = __pillar__['VIRGO_LOCAL_REPOSITORY']
    MAVEN_REPOSITORY_URL = __pillar__['MAVEN_REPOSITORY_URL']
    MAVEN_USER = __pillar__['MAVEN_USER']
    MAVEN_PASSWORD = __pillar__['MAVEN_PASSWORD']
    APP_TIME_OUT = __pillar__['APP_TIME_OUT']
    APP_SUCCESS_LOG = __pillar__['APP_SUCCESS_LOG']
    BUNDLE_LIST = __pillar__['bundles:bind:BUNDLE_LIST']


    LOCAL_TEMP_PATH = VIRGO_HOME + os.path.sep + 'work' + os.path.sep + 'tmp'

    log_path = VIRGO_HOME + os.path.sep + 'serviceability'

    if not os.path.exists(log_path):
        os.mkdir(log_path)

    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%d %b %Y %H:%M:%S',
                    filename= log_path + os.path.sep + 'virgo-deploy.log',
                    filemode='w')

    log = logging.getLogger("virgo-deploy")

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
    deploy = BundleDeployer(VIRGO_HOME, VIRGO_LOCAL_REPOSITORY,APP_TIME_OUT, APP_SUCCESS_LOG)

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

    except Exception,e:
        log.error('Error deploying ' + proj_names )
        log.error(str(sys.exc_info()[0]) + ' - ' + str(sys.exc_info()[1]))
        return False

    return True
