pipeline {
    agent any

    stages {

        stage('Build Docker Image') {
            steps {

                script {
                    GIT_HASH = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                }

                echo "Git Hash: ${GIT_HASH}"

                sh "pwd"

                sh "docker build -t flask-app:${BUILD_NUMBER}-${GIT_HASH} ."

            }
        }

    }
}
