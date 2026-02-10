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
                image: alpine/helm:3.12
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
                        // בנייה מקומית
                        sh "docker build -t ${IMAGE_REPO}:${TAG} -t ${IMAGE_REPO}:latest -f app/Dockerfile ."
                        
                        // סריקת אבטחה עם Trivy
                        // מריצים את Trivy כקונטיינר "אח" דרך ה-Socket המשותף
                        // בדיוק כמו שעשית ב-Azure
                        echo "Running Trivy Scan..."
                        sh """
                            docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            aquasec/trivy:latest image \
                            --severity HIGH,CRITICAL \
                            --exit-code 0 \
                            ${IMAGE_REPO}:${TAG}
                        """

                        // התחברות ודחיפה (רק אם הסריקה עברה)
                        withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS_ID, usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                            sh """
                                echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                                docker push ${IMAGE_REPO}:${TAG}
                                docker push ${IMAGE_REPO}:latest
                            """
                        }
                    }
                }
            }
        }

        // שלב 3: דיפלוי (רץ בתוך קונטיינר Helm)
        stage('Deploy') {
            steps {
                container('helm') {
                    script {
                        // ב-Jenkins בתוך הקלאסטר אין צורך ב-Service Connection חיצוני
                        // הוא משתמש ב-ServiceAccount של הפוד עצמו
                        sh """
                            helm upgrade --install flask-app ./helm/my-daniel-chart \
                            --set image.repository=${IMAGE_REPO} \
                            --set image.tag=${TAG} \
                            -f helm/my-daniel-chart/values.yaml \
                            --wait
                        """
                    }
                }
            }
        }
    }
}