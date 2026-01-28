pipeline {
    agent any

    environment {
        // וודא שב-Jenkins מוגדר Credentials מסוג Username/Password עם ה-ID הזה
        DOCKERHUB_CREDENTIALS = 'dockerhub' 
        IMAGE_NAME = '213daniel/flask-app' // שם המשתמש שלך ב-DockerHub
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                // שים לב: שיניתי ל-GitLab ול-Credentials הנכונים
                git branch: 'main', 
                    credentialsId: 'git', 
                    url: 'git@gitlab.com:sela-1119/students/danivaknin011/helm-charts/flask-jenkins-helm-1.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // בניית האימג'
                    docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry('', DOCKERHUB_CREDENTIALS) {
                        docker.image("${IMAGE_NAME}:${IMAGE_TAG}").push()
                        docker.image("${IMAGE_NAME}:${IMAGE_TAG}").push('latest')
                    }
                }
            }
        }

        stage('Deploy with Helm') {
            steps {
                // וודא שהנתיב ל-helm-chart נכון ביחס לשורש הפרויקט
                sh """
                    helm upgrade --install flask-app ./helm-chart \
                        --set image.repository=${IMAGE_NAME} \
                        --set image.tag=${IMAGE_TAG}
                """
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully 💚'
        }
        failure {
            echo 'Pipeline failed ❌'
        }
    }
}