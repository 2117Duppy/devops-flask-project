pipeline {
    agent any

    stages {

        stage('Calculate the version of the build') {
            steps {
                script {
                    def GIT_HASH = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()

                    echo "Git Hash: ${GIT_HASH}"
                    sh "pwd"
                }
            }
        }

        stage('Deploy Application') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'mysql-root-password',
                        variable: 'MYSQL_ROOT_PASSWORD'
                    ),
                    string(
                        credentialsId: 'mysql-database',
                        variable: 'MYSQL_DATABASE'
                    ),
                    string(
                        credentialsId: 'mysql-user',
                        variable: 'MYSQL_USER'
                    )
                ]) {
                    sh """
                        docker-compose down
                        docker-compose up -d --build
                    """
                }
            }
        }

        stage('Wait for Services') {
            steps {
                sh "sleep 10"
            }
        }

        stage('Health Check') {
            steps {
                sh "curl --fail --silent http://host.docker.internal"
            }
        }
    }
    
    post {

        success {
            echo 'Pipeline completed successfully!'
        }

        failure {
            echo 'Pipeline failed!'
        }

        always {
            echo 'Pipeline finished.'
        }
    }
}
