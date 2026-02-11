pipeline {
    agent {
        kubernetes {
            // הגדרת ה-Pod שיריץ את הג'וב
            yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: jenkins-agent
spec:
  serviceAccountName: jenkins-deployer # ה-ServiceAccount שיצרנו קודם
  containers:
  - name: docker
    image: docker:dind
    command:
    - cat
    tty: true
    volumeMounts:
      - mountPath: /var/run/docker.sock
        name: docker-sock
  
  # הוספנו את הקונטיינר הזה - הוא מכיל את HELM
  - name: helm
    image: alpine/helm:3.12.0
    command:
    - cat
    tty: true

  volumes:
    - name: docker-sock
      hostPath:
        path: /var/run/docker.sock
"""
        }
    }

    environment {
        // משתנים גלובליים
        imageRepository = '213daniel/flask-app'
        tag = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Build and Push') {
            steps {
                container('docker') { // שימוש בקונטיינר דוקר
                    script {
                        // כאן הלוגיקה של בניית הדוקר ודחיפה (מה שעשית קודם)
                        sh "docker build -t ${imageRepository}:${tag} ./app"
                        // sh "docker push..." (הנחתי שיש לך פה לוגין מסודר)
                    }
                }
            }
        }

        stage('Deploy to K8s') {
            steps {
                // *** זה התיקון הקריטי ***
                // אנחנו אומרים לג'נקינס: תריץ את הפקודות הבאות בתוך הקונטיינר שנקרא helm
                container('helm') {
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
        }
    }
}
