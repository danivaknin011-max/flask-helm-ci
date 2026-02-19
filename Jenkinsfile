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

    environment {
        IMAGE_REPO = '213daniel/flask-app'
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
                        pip install -r app/requirements.txt
                        pip install pytest pytest-flask
                        export PYTHONPATH=$PYTHONPATH:$(pwd)/app
                        pytest app/test_app.py
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
                    cd app
                    docker build -t ${IMAGE_REPO}:${TAG} -t ${IMAGE_REPO}:latest .
                    echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                    docker push ${IMAGE_REPO}:${TAG}
                    docker push ${IMAGE_REPO}:latest
                """
            }
        }
    }
}

        // שלב 3: דיפלוי (רץ בתוך קונטיינר Helm)
       stage('Deploy to K8s') {
    steps {
        script {
            sh """
              helm upgrade --install flask-app ./helm/my-daniel-chart \
              --namespace default \
              --set image.repository=${imageRepository} \
              --set image.tag=${tag} \
              --wait
            """
        }
    }
}