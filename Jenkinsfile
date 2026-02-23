pipeline {
    agent {
        kubernetes {
            yaml '''
            apiVersion: v1
            kind: Pod
            metadata:
              labels:
                app: jenkins-agent
            spec:
              serviceAccountName: jenkins-deployer
              containers:
              - name: python
                image: python:3.9-slim
                command: ['cat']
                tty: true
              - name: docker
                image: docker:cli
                command: ['cat']
                tty: true
                volumeMounts:
                - name: dockersock
                  mountPath: /var/run/docker.sock
              - name: helm
                image: dtzar/helm-kubectl:3.13.2
                command: ['cat']
                tty: true
              volumes:
              - name: dockersock
                hostPath:
                  path: /var/run/docker.sock
            '''
        }
    }

    options {
        disableConcurrentBuilds()
    }

    environment {
        IMAGE_REPO_BACKEND = '213daniel/flask-app-backend'
        IMAGE_REPO_FRONTEND = '213daniel/flask-app-frontend'
        TAG = "${env.BUILD_NUMBER}"
        DOCKER_CREDENTIALS_ID = 'dockerhub-creds'
        NAMESPACE = "default"
        RELEASE_NAME = "flask-app"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                container('python') {
                    sh '''
                        pip install -r backend/requirements.txt
                        pip install pytest pytest-flask
                        export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
                        pytest backend/test_app.py
                    '''
                }
            }
        }

        stage('Build & Push') {
            steps {
                container('docker') {
                    withCredentials([usernamePassword(
                        credentialsId: DOCKER_CREDENTIALS_ID,
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh """
                            # --- Backend ---
                            docker build -t ${IMAGE_REPO_BACKEND}:${TAG} ./backend
                            echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                            docker push ${IMAGE_REPO_BACKEND}:${TAG}

                            # --- Frontend ---
                            docker build -t ${IMAGE_REPO_FRONTEND}:${TAG} ./frontend
                            docker push ${IMAGE_REPO_FRONTEND}:${TAG}
                        """
                    }
                }
            }
        }

        stage('Deploy to K8s') {
            steps {
                container('helm') {
                    script {
                        sh "kubectl get nodes"
                        sh "kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -"
                        sh """
                            helm upgrade --install ${RELEASE_NAME} ./helm/my-daniel-chart \
                            --namespace ${NAMESPACE} \
                            --set backend.image.repository=${IMAGE_REPO_BACKEND} \
                            --set backend.image.tag=${TAG} \
                            --set frontend.image.repository=${IMAGE_REPO_FRONTEND} \
                            --set frontend.image.tag=${TAG} \
                            --set config.DB_HOST=mysql.default.svc.cluster.local \
                            --wait \
                            --timeout 300s
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo "🚀 Deployment Succeeded - Build ${TAG}"
        }
        failure {
            echo "❌ Deployment Failed - Rolling back..."
            container('helm') {
                sh "helm rollback ${RELEASE_NAME} || true"
            }
        }
        always {
            echo "Cleaning Docker images..."
            container('docker') {
                sh "docker rmi ${IMAGE_REPO_BACKEND}:${TAG} ${IMAGE_REPO_FRONTEND}:${TAG} || true"
            }
        }
    }
}