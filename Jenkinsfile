pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: docker
    image: docker:24.0.6-dind
    privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
  - name: helm
    image: alpine/helm:3.12.0
    command:
    - cat
    tty: true
'''
        }
    }

    environment {
        // וודא שה-ID הזה קיים ב-Jenkins Credentials (מסוג Username with password)
        DOCKERHUB_CREDENTIALS = 'dockerhub'
        // שים כאן את שם המשתמש שלך ב-DockerHub
        IMAGE_NAME = '213daniel/flask-app' 
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        // ה-ID של מפתח ה-SSH ל-GitLab
        GIT_CREDS_ID = 'gitlab-key' 
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', 
                    credentialsId: "${env.GIT_CREDS_ID}", 
                    url: 'git@gitlab.com:sela-1119/students/danivaknin011/helm-charts/flask-jenkins-helm-1.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                container('docker') {
                    script {
                        echo "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}..."
                        sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                        sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest"
                    }
                }
            }
        }

        stage('Push to DockerHub') {
            steps {
                container('docker') {
                    withCredentials([usernamePassword(credentialsId: DOCKERHUB_CREDENTIALS, passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                        sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
                        sh "docker push ${IMAGE_NAME}:${IMAGE_TAG}"
                        sh "docker push ${IMAGE_NAME}:latest"
                    }
                }
            }
        }

        stage('Deploy with Helm') {
            steps {
                container('helm') {
                    script {
                        echo "Deploying to Kubernetes with Helm..."
                        // וודא ששם התיקייה 'helm-chart' תואם למה שיש לך ב-Repo
                        sh """
                        helm upgrade --install flask-app ./my-daniel-chart \
                            --set image.repository=${IMAGE_NAME} \
                            --set image.tag=${IMAGE_TAG} \
                            --wait
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully! 🚀'
        }
        failure {
            echo 'Pipeline failed. Check the logs above. ❌'
        }
    }
}