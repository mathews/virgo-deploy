from virgo.vjenkins import JenkinsBuilder
from virgo.httpclient import BundleDownloader
from virgo.httpclient import BUNDLE_TYPES
from virgo.deploy import BundleDeployer
import logging, os, sys


JENKINS_URL = 'http://localhost:8080/jenkins'
JENKINS_USER = 'admin'
JENKINS_PASSWORD = 'admin'
#JENKINS_BASE_PROJECT = 'proj_base'
JENKINS_NOTIF_MQ_URL = 'amqp://guest:guest@localhost:5672//'
JENKINS_NOTIF_MQ_QUEUE = 'jenkins_job_notif'

VIRGO_HOME = '/home/mathews/dev/virgo-tomcat-server-3.0.2.BACK'
VIRGO_LOCAL_REPOSITORY = '.m2'

MAVEN_REPOSITORY_URL = 'http://localhost:9090/artifactory/libs-release-local'
MAVEN_USER = 'admin'
MAVEN_PASSWORD = 'password'

#LOCAL_TEMP_PATH = '/tmp'
LOCAL_TEMP_PATH = VIRGO_HOME + os.path.sep + 'work' + os.path.sep + 'tmp'

def __init__():
    log_path = VIRGO_HOME + os.path.sep + 'serviceability'

    if not os.path.exists(log_path):
        os.mkdir(log_path)

    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%d %b %Y %H:%M:%S',
                    filename= log_path + os.path.sep + 'virgo-deploy.log',
                    filemode='w')

def deploy(proj_name):
    __init__()

    log = logging.getLogger("virgo-deploy")

    #builder = JenkinsBuilder(JENKINS_URL, JENKINS_USER,JENKINS_PASSWORD, \
    #                         JENKINS_NOTIF_MQ_URL,JENKINS_NOTIF_MQ_QUEUE)
    #builder.build_project(proj_name)

    try:
        d = BundleDownloader(MAVEN_REPOSITORY_URL, MAVEN_USER, MAVEN_PASSWORD, LOCAL_TEMP_PATH)
        tmpBunlde = d.download('orchastack.core.tx', 'orchastack.core.tx.handler', '0.0.1', BUNDLE_TYPES['jar'])

        deploy = BundleDeployer(VIRGO_HOME, VIRGO_LOCAL_REPOSITORY)
        deploy.deploy(tmpBunlde)
        deploy.restartVirgo()
    except Exception,e:
        log.error('Error deploying ' + proj_name )
        log.error(sys.exc_info()[0] + ' - ' + sys.exc_info()[1])
        print sys.exc_info()[0],sys.exc_info()[1]
        return False

    return True


deploy('orchastack-core')
