pipeline {
    agent {
        kubernetes {
            // הגדרת ה-Pod שירוץ כ-Agent
            // אנחנו משתמשים ב-3 קונטיינרים: python, docker, helm
            yaml '''
            apiVersion: v1
            kind: Pod
            metadata:
              labels:
                app: jenkins-agent
            spec:
              # וודא שזה ה-ServiceAccount שיש לו הרשאות Helm ב-Cluster שלך
              serviceAccountName: jenkins-deployer
              containers:
              - name: python
                image: python:3.9-slim
                command:
                - cat
                tty: true
              - name: docker
                image: docker:cli
                command:
                - cat
                tty: true
                volumeMounts:
                - name: dockersock
                  mountPath: /var/run/docker.sock
              - name: helm
                image: dtzar/helm-kubectl:3.13.2
                command:
                - cat
                tty: true
              volumes:
              - name: dockersock
                hostPath:
                  path: /var/run/docker.sock
            '''
        }
    }

    environment {
        // מיפוי משתנים בדומה ל-Azure DevOps
        IMAGE_REPO = '213daniel/flask-app'
        // שימוש ב-BUILD_NUMBER של ג'נקינס כתחליף ל-BuildId
        TAG = "${env.BUILD_NUMBER}" 
        DOCKER_CREDENTIALS_ID = 'dockerhub-creds'
    }

    stages {
        // שלב 1: טסטים (רץ בתוך קונטיינר Python)
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

        // שלב 2: בנייה וסריקה (רץ בתוך קונטיינר Docker)
 stage('Build & Check') {
    steps {
        container('docker') {
            script {
                // בנייה: נכנסים ל-app ובונים מהנקודה הנוכחית
                sh "cd app && docker build -t ${IMAGE_REPO}:${TAG} -t ${IMAGE_REPO}:latest ."
                
                echo "Running Trivy Scan..."
                sh """
                    docker run --rm \
                    -v /var/run/docker.sock:/var/run/docker.sock \
                    aquasec/trivy:latest image \
                    --severity HIGH,CRITICAL \
                    --exit-code 0 \
                    ${IMAGE_REPO}:${TAG}
                """

                // התחברות ודחיפה - שים לב ל-Backslash לפני ה-DOCKER_PASS
                withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS_ID, usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh """
                        echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                        docker push ${IMAGE_REPO}:${TAG}
                        docker push ${IMAGE_REPO}:latest
                    """
                }
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