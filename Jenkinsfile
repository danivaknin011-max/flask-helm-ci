pipeline {
    // שינוי קריטי: שימוש ב-agent שהגדרנו ב-Helm במקום ב-master
    
    agent { label 'jenkins-agent' }

    environment {
        // וודא שזה השם המדויק שלך בדוקר-האב
        IMAGE_NAME = "213daniel/flask-app"
        IMAGE_TAG  = "latest"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                // ה-Agent הזה כבר מכיל דוקר ומחובר לסוקט
                sh 'docker build -t $IMAGE_NAME:$IMAGE_TAG .'
            }
        }

        stage('Login to DockerHub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub', // זה ה-ID שנצור תיכף בממשק
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                sh 'docker push $IMAGE_NAME:$IMAGE_TAG'
            }
        }
    }
}