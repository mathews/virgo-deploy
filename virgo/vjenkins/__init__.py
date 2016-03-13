# -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 00:32:38 2016

@author: mathews
"""

from jenkins import Jenkins,EMPTY_CONFIG_XML
from virgo import rabbitmq
import time, threading, logging

GIT_CONFIG_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<project>
    <actions/>
    <description/>
    <keepDependencies>false</keepDependencies>
    <properties>
        <hudson.model.ParametersDefinitionProperty>
            <parameterDefinitions>
                <hudson.model.StringParameterDefinition>
                    <name>project_version</name>
                    <description>project version</description>
                    <defaultValue>1.0.0</defaultValue>
                </hudson.model.StringParameterDefinition>
            </parameterDefinitions>
        </hudson.model.ParametersDefinitionProperty>
    </properties>
    <scm class="hudson.plugins.git.GitSCM" plugin="git@2.4.1">
        <configVersion>2</configVersion>
        <userRemoteConfigs>
            <hudson.plugins.git.UserRemoteConfig>
                <url>https://github.com/mathews/proj_name</url>
                <credentialsId>bae5f83b-cd2d-49f6-8f65-676aa38ad255</credentialsId>
            </hudson.plugins.git.UserRemoteConfig>
        </userRemoteConfigs>
        <branches>
            <hudson.plugins.git.BranchSpec>
                <name>*/master</name>
            </hudson.plugins.git.BranchSpec>
        </branches>
        <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
        <submoduleCfg class="list"/>
        <extensions/>
    </scm>
    <canRoam>true</canRoam>
    <disabled>false</disabled>
    <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
    <blockBuildWhenUpstreamBuilding>true</blockBuildWhenUpstreamBuilding>
    <jdk>(System)</jdk>
    <triggers/>
    <concurrentBuild>false</concurrentBuild>
    <builders>
        <hudson.tasks.Maven>
            <targets>deploy -Dmaven.test.skip=true</targets>
            <mavenName>jenkins-maven-3.3.9</mavenName>
            <usePrivateRepository>false</usePrivateRepository>
            <settings class="jenkins.mvn.FilePathSettingsProvider">
                <path>/home/mathews/dev/apache-maven-3.3.1/conf/settings-artifactory.xml</path>
            </settings>
            <globalSettings class="jenkins.mvn.FilePathGlobalSettingsProvider">
                <path>/home/mathews/dev/apache-maven-3.3.1/conf/settings-artifactory.xml</path>
            </globalSettings>
        </hudson.tasks.Maven>
    </builders>
    <publishers>
        <org.jenkinsci.plugins.rabbitmqbuildtrigger.RemoteBuildPublisher plugin="rabbitmq-build-trigger@2.3">
            <brokerName>jenkins_job_notif</brokerName>
            <routingKey>jenkins_job_notif</routingKey>
        </org.jenkinsci.plugins.rabbitmqbuildtrigger.RemoteBuildPublisher>
    </publishers>
    <buildWrappers/>
</project>'''

SVN_CONFIG_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<project>
    <actions/>
    <description/>
    <keepDependencies>false</keepDependencies>
    <properties>
        <hudson.model.ParametersDefinitionProperty>
            <parameterDefinitions>
                <hudson.model.StringParameterDefinition>
                    <name>project_version</name>
                    <description>project version</description>
                    <defaultValue>1.0.0</defaultValue>
                </hudson.model.StringParameterDefinition>
            </parameterDefinitions>
        </hudson.model.ParametersDefinitionProperty>
    </properties>
    <scm class="hudson.scm.SubversionSCM" plugin="subversion@1.54">
        <locations>
            <hudson.scm.SubversionSCM_-ModuleLocation>
                <remote>http://svn.apache.org/repos/asf/proj_name</remote>
                <credentialsId>2864f190-1d7b-444b-8aa9-b02da5196edf</credentialsId>
                <local>.</local>
                <depthOption>infinity</depthOption>
                <ignoreExternalsOption>false</ignoreExternalsOption>
            </hudson.scm.SubversionSCM_-ModuleLocation>
        </locations>
        <excludedRegions />
        <includedRegions />
        <excludedUsers />
        <excludedRevprop />
        <excludedCommitMessages />
        <workspaceUpdater class="hudson.scm.subversion.UpdateUpdater" />
        <ignoreDirPropChanges>false</ignoreDirPropChanges>
        <filterChangelog>false</filterChangelog>
    </scm>
    <canRoam>true</canRoam>
    <disabled>false</disabled>
    <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
    <blockBuildWhenUpstreamBuilding>true</blockBuildWhenUpstreamBuilding>
    <jdk>(System)</jdk>
    <triggers/>
    <concurrentBuild>false</concurrentBuild>
    <builders>
        <hudson.tasks.Maven>
            <targets>deploy -Dmaven.test.skip=true</targets>
            <mavenName>jenkins-maven-3.3.9</mavenName>
            <usePrivateRepository>false</usePrivateRepository>
            <settings class="jenkins.mvn.FilePathSettingsProvider">
                <path>/home/mathews/dev/apache-maven-3.3.1/conf/settings-artifactory.xml</path>
            </settings>
            <globalSettings class="jenkins.mvn.FilePathGlobalSettingsProvider">
                <path>/home/mathews/dev/apache-maven-3.3.1/conf/settings-artifactory.xml</path>
            </globalSettings>
        </hudson.tasks.Maven>
    </builders>
    <publishers>
        <org.jenkinsci.plugins.rabbitmqbuildtrigger.RemoteBuildPublisher plugin="rabbitmq-build-trigger@2.3">
            <brokerName>jenkins_job_notif</brokerName>
            <routingKey>jenkins_job_notif</routingKey>
        </org.jenkinsci.plugins.rabbitmqbuildtrigger.RemoteBuildPublisher>
    </publishers>
    <buildWrappers/>
</project>'''



log = logging.getLogger('vjenkins')

SVN = 'svn'
GIT = 'git'

class JenkinsBuilder:

    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'

    def __init__(self, url='http://localhost:8080/jenkins',userName='admin',passwd='admin', \
                 mq_url = 'amqp://guest:guest@localhost:5672//',queue = 'jenkins_job_notif'):
        # the jenkins server object
        self.server = Jenkins(url, username=userName, password=passwd)
        # this is the base job, which contains
        self.baseJob = 'proj_base'

        self._mq_url = mq_url
        self._queue = queue
        #default build is unsuccessful.
        self.buildResult = self.FAILURE
        self.buildNotifReceived = False

    def setScmParams(self,scm_type,scm_url, scm_credential_id):
        '''
        set SCM parameters
        :param scm_type: svn or git
        :param scm_url: svn or git url
        :param scm_credential_id: the id for the credential saved in jenkins
        :return:
        '''

        self._scm_type = scm_type
        self._scm_url = scm_url
        self._scm_credential_id = scm_credential_id

    def processBuildNotif(self,body, message):
        #set flag of build result
        self.buildResult = body['status']
        build_proj = body['project']
        build_num = body['number']

        if build_num == self._next_build_num and build_proj == self.baseJob:

            #rabbitmq.handle_message(body, message)
            self.buildNotifReceived = True
            log.info( 'build Notification Received, Build is ' + self.buildResult )
            self.client.stop()

            return True
        else:
            return False

    def loop(self):
        while self.buildNotifReceived == False:
             time.sleep(5)


    def build_project(self,proj_name):
        log.debug('executing build_project()')

        # build project will create a jenkins job with the project name,s
        # and build the project, if the build fails, just print error.
        # we depend maven deploy to deploy released packages into artifactory

        #query jobs list
        #print server.jobs_count()
        #jobs = server.get_jobs()
        #print jobs

        if self._scm_type != None:
            if self._scm_type == GIT:
                config_xml = GIT_CONFIG_XML.replace('proj_name',proj_name)
                if self._scm_url != None:
                    config_xml = config_xml.replace('https://github.com/mathews',self._scm_url)
                if self._scm_credential_id != None:
                    config_xml = config_xml.replace('bae5f83b-cd2d-49f6-8f65-676aa38ad255',self._scm_credential_id)
            else:
                config_xml = SVN_CONFIG_XML.replace('proj_name',proj_name)
                if self._scm_url != None:
                    config_xml = config_xml.replace('http://svn.apache.org/repos/asf',self._scm_url)
                if self._scm_credential_id != None:
                    config_xml = config_xml.replace('2864f190-1d7b-444b-8aa9-b02da5196edf',self._scm_credential_id)


        if self.server.job_exists(proj_name):
            self.server.enable_job(proj_name)
        else:
            self.server.create_job(proj_name, config_xml)


        ## the build info is for the last one, not this build
        ## if the last build is within an hour, escape build
        ## you have to listen for the job notification
        build_info = self.server.get_job_info(proj_name, 10)
        #print build_info

        if build_info != None:

            #TODO if the project is building in queue, just wait


            self._next_build_num = build_info['nextBuildNumber']

            log.info( 'next_build_num = '+str(self._next_build_num))


            last_build = build_info['lastBuild']
            log.info( 'Last Build is ' + str(last_build))

            toBuild = False

            if last_build != None:
                #build before
                lastResult = last_build['result']
                if lastResult!='SUCCESS':
                    log.warning( 'Last Build Failed! Going to build again...')
                    toBuild = True
                    self.server.build_job(proj_name,{'project_version':'1.0.0'})
                if not toBuild:
                    #last_build_timestmp is in millisecond
                    last_build_timestmp = last_build['timestamp']

                    last_build_seconds = time.time()-last_build_timestmp/1000

                    if last_build_seconds > 3600 :
                        log.warning( 'Last Build occured an hour ago! Going to build again...' )
                        #build before an hour
                        toBuild = True
                        self.server.build_job(proj_name, {'project_version':'1.0.0'})
                    else:
                        log.warning( 'Last Build is within an hour, going to ignore building ...')
            else:
                #not build before
                log.info( 'Not Build Before! Going to build again...')
                toBuild = True
                self.server.build_job(proj_name, {'project_version':'1.0.0'})


        #perhaps the build will last for hours, we need to listen rabbitMQ
        #for notifications about build failures
        if toBuild:
            self.client = rabbitmq.RabbitmqClient(self._mq_url,self._queue)
            t0 = self.client.registerCallback(self.processBuildNotif)

            t1 = threading.Thread(target=self.loop)
            t1.start()
            log.info( 'waiting for build notification.... ')
            t1.join()

            log.info( 'build result is ' + self.buildResult )
        else:
            self.buildResult=self.SUCCESS

        return self.buildResult