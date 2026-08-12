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
                    script { 

                        def ACTIVE_ENV = readFile('active-environment.txt').trim()
                        if (ACTIVE_ENV == 'BLUE') {
                           
                            echo "BLUE is currently active."
                            echo "Deploying GREEN..." 

                            sh """
                              docker-compose build flask-green
                              docker-compose up -d flask-green
                            """
                       } else if (ACTIVE_ENV == 'GREEN') {

                           echo "GREEN is currently active."
                           echo "Deploying BLUE..."
                          
                           sh """
                              docker-compose build flask-blue
                              docker-compose up -d flask-blue
                           """ 
                       } else {

                           error "Invalid active environment: ${ACTIVE_ENV}"
 
                       }
                    }
                }
            }
        }

        stage('Health check New Environment'){
            steps {
                script {
                    def ACTIVE_ENV = readFile('active-environment.txt').trim()
                    if ( ACTIVE_ENV == 'BLUE' ){
                         echo "Checking GREEN..."
                         sh """
                            docker-compose exec -T flask-green python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000')"
                         """
                    } else if (ACTIVE_ENV == 'GREEN') {
                        echo "Checking BLUE..."
                        sh """
                           docker-compose exec -T flask-blue python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000')"
                        """
                    } else {
                        error "Invalid active environment: ${ACTIVE_ENV}"
                    }
                }
            }
        }
                     
        stage('Create Build Artifact') {
            steps {
                script {
                    writeFile(
                         file: 'build-info.txt',
                         text: """Build Number: ${BUILD_NUMBER}
                         Git Commit: ${GIT_COMMIT}
                         """
                    )
                }
            }    
        }

        stage('Archive Artifact') {
             steps {
                 archiveArtifacts artifacts: 'build-info.txt'
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
