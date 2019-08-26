@Library('common-pipelines@10.16.0') _

import groovy.transform.Field
import org.doordash.JenkinsDd

// -----------------------------------------------------------------------------------
//
// CD pipeline for payment-service
//
// The following params are automatically provided by the callback gateway as inputs
// to the Jenkins pipeline that starts this job.
//
// params["SHA"]                    - Sha used to start the pipeline
// params["BRANCH_NAME"]            - Name of GitHub branch the SHA is associated with
// params["UNIQUE_BUILD_ID"]        - A randomly generated unique ID for this job run
// params["ENQUEUED_AT_TIMESTAMP"]  - Unix timestamp generated by callback gateway
// params["JSON"]                   - Extensible json doc with extra information
// params["GITHUB_REPOSITORY"]      - GitHub ssh url of repository (git://....)
// -----------------------------------------------------------------------------------

@Field
def runningStage = "Not Started"

pipeline {
  options {
    timestamps()
    skipStagesAfterUnstable()
    timeout(time: 30, unit: 'MINUTES')
  }
  agent {
    label 'universal'
  }
  stages {
    stage('Rollback Start Up') {
      steps {
        script {
          runningStage = env.STAGE_NAME
          common.notifySlackChannelDeploymentStatus(runningStage, params['SHA'], "${env.BUILD_NUMBER}", "started")
        }
        artifactoryLogin()
        script {
          /**
           * Beware: Github does not offer a way for us to "protect" git tags. Any
           * developer can "force push" tags causing chaos and GitHub offers no way
           * for us to prevent that.
           *
           * Ddops maintains it's own immutable database of sha/semvertag bindings and
           * the getImmutableReleaseSemverTag() function will retrieve the semver tag
           * value that was originally registered with the params['SHA'].
           *
           * If you decide to access the original semver value, please do not use it for
           * anything important. In other words your "1.0.0" tag might have been "force
           * pushed" around. You could unknowingly end up building/deploying (etc) a
           * version of that code that doesn't match the params['SHA'] value.
           */
          env.tag = getImmutableReleaseSemverTag(params['SHA'])
          common = load "${WORKSPACE}/Jenkinsfile-common.groovy"
        }
      }
    }
    stage('Rollback Deploy to prod') {
      steps {
        script {
          runningStage = env.STAGE_NAME
          common.notifySlackChannelDeploymentStatus(runningStage, params['SHA'], "${env.BUILD_NUMBER}", "started")
        }
        script {
          common.deployHelm(env.tag, common.getServiceName(), 'prod')
        }
        sendSlackMessage 'eng-deploy-manifest', "Successfully rollback ${common.getServiceName()}: <${JenkinsDd.instance.getBlueOceanJobUrl()}|${env.JOB_NAME} [${env.BUILD_NUMBER}]>"
      }
      post {
        success {
          script {
            common.notifySlackChannelDeploymentStatus(runningStage, params['SHA'], "${env.BUILD_NUMBER}", "success")
          }
        }
      }
    }
    stage('Rollback Deploy Pulse to prod') {
      steps {
        script {
          runningStage = env.STAGE_NAME
          common.notifySlackChannelDeploymentStatus(runningStage, params['SHA'], "${env.BUILD_NUMBER}", "started")
        }
        script {
          common.deployPulse(params['GITHUB_REPOSITORY'], params['SHA'], params['BRANCH_NAME'], common.getServiceName(), 'prod')
        }
      }
    }
  }
  post {
    always {
      script {
        common.removeAllContainers()
      }
    }
    success {
      script {
        common.notifySlackChannelDeploymentStatus("Successful Rollback", params['SHA'], "${env.BUILD_NUMBER}", "success", true)
      }
    }
    aborted {
      script {
        common.notifySlackChannelDeploymentStatus("Aborted Rollback", params['SHA'], "${env.BUILD_NUMBER}", "aborted", true)
      }
    }
    failure {
      script {
        common.notifySlackChannelDeploymentStatus("Failed Rollback", params['SHA'], "${env.BUILD_NUMBER}", "failure", true)
      }
    }
  }
}
