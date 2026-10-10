pipeline {
    agent any

    parameters {
        string(name: 'APPLICATION', defaultValue: 'OrderHub', description: 'Application to investigate')
        string(name: 'ERROR_TEXT', defaultValue: '', description: 'Sanitized incident message')
        string(name: 'EVENT_TIME', defaultValue: '', description: 'Optional event time')
        string(name: 'ORDER_ID', defaultValue: '', description: 'Optional order id')
        string(name: 'CORRELATION_ID', defaultValue: '', description: 'Optional correlation id')
    }

    stages {
        stage('Pull dummy server reference logs') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dummy-server-reader',
                    usernameVariable: 'DUMMY_SERVER_USERNAME',
                    passwordVariable: 'DUMMY_SERVER_PASSWORD'
                )]) {
                    script {
                        if (isUnix()) {
                            sh 'python -m pip install -r requirements.txt && python jenkins_pipeline.py'
                        } else {
                            bat 'py -3 -m pip install -r requirements.txt && py -3 jenkins_pipeline.py'
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reference-logs.json', allowEmptyArchive: true
        }
    }
}
