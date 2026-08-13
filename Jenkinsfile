pipeline {
    agent any

    environment {
        COMPOSE_PROJECT = 'devops-flask-pipeline'
    }

    stages {

        stage('Calculate the version of the build') {
            steps {
                script {
                    def GIT_HASH = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()

                    echo "Git Hash: ${GIT_HASH}"
                    sh 'pwd'
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

                        echo "Currently active environment: ${ACTIVE_ENV}"

                        /*
                         * Make sure shared infrastructure exists.
                         * Jenkins owns this Compose project.
                         */
                        sh '''
                            docker-compose -p ${COMPOSE_PROJECT} up -d --build mysql nginx
                        '''

                        if (ACTIVE_ENV == 'BLUE') {

                            echo "BLUE is currently active."
                            echo "Deploying GREEN..."

                            sh '''
                                docker-compose -p ${COMPOSE_PROJECT} build flask-green
                                docker-compose -p ${COMPOSE_PROJECT} up -d flask-green
                            '''

                        } else if (ACTIVE_ENV == 'GREEN') {

                            echo "GREEN is currently active."
                            echo "Deploying BLUE..."

                            sh '''
                                docker-compose -p ${COMPOSE_PROJECT} build flask-blue
                                docker-compose -p ${COMPOSE_PROJECT} up -d flask-blue
                            '''

                        } else {

                            error "Invalid active environment: ${ACTIVE_ENV}"

                        }
                    }
                }
            }
        }

        stage('Health Check New Environment') {
            steps {
                script {

                    def ACTIVE_ENV = readFile('active-environment.txt').trim()

                    if (ACTIVE_ENV == 'BLUE') {

                        echo "Checking GREEN..."

                        sh '''
                            docker-compose -p ${COMPOSE_PROJECT} exec -T flask-green \
                            python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000')"
                        '''

                    } else if (ACTIVE_ENV == 'GREEN') {

                        echo "Checking BLUE..."

                        sh '''
                            docker-compose -p ${COMPOSE_PROJECT} exec -T flask-blue \
                            python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000')"
                        '''

                    } else {

                        error "Invalid active environment: ${ACTIVE_ENV}"

                    }
                }
            }
        }

        stage('Switch Traffic') {
            steps {
                script {

                    def ACTIVE_ENV = readFile('active-environment.txt').trim()

                    if (ACTIVE_ENV == 'BLUE') {

                        echo "Switching traffic: BLUE → GREEN"

                        sh '''
                            sed -i 's/flask-blue:5000/flask-green:5000/' nginx/nginx.conf

                            docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -t

                            docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -s reload
                        '''

                    } else if (ACTIVE_ENV == 'GREEN') {

                        echo "Switching traffic: GREEN → BLUE"

                        sh '''
                            sed -i 's/flask-green:5000/flask-blue:5000/' nginx/nginx.conf

                            docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -t

                            docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -s reload
                        '''

                    } else {

                        error "Invalid active environment: ${ACTIVE_ENV}"

                    }
                }
            }
        }

        stage('Verify Traffic') {
            steps {
                sh '''
                    curl --fail --silent http://host.docker.internal
                '''
            }
        }

        stage('Update Active Environment') {
            steps {
                script {

                    def ACTIVE_ENV = readFile('active-environment.txt').trim()

                    if (ACTIVE_ENV == 'BLUE') {

                        writeFile(
                            file: 'active-environment.txt',
                            text: 'GREEN\n'
                        )

                        echo "GREEN is now the active environment."

                    } else if (ACTIVE_ENV == 'GREEN') {

                        writeFile(
                            file: 'active-environment.txt',
                            text: 'BLUE\n'
                        )

                        echo "BLUE is now the active environment."

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
Active Environment: ${readFile('active-environment.txt').trim()}
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
                sh 'sleep 10'
            }
        }

        stage('Final Health Check') {
            steps {
                sh '''
                    curl --fail --silent http://host.docker.internal
                '''
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
