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
        GITHUB_CREDENTIALS_ID = 'github-token'
        GITHUB_REPO = 'danivaknin011-max/flask-helm-ci'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test (Python)') {
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

        stage('Helm Validation (Lint & Template)') {
            steps {
                container('helm') {
                    sh "helm lint ./helm/my-daniel-chart"
                    sh "helm template test-release ./helm/my-daniel-chart --set backend.image.tag=${TAG} --set frontend.image.tag=${TAG}"
                }
            }
        }

        stage('Build & Push Docker Images') {
            steps {
                container('docker') {
                    withCredentials([usernamePassword(
                        credentialsId: DOCKER_CREDENTIALS_ID,
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh """
                            echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin

                            docker build -t ${IMAGE_REPO_BACKEND}:${TAG} ./backend
                            docker push ${IMAGE_REPO_BACKEND}:${TAG}

                            docker build -t ${IMAGE_REPO_FRONTEND}:${TAG} ./frontend
                            docker push ${IMAGE_REPO_FRONTEND}:${TAG}
                        """
                    }
                }
            }
            post {
                always {
                    container('docker') {
                        sh "docker rmi ${IMAGE_REPO_BACKEND}:${TAG} ${IMAGE_REPO_FRONTEND}:${TAG} || true"
                    }
                }
            }
        }

       stage('GitOps: Update Values & Create PR') {
    when {
        not { branch 'main' }
    }
    steps {
        container('helm') {
            withCredentials([string(credentialsId: GITHUB_CREDENTIALS_ID, variable: 'GITHUB_TOKEN')]) {
                withEnv(["GH_TOKEN=${env.GITHUB_TOKEN}"]) {
                    sh '''
                        set -e
                        apk add --no-cache git yq github-cli || true

                        # ✅ חובה לפני כל git command
                        git config --global --add safe.directory '*'

                        # הגדרת משתמש Git
                        git config --global user.email "jenkins-bot@example.com"
                        git config --global user.name "Jenkins CI Bot"

                        # הגדרת remote עם הסוד דרך משתנה סביבה
                        git remote set-url origin https://x-access-token:$GITHUB_TOKEN@github.com/${GITHUB_REPO}.git

                        # בדיקה האם אנו על HEAD detached, אם כן יוצרים branch חדש
                        CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
                        if [ "$CURRENT_BRANCH" = "HEAD" ]; then
                            CURRENT_BRANCH="feature-update-${TAG}"
                            git checkout -B $CURRENT_BRANCH
                        fi

                        # עדכון גרסאות ב-values.yaml
                        yq -i '.backend.tag = "${TAG}"' ./helm/my-daniel-chart/values.yaml
                        yq -i '.frontend.tag = "${TAG}"' ./helm/my-daniel-chart/values.yaml

                        git add ./helm/my-daniel-chart/values.yaml

                        # אם יש שינויים – commit, push ויצירת PR
                        if git diff --staged --quiet; then
                            echo "No changes detected, skipping..."
                        else
                            git commit -m "chore: update image tags to ${TAG} [skip ci]"
                            git push --force --set-upstream origin $CURRENT_BRANCH

                            gh pr create \
                                --repo "${GITHUB_REPO}" \
                                --title "Deploy: Updates for ${TAG}" \
                                --body "Automated PR update from Jenkins Build ${TAG}" \
                                --base main \
                                --head $CURRENT_BRANCH || echo "PR already exists"
                        fi
                    '''
                }
            }
        }
    }
}

    } // ← סוגר stages

    post {
        success {
            echo "✅ Pipeline Completed Successfully!"
        }
        failure {
            echo "❌ Pipeline Failed!"
        }
    }
}