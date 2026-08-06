pipeline {
   agent any

   stages {
       stage('Build Docker Image'){
            steps {
                  sh 'pwd'
                  sh 'GIT_HASH=$(git rev-parse --short HEAD)'
                  sh 'docker build -t flask-app:$GIT_HASH .'
            }
       }
   }
}
