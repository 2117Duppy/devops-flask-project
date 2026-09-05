pipeline {
    agent any

    environment {
        COMPOSE_PROJECT = 'devops-flask-pipeline'
    }

    stages {

        stage('Test EC2 SSH Access') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'ec2-deploy-key',
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no \
                        -i "$SSH_KEY" \
                        "$SSH_USER@13.127.50.247" \
                        "whoami && hostname"
                    '''
                }
            }
        }

        stage('Test EC2 Project Access') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'ec2-deploy-key',
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no \
                            -i "$SSH_KEY" \
                            "$SSH_USER@13.127.50.247" \
                            "pwd && ls -la"
                    '''
                }
            }
        }

        stage('Test EC2 Docker Access') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'ec2-deploy-key',
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no \
                            -i "$SSH_KEY" \
                            "$SSH_USER@13.127.50.247" \
                            "cd /home/ubuntu/devops-flask-project && docker compose ps"
                    '''
                }
            }
        }

        stage('Test AWS Access') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'aws-jenkins-deployer',
                        usernameVariable: 'AWS_ACCESS_KEY_ID',
                        passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                    )
                ]) {
                    sh '''
                        aws sts get-caller-identity

                        echo "Checking ALB target groups..."

                        aws elbv2 describe-target-groups \
                        --region ap-south-1 \
                        --query 'TargetGroups[].{Name:TargetGroupName,Arn:TargetGroupArn}' \
                        --output table
                    '''
                }
            }
        }

        stage('Detect ALB Active Environment') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'aws-jenkins-deployer',
                        usernameVariable: 'AWS_ACCESS_KEY_ID',
                        passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                    )
                ]) {
                    script {

                        def ACTIVE_TG = sh(
                            script: '''
                                aws elbv2 describe-listeners \
                                    --region ap-south-1 \
                                    --load-balancer-arn $(aws elbv2 describe-load-balancers \
                                        --region ap-south-1 \
                                        --names devops-flask-alb \
                                        --query 'LoadBalancers[0].LoadBalancerArn' \
                                        --output text) \
                                    --query 'Listeners[0].DefaultActions[0].TargetGroupArn' \
                                    --output text
                            ''',
                            returnStdout: true
                        ).trim()

                        echo "Active ALB Target Group ARN: ${ACTIVE_TG}"

                        if (ACTIVE_TG.contains('devops-flask-green-tg')) {
                            echo "🟢 ALB is currently pointing to GREEN"
                        } else if (ACTIVE_TG.contains('devops-flask-tg')) {
                            echo "🔵 ALB is currently pointing to BLUE"
                        } else {
                            error "Unknown ALB target group: ${ACTIVE_TG}"
                        }
                    }
                }
            }
        }

        stage('Switch ALB Traffic') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'aws-jenkins-deployer',
                        usernameVariable: 'AWS_ACCESS_KEY_ID',
                        passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                    )
                ]) {
                    script {

                        def ALB_ARN = sh(
                            script: '''
                                set -e

                                aws elbv2 describe-load-balancers \
                                    --region ap-south-1 \
                                    --names devops-flask-alb \
                                    --query 'LoadBalancers[0].LoadBalancerArn' \
                                    --output text
                            ''',
                            returnStdout: true
                        ).trim()

                        def LISTENER_ARN = sh(
                            script: """
                                set -e

                                aws elbv2 describe-listeners \
                                    --region ap-south-1 \
                                    --load-balancer-arn '${ALB_ARN}' \
                                    --query 'Listeners[0].ListenerArn' \
                                    --output text
                            """,
                            returnStdout: true
                        ).trim()

                        def CURRENT_TG = sh(
                            script: """
                                set -e

                                aws elbv2 describe-listeners \
                                    --region ap-south-1 \
                                    --listener-arns '${LISTENER_ARN}' \
                                    --query 'Listeners[0].DefaultActions[0].TargetGroupArn' \
                                    --output text
                            """,
                            returnStdout: true
                        ).trim()

                        echo "Current Target Group: ${CURRENT_TG}"

                        def TARGET_TG = ''

                        if (CURRENT_TG.contains('devops-flask-green-tg')) {

                            echo "🟢 GREEN is active"
                            echo "Switching traffic GREEN → BLUE"

                            TARGET_TG = sh(
                                script: '''
                                    aws elbv2 describe-target-groups \
                                        --region ap-south-1 \
                                        --names devops-flask-tg \
                                        --query 'TargetGroups[0].TargetGroupArn' \
                                        --output text
                                ''',
                                returnStdout: true
                            ).trim()

                        } else if (CURRENT_TG.contains('devops-flask-tg')) {

                            echo "🔵 BLUE is active"
                            echo "Switching traffic BLUE → GREEN"

                            TARGET_TG = sh(
                                script: '''
                                    aws elbv2 describe-target-groups \
                                        --region ap-south-1 \
                                        --names devops-flask-green-tg \
                                        --query 'TargetGroups[0].TargetGroupArn' \
                                        --output text
                                ''',
                                returnStdout: true
                            ).trim()

                        } else {

                            error "Unknown current target group: ${CURRENT_TG}"

                        }

                        echo "New Target Group: ${TARGET_TG}"

                        sh """
                            set -e

                            aws elbv2 modify-listener \
                                --region ap-south-1 \
                                --listener-arn '${LISTENER_ARN}' \
                                --default-actions Type=forward,TargetGroupArn='${TARGET_TG}'
                        """

                        echo "ALB traffic switch completed."

                        def VERIFIED_TG = sh(
                            script: """
                                set -e

                                aws elbv2 describe-listeners \
                                    --region ap-south-1 \
                                    --listener-arns '${LISTENER_ARN}' \
                                    --query 'Listeners[0].DefaultActions[0].TargetGroupArn' \
                                    --output text
                            """,
                            returnStdout: true
                        ).trim()

                        echo "Verified Target Group: ${VERIFIED_TG}"

                        if (VERIFIED_TG != TARGET_TG) {
                            error "ALB traffic switch verification failed!"
                        }

                        echo "✅ ALB traffic switch verified successfully."
                    }
                }
            }
        }

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
                        // Nginx is the source of truth.
                        // Check which Flask environment is currently receiving traffic.
                        def ACTIVE_ENV = sh(
                            script: '''
                                set -e

                                ACTIVE=$(docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -T 2>/dev/null |
                                    grep 'proxy_pass http://flask-' |
                                    head -n 1)

                                if echo "$ACTIVE" | grep -q "flask-green:5000"; then
                                    echo "GREEN"
                                elif echo "$ACTIVE" | grep -q "flask-blue:5000"; then
                                    echo "BLUE"
                                else
                                    echo "ERROR"
                                    exit 1
                                fi
                            ''',
                            returnStdout: true
                        ).trim()

                        echo "Currently active environment: ${ACTIVE_ENV}"

                        // Make sure MySQL and Nginx are running.
                        // sh '''
                        //     docker-compose -p ${COMPOSE_PROJECT} up -d --build mysql nginx
                        // '''

                        sh '''
                            docker-compose -p ${COMPOSE_PROJECT} up -d mysql
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

                    def ACTIVE_ENV = sh(
                        script: '''
                            docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -T 2>/dev/null |
                            grep -q "proxy_pass http://flask-green:5000;" &&
                            echo "GREEN" ||
                            echo "BLUE"
                        ''',
                        returnStdout: true
                    ).trim()

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

        stage('Switch Traffic and Verify') {
            steps {
                script {

                    def ACTIVE_ENV = sh(
                        script: '''
                            docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -T 2>/dev/null |
                            grep -q "proxy_pass http://flask-green:5000;" &&
                            echo "GREEN" ||
                            echo "BLUE"
                        ''',
                        returnStdout: true
                    ).trim()

                    try {

                        if (ACTIVE_ENV == 'BLUE') {

                            echo "Switching traffic: BLUE → GREEN"

                            sh '''
                                sed -i 's/flask-blue:5000/flask-green:5000/' nginx/nginx.conf

                                docker cp nginx/nginx.conf \
                                devops-flask-pipeline-nginx-1:/etc/nginx/nginx.conf

                                docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -t

                                docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -s reload
                            '''

                            echo "Verifying traffic is now going to GREEN..."

                            sh '''
                                docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -T \
                                | grep 'proxy_pass http://flask-green:5000;'

                                curl --fail --silent http://host.docker.internal
                            '''

                        } else if (ACTIVE_ENV == 'GREEN') {

                            echo "Switching traffic: GREEN → BLUE"

                            sh '''
                                sed -i 's/flask-green:5000/flask-blue:5000/' nginx/nginx.conf

                                docker cp nginx/nginx.conf \
                                devops-flask-pipeline-nginx-1:/etc/nginx/nginx.conf

                                docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -t

                                docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -s reload
                            '''

                            echo "Verifying traffic is now going to BLUE..."

                            sh '''
                                docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -T \
                                | grep 'proxy_pass http://flask-blue:5000;'

                                curl --fail --silent http://host.docker.internal
                            '''

                        } else {

                            error "Invalid active environment: ${ACTIVE_ENV}"

                        }

                    } catch (err) {

                        echo "Traffic verification failed!"
                        echo "Starting rollback..."

                        if (ACTIVE_ENV == 'BLUE') {

                            echo "Rolling back: GREEN → BLUE"

                            sh '''
                                sed -i 's/flask-green:5000/flask-blue:5000/' nginx/nginx.conf

                                docker cp nginx/nginx.conf \
                                devops-flask-pipeline-nginx-1:/etc/nginx/nginx.conf

                                docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -t

                                docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -s reload
                            '''

                        } else if (ACTIVE_ENV == 'GREEN') {

                            echo "Rolling back: BLUE → GREEN"

                            sh '''
                                sed -i 's/flask-blue:5000/flask-green:5000/' nginx/nginx.conf

                                docker cp nginx/nginx.conf \
                                devops-flask-pipeline-nginx-1:/etc/nginx/nginx.conf

                                docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -t

                                docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -s reload
                            '''
                        }

                        echo "Rollback completed."

                        throw err
                    }
                }
            }
        }

        stage('Cleanup Old Environment') {
            steps {
                script {

                    // After the traffic switch, ask Nginx which environment
                    // is actually active now.
                    def ACTIVE_ENV = sh(
                        script: '''
                            docker-compose -p ${COMPOSE_PROJECT} exec -T nginx nginx -T 2>/dev/null |
                            grep -q "proxy_pass http://flask-green:5000;" &&
                            echo "GREEN" ||
                            echo "BLUE"
                        ''',
                        returnStdout: true
                    ).trim()

                    if (ACTIVE_ENV == 'GREEN') {

                        echo "GREEN is active and verified."
                        echo "Stopping old BLUE environment..."

                        sh '''
                            docker-compose -p ${COMPOSE_PROJECT} stop flask-blue
                        '''

                    } else if (ACTIVE_ENV == 'BLUE') {

                        echo "BLUE is active and verified."
                        echo "Stopping old GREEN environment..."

                        sh '''
                            docker-compose -p ${COMPOSE_PROJECT} stop flask-green
                        '''

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