pipeline {
  agent {
    node {
      label 'team:iow'
    }
  }
  stages {
    stage('Set Build Description') {
      steps {
        script {
          currentBuild.description = "Deploy to ${env.DEPLOY_STAGE}"
        }
      }
    }
    stage('Clean Workspace') {
      steps {
        cleanWs()
      }
    }
    stage('Checkout scripts') {
      steps {
        checkout scm // Checks out the repo where the Jenkinsfile is located
      }
    }
    stage('Download EPA WQX dump files') {
      steps {
        sh '''set +e
           mkdir -p $WORKSPACE/wqx
           sed -i 's/\r$//g' $WORKSPACE/epa_wqx_download.py
           chmod +x $WORKSPACE/epa_wqx_download.py

           docker run --rm \
              -v $WORKSPACE:/usr/src \
              usgswma/python:3.8 \
              /usr/src/epa_wqx_download.py -d /usr/src/wqx 
        '''
      }
    }
    stage('Load EPA WQX dump files') {
      steps {
        script {
          def mappedStage = ""
          def deployStage = "$DEPLOY_STAGE"
          switch(deployStage) {
            case "PROD-EXTERNAL":
              mappedStage = "legacy-production-external"
              break
            case "QA":
              mappedStage = "legacy-qa"
              break
            case "TEST":
              mappedStage = "legacy-test"
              break
            default:
              mappedStage = "development"
          }
          env.MAPPED_STAGE = mappedStage
          def secretsString = sh(script: '/usr/local/bin/aws ssm get-parameter --name "/aws/reference/secretsmanager/WQP-EXTERNAL-$DEPLOY_STAGE" --query "Parameter.Value" --with-decryption --output text --region "us-west-2"', returnStdout: true).trim()
          def secretsJson =  readJSON text: secretsString

          env.EPA_DATABASE_ADDRESS = secretsJson.DATABASE_ADDRESS
          env.EPA_DATABASE_NAME = secretsJson.DATABASE_NAME
          env.DATABASE_PORT = secretsJson.DATABASE_PORT
          env.EPA_SCHEMA_OWNER_USERNAME = secretsJson.EPA_SCHEMA_OWNER_USERNAME
          env.EPA_SCHEMA_OWNER_PASSWORD = secretsJson.EPA_SCHEMA_OWNER_PASSWORD

          sh '''
            set +e
            sed -i 's/\r$//g' $WORKSPACE/load_epa_wqx_dump_files.sh
            chmod +x $WORKSPACE/load_epa_wqx_dump_files.sh

            docker run -e "EPA_DATABASE_ADDRESS=$EPA_DATABASE_ADDRESS" \
               -e "EPA_SCHEMA_OWNER_USERNAME=$EPA_SCHEMA_OWNER_USERNAME \
               -e "EPA_SCHEMA_OWNER_PASSWORD=$EPA_SCHEMA_OWNER_PASSWORD \
               -e "EPA_DATABASE_NAME=$EPA_DATABASE_NAME" \
               -e "DATABASE_PORT=$EPA_DATABASE_PORT" \
               -e "DATABASE_PORT=$DATABASE_PORT" \
               -e "EPA_WQX_DUMP_DIR=/usr/src/wqx" \
               --rm \
               -v $WORKSPACE:/usr/src \
               usgswma/python:3.8 \
               /usr/src/load_epa_wqx_dump_files.sh
            '''
        }
      }
    }
  }
}
