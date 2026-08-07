pipeline {
    agent any

    stages {

        stage('Deploy Application') {
            steps {
                sh """
                    docker compose down

                    docker compose up -d --build
                """
            }
        }

        stage('Wait for Services') {
            steps {
                sh "sleep 10"
            }
        }

        stage('Health Check') {
            steps {
                sh "curl --fail http://host.docker.internal"
            }
        }
    }
}
