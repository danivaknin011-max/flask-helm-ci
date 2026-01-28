podTemplate(yaml: '''
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
''') {

    node(POD_LABEL) { // ג'נקינס יזהה אוטומטית את הלייבל של הפוד שנוצר
        pipeline {
            agent none // ביטול ה-agent הדיפולטיבי כי הגדרנו podTemplate למעלה

            environment {
                DOCKERHUB_CREDENTIALS = 'dockerhub'
                IMAGE_NAME = 'danivaknin011/flask-app' 
                IMAGE_TAG = "${env.BUILD_NUMBER}"
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
                            sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                        }
                    }
                }

                stage('Push to DockerHub') {
                    steps {
                        container('docker') {
                            withCredentials([usernamePassword(credentialsId: DOCKERHUB_CREDENTIALS, passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                                sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
                                sh "docker push ${IMAGE_NAME}:${IMAGE_TAG}"
                            }
                        }
                    }
                }

                stage('Deploy with Helm') {
                    steps {
                        container('helm') {
                            sh """
                            helm upgrade --install flask-app ./helm-chart \
                                --set image.repository=${IMAGE_NAME} \
                                --set image.tag=${IMAGE_TAG} \
                                --wait
                            """
                        }
                    }
                }
            }
        }
    }
}