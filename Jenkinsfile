// Jenkinsfile - declarative pipeline
// This defines exactly what Jenkins does every time you push code to GitHub.

pipeline {
    agent any   // run on the built-in Jenkins node (fine for this simple project)

    environment {
        // Name for the Docker image Jenkins will build
        IMAGE_NAME = "two-tier-flask-app"
    }

    stages {

        stage('Clone Repository') {
            steps {
                // "checkout scm" automatically pulls whatever repo/branch
                // this pipeline job is configured to watch (set up in Part 8).
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $IMAGE_NAME .'
            }
        }

        stage('Run Docker Compose') {
            steps {
                // Bring down any old containers from a previous run first,
                // then rebuild and start fresh containers in the background (-d).
                sh 'docker-compose down || true'
                sh 'docker-compose up -d --build'
            }
        }

        stage('Integration Tests') {
            steps {
                // Give the app a few seconds to fully start before testing it
                sh 'sleep 10'

                // Curl the health check endpoint.
                // -f makes curl FAIL (non-zero exit code) if the HTTP status
                // isn't 2xx, which automatically fails this Jenkins stage.
                sh 'curl -f http://localhost:5000/health'
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline succeeded! App is deployed and healthy.'
        }
        failure {
            echo '❌ Pipeline failed. Check the console output above for details.'
        }
    }
}
