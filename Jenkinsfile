pipeline {
    agent any

    stages {

        stage('Build Docker Image') {
            steps {

                script {
                   def GIT_HASH = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                }

                echo "Git Hash: ${GIT_HASH}"

                sh "pwd"

                sh "docker build -t flask-app:${BUILD_NUMBER}-${GIT_HASH} ."

                sh "docker run --name flask-app -d -p 5000:5000 flask-app:${BUILD_NUMBER}-${GIT_HASH}"

            }
        }

    }
}
