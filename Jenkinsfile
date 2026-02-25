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
        // נדרש Credentials חדש בג'נקינס מסוג Secret Text בשם 'github-token'
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
                    echo "Running Helm Lint..."
                    sh "helm lint ./helm/my-daniel-chart"
                    
                    echo "Running Helm Template (Dry Run)..."
                    // מוודא שה-Template מתרנדר נכון ללא שגיאות
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

        stage('GitOps: Update Values & Create PR') {
            // רץ רק אם אנחנו על Feature Branch (ולא ב-Main)
            when {
                not { branch 'main' }
            }
            steps {
                container('helm') { // משתמשים בקונטיינר הזה כי יש בו git ו-curl
                    withCredentials([string(credentialsId: GITHUB_CREDENTIALS_ID, variable: 'GITHUB_TOKEN')]) {
                        sh """
                            # הגדרת משתמש Git לביצוע ה-Commit
                            git config --global user.email "jenkins-bot@example.com"
                            git config --global user.name "Jenkins CI Bot"

                            # יצירת Branch חדש עבור העדכון
                            NEW_BRANCH="update-tags-build-${TAG}"
                            git checkout -b \$NEW_BRANCH

                            # עדכון קובץ ה-values.yaml באמצעות sed (חיפוש והחלפת ה-tag)
                            sed -i -e '/backend:/,/tag:/ s/tag: .*/tag: "'${TAG}'"/' ./helm/my-daniel-chart/values.yaml
                            sed -i -e '/frontend:/,/tag:/ s/tag: .*/tag: "'${TAG}'"/' ./helm/my-daniel-chart/values.yaml

                            # הוספה ודחיפה של הקוד
                            git add ./helm/my-daniel-chart/values.yaml
                            git commit -m "chore: update image tags to ${TAG} [skip ci]"
                            
                            # Push עם הטוקן (מונע בעיות הרשאה)
                            git push https://\${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git \$NEW_BRANCH

                            # יצירת Pull Request דרך GitHub API
                            curl -L -X POST -H "Accept: application/vnd.github+json" \\
                            -H "Authorization: Bearer \${GITHUB_TOKEN}" \\
                            -H "X-GitHub-Api-Version: 2022-11-28" \\
                            https://api.github.com/repos/${GITHUB_REPO}/pulls \\
                            -d '{"title":"Deploy: Update image tags to build ${TAG}","body":"Automated PR from Jenkins Pipeline.","head":"'"\$NEW_BRANCH"'","base":"main"}'
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline Completed Successfully!"
            // כאן תוכל להוסיף התראה ל-Slack / Email
            // slackSend color: 'good', message: "Build ${TAG} succeeded and PR created! :rocket:"
        }
        failure {
            echo "❌ Pipeline Failed!"
            // slackSend color: 'danger', message: "Build ${TAG} failed! :x:"
        }
        always {
            echo "🧹 Cleaning Docker images..."
            // עטיפה ב-node פותרת את שגיאת ה- "Missing Context hudson.model.Node"
            node('jenkins-agent') {
                container('docker') {
                    sh "docker rmi ${IMAGE_REPO_BACKEND}:${TAG} ${IMAGE_REPO_FRONTEND}:${TAG} || true"
                }
            }
        }
    }
}